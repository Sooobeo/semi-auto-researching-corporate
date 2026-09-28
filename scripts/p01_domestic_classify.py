"""Offline P01 provisional classification and human-review queue; no ontology.

Signals are not substantive labels. All original text remains in the existing
private body-audit directory; outputs contain only metadata, counts and references.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

VERSION = "p01-domestic-classify/0.1"


def digest(value):
    return hashlib.sha256(value if isinstance(value, bytes) else value.encode("utf-8")).hexdigest()


def csv_rows(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def json_rows(path):
    with path.open(encoding="utf-8") as stream:
        for line in stream:
            if line.strip():
                yield json.loads(line)


def write_csv(path, rows):
    keys = list(dict.fromkeys(k for row in rows for k in row))
    with path.open("x", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, keys or ["status"])
        writer.writeheader()
        writer.writerows(rows)


def choose_review(rows, target):
    """Choose acquired bodies only; short body, family variety, source balance."""
    remaining = list(rows)
    selected, families, sources = [], set(), Counter()
    while remaining and len(selected) < target:
        selected_row = max(remaining, key=lambda r: (
            "short_body_manual_review" in r["audit"].get("diagnostics", ""),
            r["candidate"]["event_family_id"] not in families,
            -sources[r["candidate"]["source_id"]],
            -r["input_order"],
        ))
        remaining.remove(selected_row)
        selected.append(selected_row)
        families.add(selected_row["candidate"]["event_family_id"])
        sources[selected_row["candidate"]["source_id"]] += 1
    return selected


def run(candidates_path, audit_dir, output):
    if output.exists():
        raise ValueError("output_directory_must_be_new")
    candidates = csv_rows(candidates_path)
    if len({r["candidate_id"] for r in candidates}) != len(candidates):
        raise ValueError("candidate_ids_must_be_unique")
    audits = {r["candidate_id"]: r for r in csv_rows(audit_dir / "body_audit.csv")}
    documents = {(r["doc_id"], r["revision_id"]): r for r in json_rows(audit_dir / "raw/documents.jsonl")}
    sentences, spans = defaultdict(list), defaultdict(list)
    for row in json_rows(audit_dir / "raw/sentences.jsonl"):
        sentences[row["doc_id"], row["revision_id"]].append(row)
    for row in json_rows(audit_dir / "raw/spans.jsonl"):
        spans[row["doc_id"], row["revision_id"]].append(row)
    working = []
    for index, candidate in enumerate(candidates):
        audit = audits.get(candidate["candidate_id"], {})
        key = (candidate["doc_id"], audit.get("revision_id", ""))
        document = documents.get(key)
        if document:
            text = document["canonical_body_raw"]
            if digest(text) != audit["body_sha256"]:
                raise ValueError("body_hash_changed")
            for item in sentences[key] + spans[key]:
                if text[item["start"]:item["end"]] != item["text"]:
                    raise ValueError("input_span_roundtrip_failed")
        working.append({"candidate": candidate, "audit": audit, "document": document,
                        "key": key, "input_order": index})
    eligible = [row for row in working if row["document"] and row["audit"].get("audit_status") == "local_diagnostics_pending_human"]
    selected = choose_review(eligible, 20)
    review_rank = {r["candidate"]["candidate_id"]: i for i, r in enumerate(selected, 1)}
    classifications, links, signals, queue = [], [], [], []
    for row in working:
        candidate, audit, document, key = row["candidate"], row["audit"], row["document"], row["key"]
        acquired = document is not None
        identifier = candidate["candidate_id"]
        common = {"candidate_id": identifier, "doc_id": candidate["doc_id"],
                  "revision_id": audit.get("revision_id", ""), "source_id": candidate["source_id"],
                  "event_family_id": candidate["event_family_id"]}
        private_locator = str(audit_dir / "raw/documents.jsonl") + "#doc_id=" + candidate["doc_id"] + "&revision_id=" + key[1] if acquired else ""
        title = " ".join(item["text"].strip() for item in document["metadata"].get("title", [])) if acquired else candidate.get("title_raw_search", "")
        title_markers = {
            "breaking_title_marker": bool(re.search(r"[\[【(]\s*속보\s*[\]】)]", title)),
            "opinion_title_marker": bool(re.search(r"[\[【(][^\]】)]*(?:칼럼|사설|기고)[^\]】)]*[\]】)]", title)),
            "interview_title_marker": bool(re.search(r"[\[【(][^\]】)]*인터뷰[^\]】)]*[\]】)]", title)),
        }
        count = Counter(span["kind_candidate"] for span in spans[key])
        title_refs = json.dumps([item["xpath"] for item in document["metadata"].get("title", [])]) if acquired else "search_metadata_only"
        signal = common | title_markers | {
            "signal_status": "rule_candidates_not_assessments", "title_basis": "stored_publisher_headline" if acquired else "search_metadata",
            "title_sha256": digest(title), "title_location_refs": title_refs,
            "body_available": acquired,
            "body_chars": audit.get("canonical_body_chars", ""),
            "short_body_signal": "short_body_manual_review" in audit.get("diagnostics", "") if acquired else "not_available",
            "sentence_candidates": len(sentences[key]) if acquired else "",
            "quote_candidates": count["quote_candidate"] if acquired else "",
            "number_unit_candidates": count["number_unit_candidate"] if acquired else "",
            "period_candidates": count["period_candidate"] if acquired else "",
            "SAM_mention_candidates": count["company_mention_SAM"] if acquired else "",
            "SKH_mention_candidates": count["company_mention_SKH"] if acquired else "",
            "attribution_cue_candidates": count["attribution_cue_candidate"] if acquired else "",
            "body_sha256": audit.get("body_sha256", ""),
            "span_index_ref": str(audit_dir / "span_index.jsonl") + "#doc_id=" + candidate["doc_id"] if acquired else "",
            "missing_reason": "" if acquired else audit.get("missing_reason", "body_not_available"),
        }
        signals.append(signal)
        classifications.append(common | {
            "source_url": candidate["source_url"], "access_status": "local_body_acquired" if acquired else "body_not_acquired",
            "fetch_status": audit.get("fetch_status", "not_in_audit"),
            "eligibility": "unknown" if acquired else "access_unusable",
            "eligibility_reason": "body_complete_scope_and_rights_review_pending" if acquired else audit.get("missing_reason", "body_not_available"),
            "editorial_genre": "unknown", "urgency_format": "unknown", "production_origin": "unclear",
            "article_scope_assessment": "unknown", "anchor_scope_candidate": candidate.get("anchor_scope_id", ""),
            "assessment_status": "human_review_pending_rule_signals_only" if acquired else "not_assessable_without_body",
            "style_analysis_status": "pending_completeness_origin_claim_speaker_position_review" if acquired else "unavailable_without_body",
            "body_completeness": "pending_human_review" if acquired else "not_available",
            "location_offset_integrity": audit.get("location_offset_integrity", "not_available"),
            "rights_status": audit.get("rights_status") or candidate.get("rights_status", "unresolved"),
            "execution_basis": audit.get("execution_basis", ""),
            "rights_reason": audit.get("rights_reason", ""),
            "rule_signals_ref": "rule_signals.csv#candidate_id=" + identifier,
            "private_document_ref": private_locator,
            "human_review_selected": identifier in review_rank, "human_review_rank": review_rank.get(identifier, ""),
            "human_review_status": "pending" if identifier in review_rank else "not_selected_this_batch" if acquired else "not_available",
            "classification_version": VERSION,
        })
        links.append(common | {
            "primary_sampling_family_id": candidate.get("primary_sampling_family_id") or candidate["event_family_id"],
            "link_status": "provisional_discovery_link_body_match_unverified",
            "article_event_role": "uncertain", "coverage_stage": "unknown", "claim_relation": "uncertain",
            "article_company_assessment": "unknown", "anchor_company_candidate": candidate.get("company_id", ""),
            "article_scope_assessment": "unknown", "anchor_scope_candidate": candidate.get("anchor_scope_id", ""),
            "article_reference_period_assessment": "unknown", "anchor_reference_period": candidate.get("anchor_reference_period", ""),
            "link_evidence_span": "", "body_available": acquired,
            "missing_reason": "anchor_claim_and_article_span_alignment_pending" if acquired else "body_not_available",
            "assessment_status": "pending_human_claim_review", "classification_version": VERSION,
        })
    for row in selected:
        candidate, audit = row["candidate"], row["audit"]
        for reviewer in (1, 2):
            queue.append({"review_slot_id": f"P01-20260922-{review_rank[candidate['candidate_id']]:02d}-R{reviewer}",
                          "candidate_id": candidate["candidate_id"], "doc_id": candidate["doc_id"],
                          "revision_id": audit["revision_id"], "source_id": candidate["source_id"],
                          "event_family_id": candidate["event_family_id"], "selection_rank": review_rank[candidate["candidate_id"]],
                          "selection_basis": "short_body_first_then_family_diversity_then_source_balance",
                          "short_body_priority": "short_body_manual_review" in audit.get("diagnostics", ""),
                          "reviewer_slot": f"human_reviewer_{reviewer}", "reviewer_name": "unassigned",
                          "review_status": "pending", "independent_review_required": True,
                          "review_dimensions": "body_completeness|byline_dates|genre|origin|scope|event_link|claim_alignment|speaker_position",
                          "source_url": candidate["source_url"], "body_sha256": audit["body_sha256"],
                          "body_xpath": audit["body_xpath"],
                          "private_document_ref": str(audit_dir / "raw/documents.jsonl") + "#doc_id=" + candidate["doc_id"],
                          "sentence_index_ref": str(audit_dir / "sentence_index.jsonl") + "#doc_id=" + candidate["doc_id"],
                          "completed_at": "", "decision": "", "review_notes": ""})
    assert len(classifications) == len(links) == len(signals) == len(candidates)
    assert len(queue) == 2 * len(selected)
    assert all(Counter(r["doc_id"] for r in queue)[row["candidate"]["doc_id"]] == 2 for row in selected)
    output.mkdir(parents=True)
    for name, rows in (("article_classification", classifications), ("article_event_links", links), ("rule_signals", signals), ("human_review_queue", queue)):
        write_csv(output / (name + ".csv"), rows)
    summary = {"version": VERSION, "completed_at": datetime.now(timezone.utc).isoformat(),
               "candidate_rows": len(candidates), "article_classification_rows": len(classifications),
               "provisional_article_event_links": len(links), "rule_signal_rows": len(signals),
               "local_body_documents": len(eligible), "body_unavailable_documents": len(candidates) - len(eligible),
               "review_target_documents": 20, "review_selected_documents": len(selected), "review_slot_rows": len(queue),
               "review_family_count": len({r["candidate"]["event_family_id"] for r in selected}),
               "review_source_counts": dict(Counter(r["candidate"]["source_id"] for r in selected)),
               "review_short_body_documents": sum("short_body_manual_review" in r["audit"].get("diagnostics", "") for r in selected),
               "human_completed_slots": 0, "genre_assessments_confirmed": 0, "origin_assessments_confirmed": 0,
               "article_scope_assessments_confirmed": 0, "claim_alignments_confirmed": 0,
               "input_hashes": {str(path): digest(path.read_bytes()) for path in [candidates_path, audit_dir / "body_audit.csv", audit_dir / "raw/documents.jsonl", audit_dir / "raw/sentences.jsonl", audit_dir / "raw/spans.jsonl"]},
               "script_sha256": digest(Path(__file__).read_bytes()),
               "limitations": ["Title markers and body rule counts never confirm genre, origin, first report or business scope.", "One retained provisional family link per original candidate does not establish event or claim identity.", "Human slots are unassigned and pending; agent work is not two-person review.", "No original text in these outputs, no ontology and no network requests."]}
    with (output / "summary.json").open("x", encoding="utf-8") as stream:
        json.dump(summary, stream, ensure_ascii=False, indent=2)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidates", required=True, type=Path)
    parser.add_argument("--body-audit-dir", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    result = run(args.candidates, args.body_audit_dir, args.output_dir)
    print(json.dumps({key: result[key] for key in ("candidate_rows", "local_body_documents", "body_unavailable_documents", "review_selected_documents", "review_slot_rows", "review_family_count", "review_source_counts", "review_short_body_documents", "human_completed_slots")}))


if __name__ == "__main__":
    main()
