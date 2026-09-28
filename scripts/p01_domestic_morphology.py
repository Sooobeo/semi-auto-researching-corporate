"""Local Kiwi sentence/POS pilot with original Unicode offsets; no network calls.

Source text, forms and lemmas remain in raw/. Public outputs contain positions,
hashes and descriptive counts only. Segmentation disagreements are not error rates.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import html
import importlib.metadata
import json
import platform
import re
from collections import Counter, defaultdict, deque
from datetime import datetime, timezone
from pathlib import Path

from kiwipiepy import Kiwi

VERSION = "p01-domestic-morphology/0.1"


def sha(text):
    return hashlib.sha256(text if isinstance(text, bytes) else text.encode("utf-8")).hexdigest()


def jsonl(path):
    with path.open(encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def csv_read(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def csv_write(path, rows):
    with path.open("x", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, list(dict.fromkeys(key for row in rows for key in row)) or ["status"])
        writer.writeheader()
        writer.writerows(rows)


def segments(start, end, atoms):
    return [{"source_xpath": atom["source_xpath"], "source_start": max(start, atom["body_start"]) - atom["body_start"],
             "source_end": min(end, atom["body_end"]) - atom["body_start"],
             "body_start": max(start, atom["body_start"]), "body_end": min(end, atom["body_end"])}
            for atom in atoms if start < atom["body_end"] and end > atom["body_start"]]


def selftest(kiwi):
    # Authored fixtures; neither news excerpts nor semantic-quality gold.
    examples = ["😀 삼성전자는 제품을 개발했다. 다음 문장이다.", "가나다\n\n제품 12.5% 성장했다.",
                "한글과 English HBM3E 12단을 비교한다.", "\"출하할 계획\"이라고 말했다.",
                "줄바꿈\r\n뒤 문장입니다.", "이걸 나눠 주세요.", "가\u0301나다와 가나다."]
    for text in examples:
        for sentence in kiwi.split_into_sents(text, return_tokens=True):
            assert text[sentence.start:sentence.end] == sentence.text
            for token in sentence.tokens:
                assert 0 <= token.start <= token.end <= len(text)
    emoji_text = examples[0]
    tokens = kiwi.tokenize(emoji_text)
    emoji = [token for token in tokens if token.form == "😀"]
    assert emoji and emoji[0].start == 0 and emoji[0].end == 1
    company = [token for token in tokens if token.form.startswith("삼성")]
    assert company and company[0].start == emoji_text.index("삼성")
    return {"authored_fixtures": len(examples), "sentence_substring_roundtrip": "pass",
            "token_bounds": "pass", "emoji_python_codepoint_offset": "pass",
            "linguistic_accuracy_evaluated": False}


def run(audit_dir, candidates_path, output):
    if output.exists():
        raise ValueError("output_directory_must_be_new")
    documents = jsonl(audit_dir / "raw/documents.jsonl")
    candidate = {row["doc_id"]: row for row in csv_read(candidates_path)}
    atoms, old_sentences = defaultdict(list), defaultdict(list)
    for row in jsonl(audit_dir / "raw/atoms.jsonl"):
        atoms[row["doc_id"]].append(row)
    for row in jsonl(audit_dir / "raw/sentences.jsonl"):
        old_sentences[row["doc_id"]].append(row)
    kiwi = Kiwi(num_workers=1)
    fixture_results = selftest(kiwi)
    output.mkdir(parents=True)
    (output / "raw").mkdir()
    (output / "raw/.gitignore").write_text("*\n", encoding="utf-8")
    files = {key: (output / path).open("x", encoding="utf-8") for key, path in {
        "sentences": "raw/sentences.jsonl", "tokens": "raw/morphemes.jsonl", "gaps": "raw/coverage_gaps.jsonl",
        "sentence_index": "sentence_index.jsonl", "token_index": "morpheme_index.jsonl"}.items()}

    def emit(key, value):
        files[key].write(json.dumps(value, ensure_ascii=False) + "\n")

    metrics, all_sentences, pos_counts = [], [], Counter()
    token_total = zero_length = form_diff = overlapping = 0
    try:
        for doc in documents:
            doc_id, text = doc["doc_id"], doc["canonical_body_raw"]
            source = candidate[doc_id]
            old = old_sentences[doc_id]
            old_end = {row["end"] for row in old}
            analyzed = kiwi.split_into_sents(text, return_tokens=True)
            new_end = {row.end for row in analyzed}
            coverage = bytearray(len(text))
            doc_token_count = doc_zero = doc_diff = doc_overlap = 0
            previous_start, previous_end = 0, 0
            for ordinal, sentence in enumerate(analyzed, 1):
                assert 0 <= sentence.start <= sentence.end <= len(text)
                assert text[sentence.start:sentence.end] == sentence.text
                identifier = f'{doc_id}:{doc["revision_id"]}:K0231:S{ordinal:05d}'
                intersecting = [row for row in old if row["start"] < sentence.end and row["end"] > sentence.start]
                public = {"sentence_id": identifier, "doc_id": doc_id, "revision_id": doc["revision_id"],
                          "start": sentence.start, "end": sentence.end, "text_sha256": sha(sentence.text),
                          "offset_unit": "unicode_codepoint", "offset_basis": "canonical_body_raw",
                          "source_segments": segments(sentence.start, sentence.end, atoms[doc_id]),
                          "segmentation": "kiwi_model_candidate", "human_audit_status": "pending",
                          "old_rule_sentence_ids": [row["sentence_id"] for row in intersecting],
                          "boundary_matches_one_rule_sentence": len(intersecting) == 1 and sentence.start == intersecting[0]["start"] and sentence.end == intersecting[0]["end"],
                          "roundtrip": True}
                emit("sentence_index", public)
                private = public | {"text": sentence.text}
                emit("sentences", private)
                all_sentences.append(private | {"source_id": source["source_id"], "event_family_id": source["event_family_id"]})
                for token in sentence.tokens:
                    assert 0 <= token.start <= token.end <= len(text)
                    doc_token_count += 1
                    raw_surface = text[token.start:token.end]
                    length_zero = token.start == token.end
                    differs = raw_surface != token.form
                    # Overlapping morphemes and zero-width endings are model alignment features.
                    overlap = token.start < previous_end and token.end > previous_start
                    doc_zero += length_zero
                    doc_diff += differs
                    doc_overlap += overlap
                    previous_start, previous_end = token.start, token.end
                    for index in range(token.start, token.end):
                        coverage[index] = 1
                    record = {"morpheme_id": identifier + f":M{doc_token_count:06d}", "sentence_id": identifier,
                              "doc_id": doc_id, "revision_id": doc["revision_id"], "start": token.start, "end": token.end,
                              "pos_candidate": token.tag, "raw_surface_sha256": sha(raw_surface), "form_sha256": sha(token.form),
                              "surface_differs_from_model_form": differs, "zero_width_alignment": length_zero,
                              "overlaps_previous_token": overlap, "offset_unit": "unicode_codepoint",
                              "offset_basis": "canonical_body_raw", "source_segments": segments(token.start, token.end, atoms[doc_id]),
                              "alignment_type": "model_form_to_raw_span_may_overlap_or_be_zero_width",
                              "linguistic_status": "model_candidate_not_gold"}
                    emit("token_index", record)
                    emit("tokens", record | {"raw_surface": raw_surface, "form": token.form})
                    pos_counts[token.tag] += 1
            missing = [i for i, char in enumerate(text) if not char.isspace() and not coverage[i]]
            emit("gaps", {"doc_id": doc_id, "uncovered_nonspace_positions": missing,
                          "uncovered_characters": [text[index] for index in missing]})
            token_total += doc_token_count
            zero_length += doc_zero
            form_diff += doc_diff
            overlapping += doc_overlap
            metrics.append({"doc_id": doc_id, "source_id": source["source_id"], "event_family_id": source["event_family_id"],
                            "body_sha256": sha(text), "body_characters": len(text), "rule_sentence_candidates": len(old),
                            "kiwi_sentence_candidates": len(analyzed), "common_end_boundaries": len(old_end & new_end),
                            "rule_only_end_boundaries": len(old_end - new_end), "kiwi_only_end_boundaries": len(new_end - old_end),
                            "boundary_jaccard_diagnostic": round(len(old_end & new_end) / len(old_end | new_end), 6) if old_end | new_end else None,
                            "morpheme_candidates": doc_token_count, "zero_width_tokens": doc_zero,
                            "model_form_differs_from_raw_surface": doc_diff, "overlaps_previous_token": doc_overlap,
                            "uncovered_nonspace_characters": len(missing), "sentence_roundtrip": "pass",
                            "offset_bounds": "pass", "boundary_accuracy": "not_measured_requires_human_gold"})
    finally:
        for stream in files.values():
            stream.close()
    csv_write(output / "document_metrics.csv", metrics)
    csv_write(output / "pos_counts.csv", [{"pos_candidate": tag, "count": count, "interpretation": "pooled_model_counts_not_outlet_style"} for tag, count in pos_counts.most_common()])
    # Audit sample: all documents in rotation; disagreements first within each document.
    groups = defaultdict(list)
    for row in all_sentences:
        groups[row["doc_id"]].append(row)
    queues = {key: deque(sorted(value, key=lambda row: (row["boundary_matches_one_rule_sentence"], row["start"]))) for key, value in groups.items()}
    chosen = []
    while len(chosen) < min(200, len(all_sentences)):
        added = False
        for key in sorted(queues):
            if queues[key] and len(chosen) < 200:
                chosen.append(queues[key].popleft())
                added = True
        if not added:
            break
    review_rows = [{key: row[key] for key in ("sentence_id", "doc_id", "source_id", "event_family_id", "start", "end", "text_sha256", "boundary_matches_one_rule_sentence")} |
                   {"human_sentence_boundary": "pending", "human_morphology": "pending", "reviewer": "unassigned",
                    "selection_basis": "document_round_robin_boundary_disagreement_priority_not_random"} for row in chosen]
    csv_write(output / "sentence_review_queue.csv", review_rows)
    esc = html.escape
    page = ['<!doctype html><html lang="ko"><meta charset="utf-8"><title>P01 문장 검토 200개</title>',
            '<style>body{font:16px/1.7 sans-serif;max-width:950px;margin:30px auto;padding:20px}article{border-top:1px solid #ccd;padding:14px 0}small{overflow-wrap:anywhere;color:#536171}p{white-space:pre-wrap}</style>',
            '<h1>P01 문장 경계 검토 자료</h1><p>로컬 분석기가 제안한 문장입니다. 기존 규칙과 다른 경계를 우선해 문서별로 골랐습니다. 차이가 있다는 사실만으로 어느 쪽이 틀렸다고 판단하지 않습니다. 사람 검토 완료·정답 데이터가 아닙니다. 원문은 외부 공유하지 않습니다.</p>']
    for index, row in enumerate(chosen, 1):
        page.append(f'<article><h2>{index}. {esc(row["source_id"])} · {esc(row["event_family_id"])}</h2><p>{esc(row["text"])}</p><small>{esc(row["sentence_id"])}<br>원문 위치 {row["start"]}–{row["end"]}, 기존 경계 일치: {row["boundary_matches_one_rule_sentence"]}</small></article>')
    page.append('</html>')
    (output / "raw/review.html").write_text("\n".join(page), encoding="utf-8")
    summary = {"version": VERSION, "completed_at": datetime.now(timezone.utc).isoformat(),
               "script_sha256": sha(Path(__file__).read_bytes()), "python": platform.python_version(),
               "packages": {name: importlib.metadata.version(name) for name in ["kiwipiepy", "kiwipiepy_model", "numpy"]},
               "model_configuration": "Kiwi(num_workers=1); package defaults; no custom lexicon or training",
               "docs_reference": "https://bab2min.github.io/kiwipiepy/v0.23.1/kr/",
               "input_body_file_sha256": sha((audit_dir / "raw/documents.jsonl").read_bytes()),
               "input_body_audit": str(audit_dir), "documents": len(documents),
               "rule_sentence_candidates": sum(row["rule_sentence_candidates"] for row in metrics),
               "kiwi_sentence_candidates": len(all_sentences), "morpheme_candidates": token_total,
               "zero_width_tokens": zero_length, "model_forms_different_from_raw_surface": form_diff,
               "tokens_overlapping_previous": overlapping,
               "uncovered_nonspace_characters": sum(row["uncovered_nonspace_characters"] for row in metrics),
               "common_end_boundaries": sum(row["common_end_boundaries"] for row in metrics),
               "rule_only_end_boundaries": sum(row["rule_only_end_boundaries"] for row in metrics),
               "kiwi_only_end_boundaries": sum(row["kiwi_only_end_boundaries"] for row in metrics),
               "review_sentences": len(chosen), "review_documents": len({row["doc_id"] for row in chosen}),
               "human_reviewed_sentences": 0, "synthetic_checks": fixture_results,
               "model_api_calls": 0, "ontology": "not_performed", "status": "model_candidates_offsets_checked_semantic_accuracy_unmeasured",
               "limitations": ["Kiwi form is an analysis, not necessarily the original substring; zero-width/overlapping spans are retained.",
                               "Sentence boundaries disagreeing with punctuation rules are review targets, not errors or measured F1.",
                               "Morphology and aggregate POS counts do not prove shared claims, authorship or outlet style."]}
    (output / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: summary[key] for key in ["documents", "kiwi_sentence_candidates", "morpheme_candidates", "zero_width_tokens", "uncovered_nonspace_characters", "review_sentences"]}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--body-audit-dir", type=Path, required=True)
    parser.add_argument("--candidates", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    run(args.body_audit_dir, args.candidates, args.output_dir)
