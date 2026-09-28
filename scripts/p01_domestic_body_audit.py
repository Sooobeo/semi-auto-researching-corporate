"""Offline P01 body diagnostics. No network; no rights or human-review grants.

Inputs are existing collector manifests and the original candidate CSV. All text,
including titles, bylines and spans, is private under a NEW output-dir/raw. Public
files contain identifiers, locations, hashes, dates, counts and provisional labels.
DOM coverage and offset round trips are mechanical checks, never completeness gold.
"""
from __future__ import annotations

import argparse
import csv
import difflib
import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from lxml import html

VERSION = "p01-domestic-body-audit/0.1"
PROFILES = {
    "ETNEWS": {"body": '//*[@id="articleBody"]',
               "title": '//*[@id="article_title_h2"]',
               "subtitle": '//*[contains(concat(" ",normalize-space(@class)," ")," editor_mid_tit ")]',
               "byline": '//*[contains(concat(" ",normalize-space(@class)," ")," reporter_info ")]',
               "dates": '//article//*[self::time]'},
    "ZDNET_KR": {"body": '//*[@id="articleBody"]',
                 "title": '//div[@class="news_head"]/h1',
                 "subtitle": '//div[@class="news_head"]/p[@class="summary"]',
                 "byline": '//div[@class="reporter_info"] | //div[@class="reporter_name"]',
                 "dates": '//div[@class="news_head"]/p[@class="meta"]'},
    "EDAILY": {"body": '//div[@itemprop="articleBody" and contains(concat(" ",normalize-space(@class)," ")," news_body ")]',
               "title": '//div[@class="article_news"]/div[1]/h1',
               "subtitle": '//div[@class="subtitles"]/span[contains(@class,"stit")]',
               "byline": '//p[@class="reporter_name"]',
               "dates": '//div[@class="dates"]//li[1]/p'},
}
SKIP_TAGS = {"script", "style", "noscript", "iframe", "form", "button", "svg"}
SKIP_CLASS = re.compile(r"(?:^|\s)(?:view_ad\w*|ad_\w+|related\w*|connect|mt_bn_box|attach|gg_textshow|taboola\S*|dable\S*)(?:\s|$)", re.I)
SKIP_ID = re.compile(r"^(?:view_ad|dablewidget|taboola|newsroom_etview_promotion)", re.I)
BLOCK_TAGS = {"p", "div", "section", "article", "h1", "h2", "h3", "li", "figure", "figcaption", "tr", "td"}
COMPANIES = {"SAM": re.compile(r"삼성전자|Samsung(?:\s+Electronics)?", re.I),
             "SKH": re.compile(r"SK\s*하이닉스|SK\s*hynix", re.I)}
RULES = {
    "quote_candidate": re.compile(r'“[^”\n]{1,2000}”|"[^"\n]{1,2000}"|‘[^’\n]{1,1000}’'),
    "number_candidate": re.compile(r"(?<![\w])[-+]?\d[\d,]*(?:\.\d+)?"),
    "number_unit_candidate": re.compile(r"\d[\d,.]*\s*(?:조\s*원|억\s*원|만\s*원|십억\s*원|조|억|만|원|달러|%|퍼센트|GB|TB|Gbps|Gb|Tb|단|층|나노|nm|개|배)(?![A-Za-z])", re.I),
    "period_candidate": re.compile(r"20\d{2}년(?:\s*[1-4]분기)?|20\d{2}Q[1-4]|[1-4]분기|상반기|하반기|전년(?:\s*동기)?|전분기|올해|내년|지난해"),
    "attribution_cue_candidate": re.compile(r"밝혔|말했|설명했|전했|발표했|관계자|대변인"),
}
DATE_RE = re.compile(r"20\d{2}[-./]\d{1,2}[-./]\d{1,2}(?:[T\s]+(?:오전\s*|오후\s*)?\d{1,2}:\d{2}(?::\d{2})?(?:[+-]\d{2}:?\d{2}|Z)?)?")


def sha(data):
    return hashlib.sha256(data if isinstance(data, bytes) else data.encode("utf-8")).hexdigest()


def read_csv(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def write_csv(path, rows):
    fields = list(dict.fromkeys(k for row in rows for k in row))
    with path.open("x", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fields or ["status"])
        writer.writeheader()
        writer.writerows(rows)


def dump_line(stream, data):
    stream.write(json.dumps(data, ensure_ascii=False) + "\n")


def excluded(node):
    if not isinstance(node.tag, str):
        return "comment_or_processing_instruction"
    if node.tag.lower() in SKIP_TAGS:
        return "non_article_tag"
    if node.get("hidden") is not None or "display:none" in node.get("style", "").replace(" ", "").lower():
        return "hidden_element"
    if SKIP_CLASS.search(node.get("class", "")) or SKIP_ID.search(node.get("id", "")):
        return "advert_or_related_widget_profile"
    # ZDNet places the related-list heading immediately before its excluded widget.
    sibling = node.getnext()
    if node.tag in ("h2", "h3") and sibling is not None and "connect" in sibling.get("class", "").split():
        return "related_widget_heading"
    return ""


def role_for(node, region):
    lineage = [node] + list(node.iterancestors())
    for ancestor in lineage:
        classes = ancestor.get("class", "").split()
        if ancestor.tag == "figcaption" or "caption" in classes:
            return "caption"
        if "editor_mid_tit" in classes:
            return "subheadline"
        if ancestor.tag in ("h2", "h3"):
            return "subheading"
        if ancestor.tag in ("td", "th"):
            return "table_cell"
        if ancestor is region:
            break
    return "body"


def located_body(region):
    """Preserve every retained DOM text node including tails; inserted newlines mapped.

    XPath text()[n] positions count all direct text nodes, including whitespace.
    Excluding a widget never excludes its following sibling text (HTML tail).
    """
    parts, atoms, omissions, separators = [], [], [], []
    offset = 0

    def newline(reason):
        nonlocal offset
        if parts and not parts[-1].endswith("\n"):
            parts.append("\n")
            separators.append({"start": offset, "end": offset + 1, "reason": reason})
            offset += 1

    def emit(text, owner, index):
        nonlocal offset
        xpath = owner.getroottree().getpath(owner) + f"/text()[{index}]"
        atoms.append({"source_xpath": xpath, "raw_text": text,
                      "body_start": offset, "body_end": offset + len(text),
                      "segment_position_candidate": role_for(owner, region)})
        parts.append(text)
        offset += len(text)

    def visit(node):
        reason = excluded(node)
        if reason:
            omissions.append({"source_xpath": node.getroottree().getpath(node),
                              "reason": reason, "chars": len("".join(node.itertext())) if isinstance(node.tag, str) else 0})
            newline("excluded_subtree_boundary")
            return
        index = 0
        if node.text is not None:
            index += 1
            emit(node.text, node, index)
        for child in node:
            if isinstance(child.tag, str) and child.tag in BLOCK_TAGS | {"br"}:
                newline("html_block_or_br_boundary")
            visit(child)
            if isinstance(child.tag, str) and child.tag in BLOCK_TAGS | {"br"}:
                newline("html_block_or_br_boundary")
            if child.tail is not None:
                index += 1
                emit(child.tail, node, index)

    visit(region)
    return "".join(parts), atoms, omissions, separators


def sentence_ranges(text):
    start = 0
    for match in re.finditer(r'[.!?。！？]["”’\')\]]*(?=\s|$)|\n+', text):
        end = match.end()
        left, right = start, end
        while left < right and text[left].isspace():
            left += 1
        while right > left and text[right - 1].isspace():
            right -= 1
        if left < right:
            yield left, right
        start = end
    left, right = start, len(text)
    while left < right and text[left].isspace():
        left += 1
    while right > left and text[right - 1].isspace():
        right -= 1
    if left < right:
        yield left, right


def source_segments(start, end, atoms):
    return [{"source_xpath": a["source_xpath"],
             "source_start": max(start, a["body_start"]) - a["body_start"],
             "source_end": min(end, a["body_end"]) - a["body_start"],
             "body_start": max(start, a["body_start"]),
             "body_end": min(end, a["body_end"])}
            for a in atoms if a["body_start"] < end and a["body_end"] > start]


def metadata(root, profile):
    private = {}
    for role in ("title", "subtitle", "byline"):
        private[role] = [{"text": "".join(n.itertext()), "xpath": n.getroottree().getpath(n)}
                         for n in root.xpath(profile[role]) if "".join(n.itertext()).strip()]
    dates = []
    for node in root.xpath('//meta[@content]'):
        key = (node.get("property") or node.get("name") or node.get("itemprop") or "").lower()
        kind = "modified" if re.search(r"modif|updated", key) else "published" if key in {
            "article:published_time", "dd:published_time", "dc.date.issued", "datepublished", "date"} else None
        if kind:
            dates.append({"kind": kind, "value": node.get("content"), "xpath": node.getroottree().getpath(node) + "/@content", "basis": "meta"})
    for node in root.xpath(profile["dates"]):
        text = "".join(node.itertext())
        # One header can contain both labels. Classify each date from its own prefix.
        for match in DATE_RE.finditer(text):
            prefix = text[max(0, match.start() - 14):match.start()]
            kind = "modified" if re.search(r"수정|업데이트|updated", prefix, re.I) else "published" if re.search(r"등록|입력|발행|게재|published", prefix, re.I) else "unknown"
            dates.append({"kind": kind, "value": match.group(), "xpath": node.getroottree().getpath(node), "basis": "visible_header", "start": match.start(), "end": match.end()})
    def visit_json(value, path, xpath):
        if isinstance(value, dict):
            for key, val in value.items():
                if key in ("datePublished", "dateModified") and isinstance(val, str):
                    dates.append({"kind": "published" if key == "datePublished" else "modified", "value": val, "xpath": xpath, "json_path": path + "." + key, "basis": "json_ld"})
                visit_json(val, path + "." + key, xpath)
        elif isinstance(value, list):
            for index, val in enumerate(value):
                visit_json(val, path + f"[{index}]", xpath)
    for node in root.xpath('//script[@type="application/ld+json"]'):
        try:
            visit_json(json.loads(node.text or ""), "$", node.getroottree().getpath(node))
        except (ValueError, TypeError):
            private.setdefault("issues", []).append("json_ld_parse_failed")
    private["dates"] = dates
    return private


def safe_date(value):
    match = DATE_RE.search(value)
    if not match:
        return None
    found = match.group()
    date_match = re.match(r"(20\d{2})[-./](\d{1,2})[-./](\d{1,2})", found)
    y, m, d = map(int, date_match.groups())
    try:
        day = datetime(y, m, d).date().isoformat()
    except ValueError:
        return None
    # Preserve explicit clock and zone only; never infer midnight or timezone.
    time_match = re.search(r"(\d{1,2}):(\d{2})(?::(\d{2}))?", found)
    result = {"date": day, "precision": "date_only", "clock": None, "timezone": None}
    if time_match:
        hour, minute, second = time_match.groups()
        hour = int(hour)
        if "오후" in found and hour < 12:
            hour += 12
        if "오전" in found and hour == 12:
            hour = 0
        result.update(precision="second" if second else "minute", clock=f"{hour:02d}:{minute}" + (f":{second}" if second else ""))
        zone = re.search(r"(?:[+-]\d{2}:?\d{2}|Z)$", found)
        result["timezone"] = zone.group() if zone else None
    return result


def date_comparison(values):
    """Compare only shared precision, retaining absent timezone as unknown.

    An explicit offset is converted only when BOTH operands contain offsets. A
    minute header and matching second-level meta are compatible display values,
    not equal verified instants. Date-only inputs never manufacture midnight.
    """
    reasons = set()
    for index, left in enumerate(values):
        for right in values[index + 1:]:
            width = 8 if left["precision"] == right["precision"] == "second" else 5
            if left["clock"] and right["clock"] and left["timezone"] and right["timezone"]:
                first = datetime.fromisoformat(left["date"] + "T" + left["clock"] + left["timezone"].replace("Z", "+00:00")).astimezone(timezone.utc)
                second = datetime.fromisoformat(right["date"] + "T" + right["clock"] + right["timezone"].replace("Z", "+00:00")).astimezone(timezone.utc)
                if first.isoformat()[:11 + width] != second.isoformat()[:11 + width]:
                    reasons.add("published_explicit_instants_differ_at_shared_precision")
            elif left["date"] != right["date"]:
                reasons.add("published_calendar_dates_differ")
            elif left["clock"] and right["clock"] and left["clock"][:width] != right["clock"][:width]:
                reasons.add("published_local_clocks_differ_timezone_may_be_unknown")
    return sorted(reasons)


def inspect(row, manifest_path, candidate, streams):
    public = {k: row.get(k, "") for k in ("candidate_id", "doc_id", "revision_id", "source_id", "event_family_id", "company_id", "scope_id", "reference_period", "fetch_status", "rights_status", "rights_reason", "execution_basis", "user_authorization_sha256")}
    public.update(manifest_path=str(manifest_path), audit_version=VERSION,
                  body_complete="pending_human_original_comparison", human_audit_status="pending",
                  label_status="provisional_rules_only", evidence_eligible=False)
    if not row.get("storage_uri"):
        public.update(audit_status="not_available", missing_reason=row.get("missing_reason") or row.get("fetch_status"))
        return public
    raw_root = (manifest_path.parent / "raw").resolve()
    path = (manifest_path.parent / row["storage_uri"]).resolve()
    if not path.is_relative_to(raw_root):
        raise ValueError("raw_path_outside_collector_run")
    raw = path.read_bytes()
    if sha(raw) != row.get("sha256") or row.get("revision_id") != row.get("sha256"):
        raise ValueError("raw_hash_or_revision_mismatch")
    if row["source_id"] not in PROFILES:
        raise ValueError("source_profile_not_supported")
    root = html.fromstring(raw)
    profile = PROFILES[row["source_id"]]
    regions = root.xpath(profile["body"])
    public.update(body_selector=profile["body"], body_selector_matches=len(regions), raw_sha256=sha(raw))
    if len(regions) != 1:
        public.update(audit_status="profile_ambiguous_or_missing", missing_reason="body_selector_not_unique")
        return public
    region = regions[0]
    text, atoms, omissions, separators = located_body(region)
    private_meta = metadata(root, profile)
    identifier = row["doc_id"] + ":" + row["revision_id"]
    errors = []
    covered_positions = bytearray(len(text))
    for index, atom in enumerate(atoms, 1):
        atom.update(block_id=f"{identifier}:A{index:05d}", doc_id=row["doc_id"], revision_id=row["revision_id"], offset_unit="unicode_codepoint", offset_basis="canonical_body_raw", normalization="identity", human_audit_status="pending")
        selected = root.xpath(atom["source_xpath"])
        atom["xpath_roundtrip"] = len(selected) == 1 and str(selected[0]) == atom["raw_text"]
        atom["body_roundtrip"] = text[atom["body_start"]:atom["body_end"]] == atom["raw_text"]
        if not atom["xpath_roundtrip"] or not atom["body_roundtrip"]:
            errors.append("atom_roundtrip_failed")
        for p in range(atom["body_start"], atom["body_end"]):
            covered_positions[p] += 1
        dump_line(streams["atoms"], atom)
    for sep in separators:
        for p in range(sep["start"], sep["end"]):
            covered_positions[p] += 1
    if any(count != 1 for count in covered_positions):
        errors.append("canonical_body_mapping_gap_or_overlap")
    span_counts, companies = Counter(), Counter()
    spans = []
    for kind, pattern in list(RULES.items()) + [("company_mention_" + company, pattern) for company, pattern in COMPANIES.items()]:
        for match in pattern.finditer(text):
            span = {"span_id": f"{identifier}:R{len(spans)+1:05d}", "doc_id": row["doc_id"], "revision_id": row["revision_id"], "kind_candidate": kind, "start": match.start(), "end": match.end(), "text": match.group(), "offset_unit": "unicode_codepoint", "offset_basis": "canonical_body_raw", "source_segments": source_segments(match.start(), match.end(), atoms), "status": "rule_candidate_pending_review"}
            span["roundtrip"] = text[span["start"]:span["end"]] == span["text"]
            if not span["roundtrip"]:
                errors.append("span_roundtrip_failed")
            spans.append(span)
            span_counts[kind] += 1
            if kind.startswith("company_mention_"):
                companies[kind.removeprefix("company_mention_")] += 1
            dump_line(streams["spans"], span)
            dump_line(streams["span_index"], {k: v for k, v in span.items() if k != "text"} | {"text_sha256": sha(span["text"])})
    sentences = list(sentence_ranges(text))
    for index, (start, end) in enumerate(sentences, 1):
        current = text[start:end]
        company_hit = any(p.search(current) for p in COMPANIES.values())
        quote = bool(RULES["quote_candidate"].search(current))
        cue = bool(RULES["attribution_cue_candidate"].search(current))
        speaker = "company_attribution_candidate" if company_hit and cue else "unknown"
        narration = "quoted_speech_candidate" if quote else "indirect_attribution_candidate" if cue else "unattributed_narration_candidate"
        sentence = {"sentence_id": f"{identifier}:S{index:05d}", "doc_id": row["doc_id"], "revision_id": row["revision_id"], "start": start, "end": end, "text": current, "offset_unit": "unicode_codepoint", "offset_basis": "canonical_body_raw", "source_segments": source_segments(start, end, atoms), "speech_candidate": narration, "speaker_candidate": speaker, "reporter_authorship": "unknown", "segmentation_status": "provisional_punctuation_newline_rule", "human_audit_status": "pending", "roundtrip": text[start:end] == current}
        if not sentence["roundtrip"]:
            errors.append("sentence_roundtrip_failed")
        dump_line(streams["sentences"], sentence)
        dump_line(streams["sentence_index"], {k: v for k, v in sentence.items() if k != "text"} | {"text_sha256": sha(current)})
    dump_line(streams["documents"], {"doc_id": row["doc_id"], "revision_id": row["revision_id"], "canonical_body_raw": text, "metadata": private_meta, "separators": separators, "omissions": omissions, "normalization": "identity", "copyright_notice": "private_local_analysis_only_source_rights_unresolved"})
    public_dates = [{"kind_candidate": item["kind"], "location": item["xpath"], "json_path": item.get("json_path"), "normalized": safe_date(item["value"]), "raw_sha256": sha(item["value"]), "basis": item["basis"]} for item in private_meta["dates"]]
    published = [v["normalized"] for v in public_dates if v["kind_candidate"] == "published" and v["normalized"]]
    candidate_date = safe_date(candidate.get("publisher_published_raw", ""))
    date_conflicts = date_comparison(published + ([candidate_date] if candidate_date else []))
    warnings = []
    if not private_meta["title"]:
        warnings.append("headline_missing")
    if not private_meta["byline"]:
        warnings.append("byline_candidate_missing")
    if not published:
        warnings.append("published_date_unknown")
    if len(text.strip()) < 400:
        warnings.append("short_body_manual_review")
    if len(private_meta["title"]) != 1:
        warnings.append("headline_selector_not_unique")
    # The presence of a copyright/byline string is a review signal, not a deletion rule.
    if re.search(r"무단\s*(?:전재|복제)|재배포\s*금지|저작권|ⓒ", text):
        warnings.append("copyright_footer_may_be_in_selected_body")
    original_chars = len("".join(region.itertext()))
    kept_chars = sum(len(a["raw_text"]) for a in atoms)
    excluded_chars = sum(o["chars"] for o in omissions)
    if original_chars != kept_chars + excluded_chars:
        warnings.append("selected_dom_text_accounting_difference")
    headline = " ".join(item["text"].strip() for item in private_meta["title"])
    search_title = candidate.get("title_raw_search", "")
    title_similarity = difflib.SequenceMatcher(None, re.sub(r"\s+", "", headline), re.sub(r"\s+", "", search_title)).ratio() if headline and search_title else None
    hangul_chars = len(re.findall(r"[\uac00-\ud7a3]", text))
    replacement_chars = text.count("\ufffd")
    if not hangul_chars or replacement_chars:
        warnings.append("encoding_requires_review")
    if title_similarity is not None and title_similarity < 0.5:
        warnings.append("search_headline_low_character_overlap")
    public.update(audit_status="local_diagnostics_pending_human", body_xpath=region.getroottree().getpath(region),
                  body_sha256=sha(text), canonical_body_chars=len(text), retained_dom_chars=kept_chars,
                  selected_dom_chars=original_chars, excluded_subtree_chars=excluded_chars,
                  excluded_subtrees=len(omissions), atom_count=len(atoms), substantive_atom_count=sum(bool(a["raw_text"].strip()) for a in atoms),
                  sentence_candidates=len(sentences), span_candidates=len(spans), span_counts=json.dumps(span_counts),
                  company_mentions=json.dumps(companies), headline_candidates=len(private_meta["title"]),
                  subtitle_candidates=len(private_meta["subtitle"]), byline_candidates=len(private_meta["byline"]),
                  parser_document_encoding=root.getroottree().docinfo.encoding,
                  body_hangul_chars=hangul_chars, replacement_char_count=replacement_chars,
                  headline_search_character_similarity=title_similarity,
                  source_date_candidates=json.dumps(public_dates), published_date_status="conflict_pending_review" if date_conflicts else "compatible_at_shared_precision_pending_review" if published else "unknown",
                  published_date_conflict_reasons="|".join(date_conflicts),
                  published_timezone_unknown_candidates=sum(v["timezone"] is None and v["clock"] is not None for v in published),
                  modified_date_candidates=sum(d["kind_candidate"] == "modified" for d in public_dates),
                  original_fetch_observed_at=row.get("observed_at", ""),
                  location_offset_integrity="pass" if not errors else "fail", integrity_errors="|".join(sorted(set(errors))),
                  diagnostics="|".join(warnings), body_precision="not_measured", body_recall="not_measured",
                  manual_original_comparison="not_performed", private_body_uri="raw/documents.jsonl",
                  missing_reason="body_completeness_claim_alignment_and_human_review_pending")
    return public


def run(manifests, candidates_path, output):
    if output.exists():
        raise ValueError("output_directory_must_be_new")
    candidates = read_csv(candidates_path)
    by_id = {r["candidate_id"]: r for r in candidates}
    if len(by_id) != len(candidates):
        raise ValueError("duplicate_candidate_ids")
    output.mkdir(parents=True)
    (output / "raw").mkdir()
    (output / "raw" / ".gitignore").write_text("*\n", encoding="utf-8")
    locations = {"atoms": "raw/atoms.jsonl", "documents": "raw/documents.jsonl", "sentences": "raw/sentences.jsonl", "spans": "raw/spans.jsonl", "span_index": "span_index.jsonl", "sentence_index": "sentence_index.jsonl"}
    streams = {key: (output / name).open("x", encoding="utf-8") for key, name in locations.items()}
    rows, seen, input_counts = [], set(), []
    try:
        for manifest in manifests:
            source = read_csv(manifest)
            input_counts.append({"path": str(manifest), "sha256": sha(manifest.read_bytes()), "rows": len(source)})
            for row in source:
                identifier = row.get("candidate_id", "")
                base = {"candidate_id": identifier, "doc_id": row.get("doc_id", ""), "source_id": row.get("source_id", ""), "manifest_path": str(manifest), "human_audit_status": "pending", "body_complete": "pending"}
                if identifier not in by_id:
                    rows.append(base | {"audit_status": "input_error", "missing_reason": "candidate_not_in_input"})
                    continue
                if identifier in seen:
                    rows.append(base | {"audit_status": "duplicate_attempt_preserved", "missing_reason": "duplicate_candidate_attempt_not_recounted"})
                    continue
                seen.add(identifier)
                try:
                    rows.append(inspect(row, manifest, by_id[identifier], streams))
                except Exception as exc:
                    # No exceptions containing source text or HTML are printed/stored.
                    rows.append(base | {"audit_status": "local_audit_error", "missing_reason": type(exc).__name__})
    finally:
        for stream in streams.values():
            stream.close()
    write_csv(output / "body_audit.csv", rows)
    processed = [r for r in rows if r.get("audit_status") == "local_diagnostics_pending_human"]
    summary = {"version": VERSION, "completed_at": datetime.now(timezone.utc).isoformat(),
               "script_sha256": sha(Path(__file__).read_bytes()), "candidate_sha256": sha(candidates_path.read_bytes()),
               "input_manifests": input_counts, "candidate_rows": len(candidates), "attempt_rows": len(rows),
               "candidate_ids_not_in_manifests": sorted(set(by_id) - seen),
               "processed_local_bodies": len(processed), "source_body_counts": dict(Counter(r["source_id"] for r in processed)),
               "statuses": dict(Counter(r["audit_status"] for r in rows)),
               "body_hash_unique_count": len({r["body_sha256"] for r in processed}),
               "location_offset_integrity_pass": sum(r["location_offset_integrity"] == "pass" for r in processed),
               "date_conflict_candidates": sum(r["published_date_status"] == "conflict_pending_review" for r in processed),
               "sentence_candidates": sum(r["sentence_candidates"] for r in processed),
               "span_candidates": sum(r["span_candidates"] for r in processed),
               "human_audit_passed": 0, "complete_bodies_verified": 0,
               "independent_original_authorship_verified": 0, "claim_matches_verified": 0,
               "rights_inference": "none_source_rights_and_user_execution_authorization_separate",
               "limitations": ["Selected DOM accounting is not semantic recall or precision.", "Rules can split abbreviations or miss cross-paragraph quotes; no linguistic gold.", "Attribution and company mentions are candidates, not speaker or authorship decisions.", "No morphology, lemmatization, ontology, new network request or rights approval."]}
    with (output / "summary.json").open("x", encoding="utf-8") as stream:
        json.dump(summary, stream, ensure_ascii=False, indent=2)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, action="append", required=True)
    parser.add_argument("--candidates", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    summary = run(args.manifest, args.candidates, args.output_dir)
    print(json.dumps({k: summary[k] for k in ("attempt_rows", "processed_local_bodies", "source_body_counts", "statuses", "location_offset_integrity_pass", "sentence_candidates", "span_candidates", "human_audit_passed")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
