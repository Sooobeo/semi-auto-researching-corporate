"""Offline second-pass extraction diagnostics; never a human completeness audit.

Only existing HTML and audit files are read. No source text is printed or stored
in public outputs. Alternative parsers/DOM regions provide mechanical mismatch
candidates, not independent factual sources or semantic completeness estimates.
"""
import argparse
import csv
import difflib
import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from lxml import html
import trafilatura

VERSION = "p01-domestic-extraction-review/0.1"
NONVISIBLE = {"script", "style", "noscript", "iframe", "svg", "form", "button"}
CONTEXT = {
    "ETNEWS": 'ancestor::article[1]',
    "ZDNET_KR": 'ancestor::div[contains(concat(" ",normalize-space(@class)," ")," zdnetkor-scroll ")][1]',
    "EDAILY": 'ancestor::div[contains(concat(" ",normalize-space(@class)," ")," article_news ")][1]',
}
WIDGET = re.compile(r"related|recommend|ranking|popular|connect|promotion|banner|taboola|dable|(?:^|[ _-])ad(?:[ _-]|$)|view_ad|ad_|sns|share|comment|copyright|reporter", re.I)


def sha(value):
    return hashlib.sha256(value if isinstance(value, bytes) else value.encode("utf-8")).hexdigest()


def compact(value):
    return re.sub(r"\s+", "", value)


def csv_rows(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def jsonl(path):
    with Path(path).open(encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def xpath(node):
    return node.getroottree().getpath(node)


def comparison(canonical, alternative):
    left, right = compact(canonical), compact(alternative)
    matcher = difflib.SequenceMatcher(None, left, right, autojunk=False)
    matched = sum(block.size for block in matcher.get_matching_blocks())
    extra = [j2-j1 for op,i1,i2,j1,j2 in matcher.get_opcodes() if op in ("insert", "replace")]
    return {"alternative_chars": len(alternative), "alternative_sha256": sha(alternative),
            "whitespace_insensitive_equal": left == right,
            "canonical_matched_char_fraction": round(matched / len(left), 6) if left else None,
            "alternative_matched_char_fraction": round(matched / len(right), 6) if right else None,
            "alternative_longest_unmatched_run": max(extra, default=0),
            "metric_status": "character_alignment_diagnostic_not_semantic_recall"}


def visible_owner(text_node):
    node = text_node.getparent()
    return node.getparent() if text_node.is_tail else node


def lineage(node):
    return [node] + list(node.iterancestors())


def visible(node):
    return not any(not isinstance(n.tag, str) or n.tag.lower() in NONVISIBLE or n.get("hidden") is not None
                   or "display:none" in n.get("style", "").replace(" ", "").lower() for n in lineage(node))


def node_role(node, metadata):
    paths = [xpath(n) for n in lineage(node)]
    for role in ("title", "subtitle", "byline"):
        if any(entry["xpath"] in paths for entry in metadata.get(role, [])):
            return role + "_metadata_preserved"
    classes = " ".join(n.get("class", "") + " " + n.get("id", "") for n in lineage(node))
    if WIDGET.search(classes):
        return "widget_or_byline_boundary_candidate"
    if re.search(r"date|meta|news_head|subtitles|title", classes, re.I):
        return "header_metadata_candidate"
    if any(n.tag == "a" for n in lineage(node)):
        return "outside_link_candidate"
    return "outside_substantive_text_review"


def json_body_candidates(root):
    found, parse_errors, permissive = [], 0, 0
    def walk(value, location, path):
        if isinstance(value, dict):
            for key, item in value.items():
                if key == "articleBody" and isinstance(item, str):
                    found.append((location, path + ".articleBody", item))
                walk(item, location, path + "." + key)
        elif isinstance(value, list):
            for index, item in enumerate(value):
                walk(item, location, path + f"[{index}]")
    for node in root.xpath('//script[@type="application/ld+json"]'):
        try:
            value = json.loads(node.text or "")
        except ValueError:
            try:
                value = json.loads(node.text or "", strict=False)
                permissive += 1
            except ValueError:
                parse_errors += 1
                continue
        walk(value, xpath(node), "$")
    return found, parse_errors, permissive


def review(audit_dir, output):
    output.mkdir(parents=True, exist_ok=False)
    docs = {row["doc_id"]: row for row in jsonl(audit_dir / "raw/documents.jsonl")}
    atoms = defaultdict(list)
    for atom in jsonl(audit_dir / "raw/atoms.jsonl"):
        atoms[atom["doc_id"]].append(atom)
    audits = {row["doc_id"]: row for row in csv_rows(audit_dir / "body_audit.csv")}
    manifest_cache, records, findings, alternatives = {}, [], [], []
    for doc_id, doc in docs.items():
        audit = audits[doc_id]
        manifest_path = Path(audit["manifest_path"])
        if manifest_path not in manifest_cache:
            manifest_cache[manifest_path] = {row["doc_id"]: row for row in csv_rows(manifest_path)}
        manifest = manifest_cache[manifest_path][doc_id]
        raw_path = (manifest_path.parent / manifest["storage_uri"]).resolve()
        if not raw_path.is_relative_to((manifest_path.parent / "raw").resolve()):
            raise ValueError("raw_path_outside_existing_run")
        raw, canonical = raw_path.read_bytes(), doc["canonical_body_raw"]
        if sha(raw) != doc["revision_id"] or sha(canonical) != audit["body_sha256"]:
            raise ValueError("source_hash_mismatch")
        root = html.fromstring(raw)
        selected = root.xpath(audit["body_xpath"])
        if len(selected) != 1:
            raise ValueError("body_xpath_not_unique")
        body = selected[0]
        context_nodes = body.xpath(CONTEXT[audit["source_id"]])
        context = context_nodes[0] if context_nodes else body.getparent()
        local_findings, mismatch_count = [], 0
        retained = set(a["source_xpath"] for a in atoms[doc_id])
        metadata = doc["metadata"]
        for atom in atoms[doc_id]:
            nodes = root.xpath(atom["source_xpath"])
            if len(nodes) != 1 or str(nodes[0]) != atom["raw_text"]:
                mismatch_count += 1
            elif len(atom["raw_text"].strip()) >= 15:
                owner = visible_owner(nodes[0])
                signatures = " ".join(n.get("class", "") + " " + n.get("id", "") for n in lineage(owner) if n is body or body in n.iterancestors())
                if WIDGET.search(signatures):
                    local_findings.append({"kind": "retained_widget_or_byline_signal", "location": atom["source_xpath"],
                                           "chars": len(atom["raw_text"]), "sha256": sha(atom["raw_text"]),
                                           "action": "inspect_local_boundary_before_treating_as_reporter_text"})
        outside_counts = Counter()
        for value in context.xpath('.//text()'):
            owner = visible_owner(value)
            if owner is None or body is owner or body in owner.iterancestors() or not visible(owner) or len(str(value).strip()) < 30:
                continue
            role = node_role(owner, metadata)
            outside_counts[role] += 1
            local_findings.append({"kind": role, "location": xpath(owner), "chars": len(str(value)),
                                   "sha256": sha(str(value)), "action": "review_as_missing_body_candidate" if role == "outside_substantive_text_review" else "keep_separate_from_body_or_widget"})
        substantive_omissions = 0
        for omitted in doc["omissions"]:
            nodes = root.xpath(omitted["source_xpath"])
            if not nodes or not isinstance(nodes[0].tag, str) or nodes[0].tag in NONVISIBLE:
                continue
            node = nodes[0]
            if len("".join(node.itertext()).strip()) >= 80 and node.xpath('.//p | .//blockquote | .//table | .//figcaption'):
                substantive_omissions += 1
                local_findings.append({"kind": "omitted_region_contains_substantive_structure", "location": omitted["source_xpath"],
                                       "chars": omitted["chars"], "sha256": sha("".join(node.itertext())),
                                       "action": "inspect_excluded_related_or_attachment_region_locally"})
        js_bodies, js_errors, js_permissive = json_body_candidates(root)
        for location, jpath, text in js_bodies:
            alternatives.append({"doc_id": doc_id, "method": "jsonld_articleBody", "location": location,
                                 "json_path": jpath, **comparison(canonical, text)})
        alternate = trafilatura.extract(raw, include_comments=False, include_tables=True, favor_recall=False) or ""
        parser_check = comparison(canonical, alternate)
        alternatives.append({"doc_id": doc_id, "method": "trafilatura_independent_fallback", "location": "stored_html", **parser_check})
        explicit_regions = root.xpath('//*[@itemprop="articleBody"] | //*[@id="articleBody"]')
        inner = body.xpath('./div[starts-with(@id,"content-")]')
        alternative_regions = inner + [node for node in explicit_regions if node is not body and body not in node.iterancestors()]
        region_exact = 0
        for region in alternative_regions:
            text = "".join(str(v) for v in region.xpath('.//text()') if visible(visible_owner(v)))
            measured = comparison(canonical, text)
            region_exact += int(measured["whitespace_insensitive_equal"])
            alternatives.append({"doc_id": doc_id, "method": "alternate_semantic_or_content_id_dom", "location": xpath(region), **measured})
        quote_open = sum(canonical.count(char) for char in ('“', '‘'))
        quote_close = sum(canonical.count(char) for char in ('”', '’'))
        tables = body.xpath('.//table')
        captions = body.xpath('.//figcaption | .//*[contains(concat(" ",normalize-space(@class)," ")," caption ")]')
        paras = ["".join(node.itertext()) for node in body.xpath('.//p') if visible(node) and "".join(node.itertext()).strip()]
        p_retained = sum(compact(text) in compact(canonical) for text in paras)
        short = len(canonical.strip()) < 400
        short_support = short and region_exact > 0 and outside_counts["outside_substantive_text_review"] == 0 and p_retained == len(paras)
        record = {"doc_id": doc_id, "source_id": audit["source_id"], "revision_id": doc["revision_id"],
                  "raw_html_uri": str(raw_path), "body_audit_dir": str(audit_dir), "body_xpath": audit["body_xpath"],
                  "canonical_body_chars": len(canonical), "body_sha256": sha(canonical),
                  "retained_atom_xpath_checks": len(atoms[doc_id]), "retained_atom_xpath_mismatches": mismatch_count,
                  "headline_metadata_count": len(metadata.get("title", [])), "subtitle_metadata_count": len(metadata.get("subtitle", [])),
                  "byline_metadata_count": len(metadata.get("byline", [])), "date_metadata_count": len(metadata.get("dates", [])),
                  "paragraph_elements": len(paras), "paragraphs_whitespace_contained_in_canonical": p_retained,
                  "lead_status": "first_substantive_paragraph_candidate_not_human_verified",
                  "table_elements": len(tables), "tables_with_header_cells": sum(bool(t.xpath('.//th')) for t in tables),
                  "table_semantics": "not_assessed_layout_or_data", "caption_elements": len(captions),
                  "caption_elements_whitespace_contained": sum(compact("".join(c.itertext())) in compact(canonical) for c in captions),
                  "blockquote_elements": len(body.xpath('.//blockquote')), "curly_quote_open": quote_open, "curly_quote_close": quote_close,
                  "quote_boundary_status": "balanced_character_count_only" if quote_open == quote_close else "unbalanced_review_candidate",
                  "outside_unclassified_substantive_text_nodes": outside_counts["outside_substantive_text_review"],
                  "outside_metadata_or_widget_nodes": sum(outside_counts.values())-outside_counts["outside_substantive_text_review"],
                  "omitted_substantive_structure_candidates": substantive_omissions,
                  "retained_widget_or_byline_signals": sum(f["kind"] == "retained_widget_or_byline_signal" for f in local_findings),
                  "jsonld_articleBody_candidates": len(js_bodies), "jsonld_parse_errors": js_errors,
                  "jsonld_permissive_parses": js_permissive, "alternate_dom_regions": len(alternative_regions),
                  "alternate_dom_whitespace_exact_matches": region_exact,
                  "trafilatura_canonical_matched_char_fraction": parser_check["canonical_matched_char_fraction"],
                  "trafilatura_longest_unmatched_run": parser_check["alternative_longest_unmatched_run"],
                  "short_body": short, "short_body_assessment": "stored_dom_supports_short_article_pending_human" if short_support else "short_body_more_review_needed" if short else "not_short",
                  "mechanical_xpath_diagnostic": "pass" if mismatch_count == 0 else "fail",
                  "semantic_completeness": "pending_human_original_comparison", "human_audit_performed": False,
                  "precision_recall": "not_measured", "source_rights": "unchanged_unresolved",
                  "review_action": "inspect_boundary_candidates_and_metadata_in_local_original" if local_findings or short else "perform_human_original_comparison"}
        records.append(record)
        findings.extend(dict(f, doc_id=doc_id, revision_id=doc["revision_id"] ) for f in local_findings)
    with (output / "extraction_review.csv").open("x", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(records[0]) if records else ["status"])
        writer.writeheader()
        writer.writerows(records)
    for filename, rows in (("boundary_findings.jsonl", findings), ("alternative_comparisons.jsonl", alternatives)):
        with (output / filename).open("x", encoding="utf-8") as stream:
            for row in rows:
                stream.write(json.dumps(row, ensure_ascii=False) + "\n")
    summary = {"version": VERSION, "completed_at": datetime.now(timezone.utc).isoformat(), "script_sha256": sha(Path(__file__).read_bytes()),
               "body_audit_summary_sha256": sha((audit_dir / "summary.json").read_bytes()),
               "documents_reviewed": len(records), "source_counts": dict(Counter(r["source_id"] for r in records)),
               "xpath_diagnostic_pass": sum(r["mechanical_xpath_diagnostic"] == "pass" for r in records),
               "xpath_atoms_checked": sum(r["retained_atom_xpath_checks"] for r in records),
               "jsonld_articleBody_documents": sum(r["jsonld_articleBody_candidates"] > 0 for r in records),
               "jsonld_parse_error_documents": sum(r["jsonld_parse_errors"] > 0 for r in records),
               "independent_parser_comparisons": len(records), "alternative_dom_comparisons": sum(r["alternate_dom_regions"] for r in records),
               "boundary_findings": dict(Counter(f["kind"] for f in findings)),
               "short_body_documents": [{"doc_id": r["doc_id"], "chars": r["canonical_body_chars"], "assessment": r["short_body_assessment"],
                                         "alternate_dom_exact": r["alternate_dom_whitespace_exact_matches"],
                                         "outside_unclassified_nodes": r["outside_unclassified_substantive_text_nodes"]} for r in records if r["short_body"]],
               "human_audit_performed": False, "complete_bodies_verified": 0, "network_requests": 0, "llm_calls": 0,
               "source_text_in_public_output": False,
               "limitations": ["Stored static HTML only; dynamic text, paywalls, images and rendered tables may require local human inspection.",
                               "Character matching between extraction methods is not semantic recall or precision.",
                               "Boundary signals include legitimate metadata and related links; they are review candidates, not proven contamination.",
                               "No existing extractor or source file was changed; no human two-reviewer audit was performed."]}
    with (output / "summary.json").open("x", encoding="utf-8") as stream:
        json.dump(summary, stream, ensure_ascii=False, indent=2)
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--body-audit-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    result = review(args.body_audit_dir, args.output_dir)
    print(json.dumps({k: result[k] for k in ("documents_reviewed", "xpath_diagnostic_pass", "jsonld_articleBody_documents", "boundary_findings", "short_body_documents", "human_audit_performed")}))
