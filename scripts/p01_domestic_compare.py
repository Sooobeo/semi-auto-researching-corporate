"""Offline, provisional P01 comparison candidates; no network or model inference.

All copied source text stays in ignored raw/. Similarity ranks review candidates;
it does not establish a shared proposition, speaker, genre or original authorship.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import html
import itertools
import json
import re
import statistics
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

VERSION = "p01-domestic-compare/0.1"


def sha(value):
    return hashlib.sha256(value if isinstance(value, bytes) else value.encode("utf-8")).hexdigest()


def csv_rows(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def jsonl(path):
    with path.open(encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def csv_write(path, rows):
    fields = list(dict.fromkeys(key for row in rows for key in row)) or ["status"]
    with path.open("x", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fields)
        writer.writeheader()
        writer.writerows(rows)


def normalized(text):
    return re.sub(r"[^\w]", "", unicodedata.normalize("NFKC", text).lower())


def grams(text):
    value = normalized(text)
    return {value[i:i + 3] for i in range(max(0, len(value) - 2))}


def jaccard(left, right):
    union = left | right
    return len(left & right) / len(union) if union else 0.0


def run(candidates_path, audit_dir, output):
    if output.exists():
        raise ValueError("output_directory_must_be_new")
    candidates = csv_rows(candidates_path)
    metadata = {row["doc_id"]: row for row in candidates}
    documents = {row["doc_id"]: row for row in jsonl(audit_dir / "raw/documents.jsonl")}
    audit = {row["doc_id"]: row for row in csv_rows(audit_dir / "body_audit.csv")}
    all_sentences = jsonl(audit_dir / "raw/sentences.jsonl")
    atoms = defaultdict(list)
    for row in jsonl(audit_dir / "raw/atoms.jsonl"):
        atoms[row["doc_id"]].append(row)
    sentences, eligible = defaultdict(list), defaultdict(list)
    excluded = Counter()
    for row in all_sentences:
        doc = documents[row["doc_id"]]
        assert doc["canonical_body_raw"][row["start"]:row["end"]] == row["text"]
        sentences[row["doc_id"]].append(row)
        roles = {atom["segment_position_candidate"] for atom in atoms[row["doc_id"]]
                 if atom["body_start"] < row["end"] and atom["body_end"] > row["start"]}
        reason = ("short_segment" if len(normalized(row["text"])) < 30 else
                  "caption_or_subheading" if roles and roles <= {"caption", "subheadline", "subheading"} else
                  "footer_byline_or_photo_cue" if re.search(r"@|무단\s*(?:전재|복제)|재배포\s*금지|저작권|ⓒ|\[사진|사진\s*=", row["text"]) else "")
        if reason:
            excluded[reason] += 1
        else:
            row = dict(row)
            row["position_candidate"] = "lead_candidate" if len(eligible[row["doc_id"]]) < 2 else "body_candidate"
            eligible[row["doc_id"]].append(row)
    output.mkdir(parents=True)
    (output / "raw").mkdir()
    (output / "raw/.gitignore").write_text("*\n", encoding="utf-8")
    chunks = 0
    with (output / "raw/chunks.jsonl").open("x", encoding="utf-8") as raw, (output / "chunk_index.jsonl").open("x", encoding="utf-8") as public:
        for sentence in all_sentences:
            for index, match in enumerate(re.finditer(r"\S+", sentence["text"]), 1):
                start, end = sentence["start"] + match.start(), sentence["start"] + match.end()
                text = match.group()
                assert documents[sentence["doc_id"]]["canonical_body_raw"][start:end] == text
                record = {"chunk_id": sentence["sentence_id"] + f":E{index:04d}",
                          "doc_id": sentence["doc_id"], "revision_id": sentence["revision_id"],
                          "sentence_id": sentence["sentence_id"], "start": start, "end": end,
                          "offset_unit": "unicode_codepoint", "offset_basis": "canonical_body_raw",
                          "chunk_type": "whitespace_eojeol_candidate", "raw_sha256": sha(text),
                          "normalized_nfkc_sha256": sha(unicodedata.normalize("NFKC", text)),
                          "normalization_changes_text": unicodedata.normalize("NFKC", text) != text,
                          "normalization_alignment": "whole_token_raw_span_only",
                          "roundtrip": True, "morphology_status": "not_performed", "human_review": "pending"}
                raw.write(json.dumps(record | {"raw": text, "normalized": unicodedata.normalize("NFKC", text)}, ensure_ascii=False) + "\n")
                public.write(json.dumps(record, ensure_ascii=False) + "\n")
                chunks += 1
    metrics, family_docs = [], defaultdict(list)
    for doc_id, document in documents.items():
        source = metadata[doc_id]
        lengths = [len(row["text"]) for row in sentences[doc_id]]
        metrics.append({"doc_id": doc_id, "revision_id": document["revision_id"], "source_id": source["source_id"],
                        "event_family_id": source["event_family_id"], "body_chars": len(document["canonical_body_raw"]),
                        "sentence_candidates": len(lengths), "eligible_sentence_candidates": len(eligible[doc_id]),
                        "mean_sentence_chars": round(statistics.mean(lengths), 2) if lengths else None,
                        "median_sentence_chars": statistics.median(lengths) if lengths else None,
                        "quoted_sentence_candidates": sum(s["speech_candidate"] == "quoted_speech_candidate" for s in sentences[doc_id]),
                        "indirect_attribution_candidates": sum(s["speech_candidate"] == "indirect_attribution_candidate" for s in sentences[doc_id]),
                        "body_diagnostics": audit[doc_id].get("diagnostics", ""),
                        "assessment": "descriptive_rule_counts_content_genre_and_speaker_uncontrolled"})
        family_docs[source["event_family_id"]].append(doc_id)
    pairs, alignments, cards = [], [], []
    for family, doc_ids in sorted(family_docs.items()):
        for left_id, right_id in itertools.combinations(sorted(doc_ids), 2):
            if metadata[left_id]["source_id"] == metadata[right_id]["source_id"]:
                continue
            pair_id = "PAIR-" + sha(left_id + "|" + right_id)[:16]
            left_body, right_body = documents[left_id]["canonical_body_raw"], documents[right_id]["canonical_body_raw"]
            ranking = []
            for left, right in itertools.product(eligible[left_id], eligible[right_id]):
                if left["position_candidate"] != right["position_candidate"]:
                    continue
                if left["speech_candidate"] != right["speech_candidate"]:
                    continue
                similarity = jaccard(grams(left["text"]), grams(right["text"]))
                if similarity < 0.12:
                    continue
                ranking.append((similarity, left, right))
            chosen, used_left, used_right = [], set(), set()
            for similarity, left, right in sorted(ranking, key=lambda item: (-item[0], item[1]["sentence_id"], item[2]["sentence_id"])):
                if left["sentence_id"] in used_left or right["sentence_id"] in used_right:
                    continue
                used_left.add(left["sentence_id"])
                used_right.add(right["sentence_id"])
                alignment_id = pair_id + f":A{len(chosen)+1:02d}"
                numbers_left = set(re.findall(r"\d[\d,]*(?:\.\d+)?", left["text"]))
                numbers_right = set(re.findall(r"\d[\d,]*(?:\.\d+)?", right["text"]))
                record = {"alignment_id": alignment_id, "pair_id": pair_id, "event_family_id": family,
                          "left_doc_id": left_id, "right_doc_id": right_id,
                          "left_sentence_id": left["sentence_id"], "right_sentence_id": right["sentence_id"],
                          "left_start": left["start"], "left_end": left["end"], "right_start": right["start"], "right_end": right["end"],
                          "left_text_sha256": sha(left["text"]), "right_text_sha256": sha(right["text"]),
                          "character_trigram_jaccard": round(similarity, 6),
                          "position_candidate": left["position_candidate"], "speech_candidate": left["speech_candidate"],
                          "shared_number_surface_count": len(numbers_left & numbers_right),
                          "number_surface_sets_differ": numbers_left != numbers_right,
                          "number_meaning_relation": "unassessed_units_periods_scopes_required",
                          "claim_relation": "uncertain", "speaker_relation": "unknown",
                          "genre_relation": "unknown", "production_independence": "unknown",
                          "reference_claim_status": "anchor_claim_not_aligned", "style_comparison_eligible": False,
                          "status": "ranked_review_candidate_not_verified_match"}
                alignments.append(record)
                chosen.append(record)
                cards.append(record | {"left_text": left["text"], "right_text": right["text"],
                                      "left_source_segments": left["source_segments"], "right_source_segments": right["source_segments"],
                                      "left_source_url": metadata[left_id]["source_url"], "right_source_url": metadata[right_id]["source_url"]})
                if len(chosen) == 8:
                    break
            exact = {normalized(row["text"]) for row in eligible[left_id]} & {normalized(row["text"]) for row in eligible[right_id]}
            pairs.append({"pair_id": pair_id, "event_family_id": family, "left_doc_id": left_id, "right_doc_id": right_id,
                          "left_source_id": metadata[left_id]["source_id"], "right_source_id": metadata[right_id]["source_id"],
                          "body_character_trigram_jaccard": round(jaccard(grams(left_body), grams(right_body)), 6),
                          "normalized_body_equal": normalized(left_body) == normalized(right_body),
                          "shared_exact_normalized_sentence_candidates": len(exact),
                          "ranked_sentence_pairs": len(chosen), "content_relation": "uncertain",
                          "pair_status": "same_provisional_family_candidate", "style_comparison_eligible": False})
    csv_write(output / "article_metrics.csv", metrics)
    csv_write(output / "article_pairs.csv", pairs)
    csv_write(output / "sentence_alignment_candidates.csv", alignments)
    with (output / "raw/alignment_cards.jsonl").open("x", encoding="utf-8") as stream:
        for card in cards:
            stream.write(json.dumps(card, ensure_ascii=False) + "\n")
    esc = html.escape
    page = ['<!doctype html><html lang="ko"><meta charset="utf-8"><title>P01 문장 비교 후보</title>',
            '<style>body{font:16px/1.7 sans-serif;max-width:1200px;margin:36px auto;padding:0 24px;color:#182633}article{border-top:1px solid #bbb;padding:20px 0}.pair{display:grid;grid-template-columns:1fr 1fr;gap:28px}p{white-space:pre-wrap}small{color:#58636e}a{color:#145ea8}@media(max-width:700px){.pair{grid-template-columns:1fr}}</style>',
            '<h1>P01 문장 비교 후보</h1><p>로컬 검토용 원문입니다. 동일 주장·화자·장르·독립 원저작 판정 전의 규칙 후보이며, 문체 결론이나 gold가 아닙니다. 숫자 표면 차이는 모순을 뜻하지 않습니다. 공유·재배포용 파일이 아닙니다.</p>']
    for card in cards:
        page.extend([f'<article><h2>{esc(card["event_family_id"])} · {esc(card["alignment_id"].split(":")[-1])}</h2>',
                     f'<small>3-gram Jaccard {card["character_trigram_jaccard"]:.3f} · {esc(card["position_candidate"])} · {esc(card["speech_candidate"])}</small><div class="pair">'])
        for side in ("left", "right"):
            page.append(f'<section><a href="{esc(card[side + "_source_url"], quote=True)}">{esc(metadata[card[side + "_doc_id"]]["source_id"])}</a><p>{esc(card[side + "_text"])}</p><small>{esc(card[side + "_sentence_id"])}</small></section>')
        page.append('</div></article>')
    page.append('</html>')
    (output / "raw/review.html").write_text("\n".join(page), encoding="utf-8")
    summary = {"version": VERSION, "completed_at": datetime.now(timezone.utc).isoformat(),
               "script_sha256": sha(Path(__file__).read_bytes()), "candidate_sha256": sha(candidates_path.read_bytes()),
               "body_audit_summary_sha256": sha((audit_dir / "summary.json").read_bytes()), "body_audit_dir": str(audit_dir),
               "articles": len(documents), "families_with_body": len(family_docs),
               "families_with_multiple_sources": sum(len({metadata[doc]["source_id"] for doc in ids}) > 1 for ids in family_docs.values()),
               "same_family_article_pair_candidates": len(pairs), "ranked_sentence_pair_candidates": len(alignments),
               "pairs_with_ranked_candidates": sum(row["ranked_sentence_pairs"] > 0 for row in pairs),
               "verified_same_claim_pairs": 0, "verified_independent_style_pairs": 0,
               "sentence_candidates": len(all_sentences), "eligible_sentence_candidates": sum(map(len, eligible.values())),
               "excluded_sentence_candidates_by_reason": dict(excluded), "eojeol_candidates": chunks,
               "sentence_and_eojeol_raw_offset_roundtrip": "pass", "offset_unit": "unicode_codepoint",
               "normalization": "NFKC only as a parallel token value; offsets always address original canonical body",
               "method": "same provisional family, same rule position and speech category, trigram Jaccard >= 0.12, greedy non-reused top 8",
               "method_validation": "heuristic_unvalidated_no_precision_or_recall_claim",
               "limitations": ["Anchor propositions not yet aligned; speaker, genre, scope, period, unit and origin require review.",
                               "First two eligible segments are lead candidates, not verified lead boundaries.",
                               "Whitespace units are eojeol candidates, not morphology or linguistic chunks.",
                               "Counts and similarities are descriptive and cannot establish outlet style or independence."]}
    (output / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: summary[key] for key in ("articles", "same_family_article_pair_candidates", "ranked_sentence_pair_candidates", "eojeol_candidates", "sentence_and_eojeol_raw_offset_roundtrip")}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidates", type=Path, required=True)
    parser.add_argument("--body-audit-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    run(args.candidates, args.body_audit_dir, args.output_dir)
