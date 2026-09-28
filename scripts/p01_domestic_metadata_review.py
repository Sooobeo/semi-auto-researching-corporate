"""Offline URL identity and explicit-time metadata overlay; never rewrites IDs.

Source headers, titles and authors remain in ignored raw/. Canonical declarations
are publisher metadata candidates, not proof of article independence or identity.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, time, timezone
from pathlib import Path
from urllib.parse import parse_qs, urljoin, urlsplit

from lxml import html
from p01_domestic_body_audit import PROFILES, metadata, safe_date, date_comparison

VERSION = "p01-domestic-metadata-review/0.1"


def sha(value):
    return hashlib.sha256(value if isinstance(value, bytes) else value.encode("utf-8")).hexdigest()


def jsonl(path):
    return [json.loads(x) for x in Path(path).read_text(encoding="utf-8").splitlines() if x.strip()]


def dump(path, rows):
    with path.open("x", encoding="utf-8", newline="\n") as out:
        for row in rows:
            out.write(json.dumps(row, ensure_ascii=False) + "\n")


def article_id(url, source_id):
    parsed = urlsplit(url); query = {k.lower(): v for k, v in parse_qs(parsed.query).items()}
    if source_id == "ZDNET_KR":
        values, basis = query.get("no", []), "query:no"
    elif source_id == "EDAILY":
        values, basis = query.get("newsid", []), "query:newsId"
    elif source_id == "ETNEWS":
        values, basis = [parsed.path.rstrip("/").split("/")[-1]], "path:last_component"
    else:
        return None
    return {"value": values[0], "basis": basis} if len(values) == 1 and re.fullmatch(r"\d+", values[0]) else None


def normalized_time(raw):
    normalized = safe_date(raw)
    if not normalized:
        return {"normalization_status": "unparsed", "date": None, "clock": None, "precision": "unknown", "timezone": None, "utc_derived": None}
    result = normalized | {"normalization_status": "parsed", "utc_derived": None}
    if normalized["clock"]:
        try:
            time.fromisoformat(normalized["clock"])
            if normalized["timezone"]:
                instant = datetime.fromisoformat(normalized["date"] + "T" + normalized["clock"] + normalized["timezone"].replace("Z", "+00:00"))
                result["utc_derived"] = instant.astimezone(timezone.utc).isoformat(timespec="seconds" if normalized["precision"] == "second" else "minutes").replace("+00:00", "Z")
        except ValueError:
            result.update(normalization_status="invalid_clock_or_offset", utc_derived=None)
    result["timezone_basis"] = "explicit_source_offset" if normalized["timezone"] else "not_stated_not_inferred"
    return result


def url_metadata(root, final_url):
    records = []
    for node in root.xpath('//link[@href]'):
        if "canonical" in node.get("rel", "").lower().split():
            records.append({"kind": "canonical", "url": urljoin(final_url, node.get("href")), "xpath": node.getroottree().getpath(node) + "/@href"})
    for node in root.xpath('//meta[@content]'):
        key = (node.get("property") or node.get("name") or "").lower()
        if key == "og:url":
            records.append({"kind": "og_url", "url": urljoin(final_url, node.get("content")), "xpath": node.getroottree().getpath(node) + "/@content"})
    for node in root.xpath('//script[@type="application/ld+json"]'):
        try:
            value = json.loads(node.text or "")
        except (ValueError, TypeError):
            continue
        def visit(value, path):
            if isinstance(value, dict):
                types = value.get("@type", [])
                types = types if isinstance(types, list) else [types]
                if any(str(t).endswith("Article") for t in types):
                    for key in ["url", "@id", "mainEntityOfPage"]:
                        item = value.get(key)
                        item = item.get("@id", item.get("url")) if isinstance(item, dict) else item
                        if isinstance(item, str) and (item.startswith(("http://", "https://", "/"))):
                            records.append({"kind": "json_ld_article_" + key, "url": urljoin(final_url, item), "xpath": node.getroottree().getpath(node), "json_path": path + "." + key})
                for key, item in value.items(): visit(item, path + "." + key)
            elif isinstance(value, list):
                for i, item in enumerate(value): visit(item, path + f"[{i}]")
        visit(value, "$")
    return records


def run(audit_dir, manifest_paths, output):
    if output.exists(): raise ValueError("output_directory_must_be_new")
    documents = {r["doc_id"]: r for r in jsonl(audit_dir / "raw/documents.jsonl")}
    input_paths = [audit_dir / "raw/documents.jsonl", audit_dir / "body_audit.csv", *manifest_paths]
    inputs = {str(p): sha(p.read_bytes()) for p in input_paths}
    overlays, dates, private_dates, private_headers, aliases = [], [], [], [], defaultdict(set)
    raw_hash_checks = 0
    for manifest in manifest_paths:
        with manifest.open(encoding="utf-8-sig", newline="") as stream: rows = list(csv.DictReader(stream))
        for row in rows:
            if not row["storage_uri"]: continue
            raw_path = (manifest.parent / row["storage_uri"]).resolve()
            if not raw_path.is_relative_to((manifest.parent / "raw").resolve()): raise ValueError("raw_path_outside_run")
            raw = raw_path.read_bytes(); assert sha(raw) == row["sha256"] == row["revision_id"]; raw_hash_checks += 1
            inputs[str(raw_path)] = sha(raw)
            provenance_path = manifest.parent / row["provenance_uri"]
            provenance = json.loads(provenance_path.read_text(encoding="utf-8")); inputs[str(provenance_path)] = sha(provenance_path.read_bytes())
            assert sha(provenance["source_url"]) == row["source_url_sha256"]
            assert sha(provenance["final_url"]) == row["final_url_sha256"]
            root = html.fromstring(raw, parser=html.HTMLParser(encoding="utf-8"))
            extracted = metadata(root, PROFILES[row["source_id"]]); prior = documents[row["doc_id"]]["metadata"]
            identity = {k: row[k] for k in ["doc_id", "revision_id", "source_id", "candidate_id"]}
            refs = url_metadata(root, provenance["final_url"])
            source_id = article_id(provenance["source_url"], row["source_id"])
            final_id = article_id(provenance["final_url"], row["source_id"])
            for ref in refs:
                ref["article_id_candidate"] = article_id(ref["url"], row["source_id"])
                ref["exact_source_url_equal"] = ref["url"] == provenance["source_url"]
                ref["exact_final_url_equal"] = ref["url"] == provenance["final_url"]
                ref["same_host_as_final"] = urlsplit(ref["url"]).hostname == urlsplit(provenance["final_url"]).hostname
                ref["article_id_equal_source"] = bool(source_id and ref["article_id_candidate"] and source_id["value"] == ref["article_id_candidate"]["value"])
                if ref["kind"] == "canonical": aliases[ref["url"]].add(row["doc_id"])
            local_dates = []
            for i, item in enumerate(extracted["dates"], 1):
                normalized = normalized_time(item["value"])
                record = identity | {"date_candidate_id": row["doc_id"] + f":D{i:03d}", "kind_candidate": item["kind"],
                                     "xpath": item["xpath"], "json_path": item.get("json_path"), "basis": item["basis"],
                                     "raw_sha256": sha(item["value"]), "source_substring_start": item.get("start"),
                                     "source_substring_end": item.get("end"), "normalization": normalized,
                                     "assessment": "publisher_metadata_candidate_not_verified_event_time"}
                dates.append(record); local_dates.append(record); private_dates.append(record | {"raw_value": item["value"]})
            published = [r["normalization"] for r in local_dates if r["kind_candidate"] == "published" and r["normalization"]["normalization_status"] == "parsed"]
            modified = [r["normalization"] for r in local_dates if r["kind_candidate"] == "modified" and r["normalization"]["normalization_status"] == "parsed"]
            headers = {kind: [{"xpath": item["xpath"], "text_sha256": sha(item["text"])} for item in extracted.get(kind, [])] for kind in ["title", "subtitle", "byline"]}
            overlays.append(identity | {"source_url": provenance["source_url"], "final_url": provenance["final_url"],
                                         "source_article_id_candidate": source_id, "final_article_id_candidate": final_id,
                                         "url_metadata_candidates": refs, "canonical_present": any(r["kind"] == "canonical" for r in refs),
                                         "og_url_present": any(r["kind"] == "og_url" for r in refs),
                                         "url_metadata_supporting_source_article_id": sum(r["article_id_equal_source"] for r in refs),
                                         "url_metadata_disagreeing_source_article_id": sum(bool(r["article_id_candidate"]) and not r["article_id_equal_source"] for r in refs),
                                         "dates_equal_body_audit003": extracted["dates"] == prior["dates"],
                                         "title_subtitle_byline_equal_body_audit003": all(extracted.get(k, []) == prior.get(k, []) for k in headers),
                                         "header_hashes": headers, "published_candidate_count": len(published), "modified_candidate_count": len(modified),
                                         "published_conflict_reasons": date_comparison(published), "modified_conflict_reasons": date_comparison(modified),
                                         "published_explicit_utc_candidates": sum(bool(d["utc_derived"]) for d in published),
                                         "published_timezone_unknown_candidates": sum(d["clock"] is not None and not d["timezone"] for d in published),
                                         "fetch_observed_at": row["observed_at"], "doc_id_reassignment": "not_performed",
                                         "independent_original_article": "unverified", "assessment": "provisional_identity_metadata_overlay"})
            private_headers.append(identity | {"metadata": extracted})
    duplicates = [{"canonical_url": url, "doc_ids": sorted(ids), "assessment": "exact_canonical_alias_duplicate_candidate_only"} for url, ids in sorted(aliases.items()) if len(ids) > 1]
    assert all(sha(Path(p).read_bytes()) == h for p, h in inputs.items())
    output.mkdir(parents=True); (output / "raw").mkdir(); (output / "raw/.gitignore").write_text("*\n", encoding="utf-8")
    dump(output / "article_metadata_overlay.jsonl", overlays); dump(output / "date_candidates.jsonl", dates)
    dump(output / "canonical_duplicate_candidates.jsonl", duplicates); dump(output / "raw/date_candidates.jsonl", private_dates); dump(output / "raw/header_metadata.jsonl", private_headers)
    summary = {"version": VERSION, "completed_at": datetime.now(timezone.utc).isoformat(), "script_sha256": sha(Path(__file__).read_bytes()),
               "metadata_extractor_sha256": sha(Path(__file__).with_name("p01_domestic_body_audit.py").read_bytes()), "input_sha256": inputs,
               "network_requests": 0, "model_calls": 0, "documents": len(overlays), "raw_hashes_verified": raw_hash_checks,
               "canonical_present": sum(r["canonical_present"] for r in overlays), "og_url_present": sum(r["og_url_present"] for r in overlays),
               "documents_with_url_metadata_supporting_article_id": sum(r["url_metadata_supporting_source_article_id"] > 0 for r in overlays),
               "documents_with_url_metadata_disagreeing_article_id": sum(r["url_metadata_disagreeing_source_article_id"] > 0 for r in overlays),
               "exact_canonical_alias_duplicate_groups": len(duplicates), "dates_equal_body_audit003": sum(r["dates_equal_body_audit003"] for r in overlays),
               "headers_equal_body_audit003": sum(r["title_subtitle_byline_equal_body_audit003"] for r in overlays),
               "date_candidate_roles": dict(Counter(r["kind_candidate"] for r in dates)),
               "published_utc_candidate_documents": sum(r["published_explicit_utc_candidates"] > 0 for r in overlays),
               "published_utc_candidates": sum(r["published_explicit_utc_candidates"] for r in overlays),
               "published_timezone_unknown_candidate_documents": sum(r["published_timezone_unknown_candidates"] > 0 for r in overlays),
               "published_conflict_documents": sum(bool(r["published_conflict_reasons"]) for r in overlays),
               "modified_conflict_documents": sum(bool(r["modified_conflict_reasons"]) for r in overlays),
               "limitations": ["Overlay only: original IDs and manifests unchanged; canonical/OG tags do not prove independence or uniqueness.",
                               "Publication, modification, fetch observation and event dates remain separate; timezone absent means unknown.",
                               "UTC values derive only from explicit source offsets, preserving minute/second precision.",
                               "Date/header parity reuses the audit extractor and is a reproducibility check, not independent semantic extraction accuracy."]}
    (output / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k not in {"input_sha256", "limitations"}}, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit-dir", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, action="append", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    run(args.audit_dir, args.manifest, args.output_dir)
