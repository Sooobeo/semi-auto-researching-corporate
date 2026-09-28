"""Join independently generated local P01 diagnostics without changing evidence."""
import argparse
import csv
import hashlib
import json
import os
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


def rows(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def lines(path):
    with path.open(encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def write(path, data):
    with path.open("x", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, list(dict.fromkeys(k for row in data for k in row)))
        writer.writeheader()
        writer.writerows(data)


def run(prior, followup, claim_dir, output, ocr_dir=None):
    if output.exists():
        raise ValueError("output_directory_must_be_new")
    candidate = {r["doc_id"]: r for r in rows(prior / "article_candidates.csv")}
    bodies = {r["doc_id"]: r for r in rows(prior / "body_audit_003/body_audit.csv") if r["body_sha256"]}
    extraction = {r["doc_id"]: r for r in rows(followup / "extraction_review_001/extraction_review.csv")}
    morph = {r["doc_id"]: r for r in rows(followup / "morphology_001/document_metrics.csv")}
    old_sentences = {r["sentence_id"]: r for r in lines(prior / "body_audit_003/sentence_index.jsonl")}
    kiwi_sentences = defaultdict(list)
    for row in lines(followup / "morphology_001/sentence_index.jsonl"):
        kiwi_sentences[row["doc_id"]].append(row)
    signals = lines(claim_dir / "claim_signals.jsonl")
    signal_counts = Counter(row["doc_id"] for row in signals)
    alignments = {r["alignment_id"]: r for r in rows(prior / "comparison_001/sentence_alignment_candidates.csv")}
    claim_pairs = lines(claim_dir / "pair_diagnostics.jsonl")
    assert set(bodies) == set(extraction) == set(morph) == set(kiwi_sentences)
    assert {r["alignment_id"] for r in claim_pairs} == set(alignments)
    priorities = json.loads((followup / "extraction_review_001/review_priorities.json").read_text(encoding="utf-8"))
    reasons = defaultdict(list)
    for name in ("low_alternative_parser_coverage", "long_alternative_only_runs", "table_semantics_pending"):
        for item in priorities[name]:
            reasons[item["doc_id"]].append(name)
    original_review = {r["doc_id"] for r in rows(prior / "classification_001/human_review_queue.csv")}
    document_rows = []
    for doc_id, body in bodies.items():
        m = morph[doc_id]
        boundary_count = int(m["rule_only_end_boundaries"]) + int(m["kiwi_only_end_boundaries"])
        if boundary_count:
            reasons[doc_id].append("sentence_boundary_disagreement")
        document_rows.append({"doc_id": doc_id, "revision_id": body["revision_id"], "source_id": candidate[doc_id]["source_id"],
                              "event_family_id": candidate[doc_id]["event_family_id"], "source_url": candidate[doc_id]["source_url"],
                              "body_chars": body["canonical_body_chars"], "xpath_integrity": body["location_offset_integrity"],
                              "extraction_secondary_check": extraction[doc_id]["mechanical_xpath_diagnostic"],
                              "short_article_assessment": extraction[doc_id]["short_body_assessment"],
                              "rule_sentence_candidates": m["rule_sentence_candidates"], "kiwi_sentence_candidates": m["kiwi_sentence_candidates"],
                              "boundary_disagreement_count": boundary_count, "morpheme_candidates": m["morpheme_candidates"],
                              "claim_signal_candidates": signal_counts[doc_id], "original_20_article_review_sample": doc_id in original_review,
                              "review_priority_score": len(reasons[doc_id]), "review_reasons": "|".join(reasons[doc_id]) or "routine_original_page_check",
                              "published_date_status": body["published_date_status"],
                              "human_completeness_review": "pending", "independent_authorship": "unknown"})
    pair_rows = []
    for row in claim_pairs:
        original = alignments[row["alignment_id"]]
        result = {key: row[key] for key in ("alignment_id", "pair_id", "event_family_id", "left_doc_id", "right_doc_id", "left_sentence_id", "right_sentence_id")}
        for side in ("left", "right"):
            sentence = old_sentences[row[side + "_sentence_id"]]
            assert sentence["text_sha256"] == row[side + "_text_sha256"]
            overlapping = [s for s in kiwi_sentences[row[side + "_doc_id"]] if s["start"] < sentence["end"] and s["end"] > sentence["start"]]
            result[side + "_kiwi_sentence_ids"] = "|".join(s["sentence_id"] for s in overlapping)
            result[side + "_boundary_agrees"] = len(overlapping) == 1 and overlapping[0]["start"] == sentence["start"] and overlapping[0]["end"] == sentence["end"]
        result.update(character_trigram_jaccard=original["character_trigram_jaccard"],
                      common_quantity_value_unit_count=len(row["common_quantity_value_unit"]),
                      quantity_surface_sets_differ=row["quantity_surface_sets_differ"],
                      readiness_blockers="|".join(row["readiness_blockers"]), claim_relation=row["claim_relation"],
                      claim_alignment_ready=row["claim_alignment_ready"], semantic_review="pending")
        pair_rows.append(result)
    output.mkdir(parents=True)
    write(output / "document_review_index.csv", sorted(document_rows, key=lambda r: (-r["review_priority_score"], r["doc_id"])))
    write(output / "pair_review_index.csv", pair_rows)
    task_rows = rows(followup / "p01_inventory/task_status.csv")
    for task in task_rows:
        resolved_evidence = []
        for entry in task["evidence"].split(";"):
            options = [followup / "p01_inventory" / entry, prior.parent / entry, Path(entry)]
            target = next((path for path in options if path.exists()), None)
            if target is None:
                raise ValueError("unresolved_inventory_evidence:" + entry)
            resolved_evidence.append(os.path.relpath(target.resolve(), output.resolve()).replace("\\", "/"))
        task["evidence"] = ";".join(resolved_evidence)
        if task["task_id"] == "P01-T05" and (followup / "metadata_review_001/summary.json").exists():
            task["evidence"] += ";../metadata_review_001/summary.json"
            task["completed_local_work"] += "; 국내기사22건 canonical/기사ID/게시·수정시각 후보 대조 추가"
        if task["task_id"] == "P01-T06" and ocr_dir is not None:
            if not (ocr_dir / "summary.json").exists():
                raise ValueError("ocr_summary_missing")
            task["evidence"] += ";" + os.path.relpath((ocr_dir / "summary.json").resolve(), output.resolve()).replace("\\", "/")
            task["remaining_reason"] = "이미지형 페이지 로컬 OCR 보조결과 추가; OCR은 자동 후보이며 이미지·PDF표 의미 완전성의 사람 검증 미보장"
        if task["task_id"] == "P01-T11":
            task["evidence"] = "../handoff_p0.md;../p01_inventory/additional_checks.json"
        if task["task_id"] == "P01-T10":
            task["status"] = "done"
            task["completed_local_work"] = "공식자료·국내기사별 분모, 출처 판단, 실패·제약 및 현재 분석 결과를 통합해 재계산 가능한 보고서와 인계 자료 작성"
            task["evidence"] = "../briefing.md;../handoff_p0.md;../run_manifest.json;../p01_inventory/summary.json"
            task["remaining_reason"] = "측정·보고 완료; 권리·본문 완전성·독립 표현·사람 감사의 미확인 상태 자체는 유지"
    write(output / "task_status.csv", task_rows)
    summary = {"version": "p01-followup-index/0.3", "completed_at": datetime.now(timezone.utc).isoformat(),
               "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               "documents": len(document_rows), "alignment_candidates": len(pair_rows),
               "alignment_candidates_with_boundary_disagreement": sum(not(r["left_boundary_agrees"] and r["right_boundary_agrees"]) for r in pair_rows),
               "documents_with_additional_review_flags": sum(bool(reasons[doc_id]) for doc_id in bodies),
               "task_status_counts": dict(Counter(r["status"] for r in task_rows)),
               "claim_diagnostics_dir": str(claim_dir), "ocr_dir": str(ocr_dir) if ocr_dir else None, "human_reviews_completed": 0,
               "status": "joined_provenance_and_review_priorities_not_human_gold"}
    (output / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=True))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prior-dir", type=Path, required=True)
    parser.add_argument("--followup-dir", type=Path, required=True)
    parser.add_argument("--claim-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--ocr-dir", type=Path)
    args = parser.parse_args()
    run(args.prior_dir, args.followup_dir, args.claim_dir, args.output_dir, args.ocr_dir)
