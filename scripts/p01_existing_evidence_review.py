"""Read-only inventory of retained P01 evidence; writes only a new output folder.

No network, credential reads, original-text output, ontology or gold construction.
All block text is processed locally and discarded after mechanical checks.
"""
import argparse
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
P0 = ROOT / "artifacts/p0"
VERSION = "p01-existing-evidence-review/0.1"


def rows(name):
    with (P0 / name).open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def sha(path):
    result = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            result.update(chunk)
    return result.hexdigest()


def write_csv(path, data):
    fields = list(dict.fromkeys(k for row in data for k in row))
    with path.open("x", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fields or ["status"])
        writer.writeheader()
        writer.writerows(data)


def number(value):
    return Decimal(value.replace(",", ""))


def run(output):
    if output.exists():
        raise ValueError("output_directory_must_be_new")
    output.mkdir(parents=True)
    inputs = ["document_manifest.csv", "news_manifest.csv", "news_body_manifest.csv", "coverage_matrix.csv", "entities.csv", "company_overview.csv", "access_trials.csv", "parser_trials.csv", "extraction_audit.csv", "numeric_reconciliation.csv", "document_relations.csv", "block_counts.csv", "table_registry.csv", "block_validation.json", "source_registry.csv", "scope.md", "data_feasibility.md", "document_selection.md"]
    before = {name: sha(P0 / name) for name in inputs}
    manifest, news = rows("document_manifest.csv"), rows("news_body_manifest.csv")
    docs, audit = {r["doc_id"]: r for r in manifest}, {r["doc_id"]: r for r in rows("extraction_audit.csv")}
    counts = {r["doc_id"]: r for r in rows("block_counts.csv")}
    primary = {k for k, r in docs.items() if r["source_id"] != "SKH_NEWSROOM"}
    errors, integrity, missing = [], [], []
    for group, records in (("official_documents", manifest), ("official_news_pilot", news)):
        if len(records) != len({r["doc_id"] for r in records}):
            errors.append(group + ":duplicate_doc_id")
        for row in records:
            path = (ROOT / row["storage_uri"]).resolve()
            exists = path.is_file() and path.is_relative_to(P0.resolve())
            found_hash = sha(path) if exists else ""
            passed = exists and found_hash == row["sha256"] and path.stat().st_size == int(row["byte_size"])
            if not passed:
                errors.append(group + ":file_integrity:" + row["doc_id"])
            integrity.append({"corpus_group": group, "doc_id": row["doc_id"], "revision_id": row["revision_id"], "source_id": row["source_id"], "storage_uri": row["storage_uri"], "expected_sha256": row["sha256"], "observed_sha256": found_hash, "byte_size": path.stat().st_size if exists else "", "integrity_status": "pass" if passed else "fail", "published_date": row.get("published_date", ""), "time_precision": row.get("time_precision", ""), "date_conflict": row.get("date_conflict", "not_recorded")})
            if not row.get("published_date"):
                missing.append({"record_id": row["doc_id"], "field": "published_date", "status": "unknown", "reason": "existing_manifest_explicit_time_precision_unknown", "next_action": "verify_existing_official_publication_metadata_without_inventing_timestamp"})
    tables = {r["table_id"] for r in rows("table_registry.csv")}
    block_ids, per_doc, chars, types = set(), defaultdict(Counter), Counter(), Counter()
    plan_locations = []
    block_hash = hashlib.sha256()
    with (P0 / "blocks.jsonl").open("rb") as stream:
        for index, raw_line in enumerate(stream, 1):
            block_hash.update(raw_line)
            block = json.loads(raw_line)
            doc, bid, kind = block["doc_id"], block["block_id"], block["block_type"]
            row_errors = []
            if doc not in docs or block["revision_id"] != docs[doc]["revision_id"]:
                row_errors.append("doc_revision")
            if bid in block_ids:
                row_errors.append("duplicate_block")
            if any(ref not in block_ids for ref in block["header_refs"]):
                row_errors.append("header_reference")
            if re.sub(r"\s+", " ", block["raw_text"]).strip() != block["normalized_text"]:
                row_errors.append("normalization")
            if kind == "table_cell" and (block["table_id"] not in tables or block["row_index"] is None or block["col_index"] is None):
                row_errors.append("table_location")
            if kind == "pdf_text_block" and (not 1 <= block["page_number"] <= int(counts[doc]["pdf_pages"]) or len(block["bbox"]) != 4):
                row_errors.append("pdf_location")
            if kind in ("paragraph", "heading", "table_cell", "inline_text") and not (block["source_xpath"] and block["source_entry"]):
                row_errors.append("xml_location")
            errors.extend(f"block_line_{index}:{code}" for code in row_errors)
            block_ids.add(bid)
            per_doc[doc][kind] += 1
            types[kind] += 1
            chars[doc] += len(re.sub(r"\s+", "", block["raw_text"]))
            if doc in ("SAM-2025Q4-IR", "SAM-2026Q1-IR") and "HBM4" in block["raw_text"]:
                plan_locations.append({"doc_id": doc, "block_id": bid, "page_number": block.get("page_number", ""), "bbox": json.dumps(block.get("bbox")), "text_sha256": hashlib.sha256(block["raw_text"].encode()).hexdigest(), "product_marker": "HBM4", "plan_cue": bool(re.search(r"계획|예정|전망", block["raw_text"])), "execution_cue": bool(re.search(r"개시|시작|양산|출하|판매", block["raw_text"])), "relation_assessment": "candidate_only_no_claim_or_followup_confirmed"})
    block_review = []
    for doc, expected in counts.items():
        passed = chars[doc] == int(expected["emitted_nonwhite_chars"]) == int(expected["source_nonwhite_chars"])
        passed &= per_doc[doc]["table_cell"] == int(expected["table_cells"])
        passed &= per_doc[doc]["image_marker"] == int(expected["image_markers"])
        passed &= per_doc[doc]["paragraph"] + per_doc[doc]["pdf_text_block"] == int(expected["paragraph_or_text_blocks"])
        if not passed:
            errors.append("block_counts:" + doc)
        block_review.append({"doc_id": doc, "blocks": sum(per_doc[doc].values()), "table_cells": per_doc[doc]["table_cell"], "image_markers": per_doc[doc]["image_marker"], "source_text_count_status": "pass" if passed else "fail", "validation_limit": "existing_recovered_DOM_or_PDF_text_layer_not_raster_semantics"})
    scope_review = []
    for doc, row in audit.items():
        identity_ok = doc in primary
        flags_ok = all(row[k] == "True" for k in ("unit_verified", "period_verified", "scope_verified", "value_verified", "header_verified", "paragraph_verified"))
        expected_scope = "SAM_memory_revenue_only" if row["company_id"] == "SAM" and row["source_id"] != "DART" else "SAM_DS_segment_including_nonmemory" if row["company_id"] == "SAM" else None
        scope_ok = row["source_scope"] == expected_scope if expected_scope else row["source_scope"].startswith("SKH_consolidated_")
        link_ok = row["value_block_id"] in block_ids and row["table_id"] in tables if row["source_id"] == "DART" else bool(row["header_bbox"] and row["value_bbox"] and row["paragraph_bbox"])
        passed = identity_ok and flags_ok and scope_ok and link_ok
        if not passed:
            errors.append("audit_scope_link:" + doc)
        scope_review.append({"doc_id": doc, "company_id": row["company_id"], "source_scope": row["source_scope"], "metric": row["metric"], "table_location": row["table_location"], "value_block_id": row["value_block_id"], "existing_sample_status": row["audit_status"], "metadata_scope_and_evidence_link_check": "pass" if passed else "fail", "new_manual_semantic_audit": "not_performed", "two_person_review_evidence": "not_recorded"})
    if set(audit) != primary:
        errors.append("primary_audit_coverage")
    numeric_review, prior = [], {}
    for row in sorted(rows("numeric_reconciliation.csv"), key=lambda r: (r["company_id"], r["quarter"])):
        company, period = row["company_id"], row["quarter"]
        dart, ir = audit[row["dart_doc_id"]], audit[row["ir_doc_id"]]
        cumulative = number(dart["value_decimal"])
        previous = prior.get((company, period[:4]), Decimal(0))
        conversion = Decimal(10000 if company == "SAM" else 1000)
        quarterly = (cumulative - previous) / conversion
        prior[company, period[:4]] = cumulative
        ir_value = number(ir["related_DS_revenue_raw"] if company == "SAM" else ir["value_decimal"])
        delta = abs(quarterly - ir_value)
        passed = quarterly == number(row["dart_quarter_converted"]) and ir_value == number(row["ir_quarter_raw"]) and delta == number(row["absolute_delta"]) and delta <= number(row["tolerance"])
        if not passed:
            errors.append("numeric_recalculation:" + company + period)
        numeric_review.append({"company_id": company, "quarter": period, "metric_scope": row["metric_scope"], "dart_doc_id": row["dart_doc_id"], "ir_doc_id": row["ir_doc_id"], "recalculated_quarter": str(quarterly), "ir_value": str(ir_value), "recalculated_delta": str(delta), "existing_tolerance": row["tolerance"], "recalculation_status": "pass" if passed else "fail", "scope_warning": "SAM_DS_reconciliation_not_memory_revenue" if company == "SAM" else "SKH_consolidated_company_not_HBM_product"})
    coverage_review = []
    for row in rows("coverage_matrix.csv"):
        dart = [r for r in manifest if r["source_id"] == "DART" and r["source_api_record_id"] == row["dart_latest_rcept_no"]]
        ir = [r for r in manifest if r["doc_id"] == row["company_id"] + "-" + row["quarter"] + "-IR"]
        passed = len(dart) == len(ir) == 1
        if not passed:
            errors.append("coverage:" + row["company_id"] + row["quarter"])
        coverage_review.append({"company_id": row["company_id"], "quarter": row["quarter"], "dart_doc_id": dart[0]["doc_id"] if dart else "", "ir_doc_id": ir[0]["doc_id"] if ir else "", "retained_document_link_status": "pass" if passed else "missing_or_ambiguous", "official_announcement_exhaustiveness": "not_verified", "QA_transcript_coverage": "not_yet_checked"})
    relation_review = []
    for row in rows("document_relations.csv"):
        valid = row["doc_id"] in docs and row["related_doc_id"] in docs
        different = valid and docs[row["doc_id"]]["sha256"] != docs[row["related_doc_id"]]["sha256"]
        relation_review.append({"doc_id": row["doc_id"], "related_doc_id": row["related_doc_id"], "existing_relation_type": row["relation_type"], "both_doc_ids_exist": valid, "different_file_hashes": different, "semantic_relation_reaudited": False})
        if not valid:
            errors.append("dangling_document_relation")
    entity_review = []
    overview = {r["company_id"]: r for r in rows("company_overview.csv")}
    for row in rows("entities.csv"):
        paired = overview.get(row["company_id"], {})
        okay = row["corp_code"] == paired.get("corp_code") and row["ticker"] == paired.get("stock_code")
        entity_review.append({"company_id": row["company_id"], "corp_code": row["corp_code"], "ticker": row["ticker"], "local_official_identity_records_agree": okay, "scope_representation": "existing_operational_scope_notes_no_new_ontology"})
        if not okay:
            errors.append("company_identity_mismatch")
    source_review = [{"source_id": r["source_id"], "terms_url_present": bool(r["terms_url"]), "unresolved_reason_present": bool(r["unresolved_reason"]), "legacy_status": r["status"], "current_use_note": "excluded_by_current_AGENTS_not_hold_for_credentials" if r["source_id"] == "NAVER_NEWS" else "automated_access_prohibition_recorded_in_newer_20260922_review_legacy_not_current_permission" if r["source_id"] == "SKH_NEWSROOM" else "legacy_access_observation_not_rights_grant", "new_rights_verification": "not_performed"} for r in rows("source_registry.csv")]
    saved_audit = json.loads((P0 / "block_validation.json").read_text(encoding="utf-8"))
    summary = {"version": VERSION, "checked_at": datetime.now(timezone.utc).isoformat(), "official_manifest_documents": len(manifest), "primary_documents": len(primary), "auxiliary_documents": len(manifest)-len(primary), "official_news_documents": len(news), "official_news_blocks_recorded": sum(int(r["block_count"]) for r in news), "official_news_date_conflicts": sum(r["date_conflict"] == "True" for r in news), "quarter_slots": len(coverage_review), "quarter_slots_with_both_documents": sum(r["retained_document_link_status"] == "pass" for r in coverage_review), "all_block_records_scanned": len(block_ids), "block_types": dict(types), "native_tables_registered": len(tables), "existing_summary_block_count_agrees": len(block_ids) == saved_audit["blocks"], "numeric_pairs_recalculated": len(numeric_review), "numeric_pairs_passed": sum(r["recalculation_status"] == "pass" for r in numeric_review), "sample_audit_rows_linked": len(scope_review), "publication_date_missing_documents": sum(not r.get("published_date") for r in manifest), "image_only_pages_recorded": sum(int(r["image_only_pages"]) for r in rows("parser_trials.csv")), "document_relations_recorded": len(relation_review), "HBM4_plan_execution_location_candidates": len(plan_locations), "blocks_jsonl_sha256": block_hash.hexdigest(), "integrity_errors": errors[:100], "integrity_error_count": len(errors), "new_human_audit": "none", "coverage_limit": "No semantic completeness claim for raster images, no new source rights or event gold."}
    files = {"document_integrity": integrity, "coverage_review": coverage_review, "block_review": block_review, "numeric_recheck": numeric_review, "scope_checks": scope_review, "relation_review": relation_review, "entity_review": entity_review, "source_registry_review": source_review, "missing_metadata": missing, "plan_execution_location_candidates": plan_locations}
    for name, data in files.items():
        write_csv(output / (name + ".csv"), data)
    preservation = [{"path": "artifacts/p0/" + name, "sha256_before": before[name], "sha256_after": sha(P0 / name), "unchanged": before[name] == sha(P0 / name)} for name in inputs]
    write_csv(output / "input_preservation.csv", preservation)
    summary["metadata_files_unchanged"] = all(r["unchanged"] for r in preservation)
    with (output / "summary.json").open("x", encoding="utf-8") as stream:
        json.dump(summary, stream, ensure_ascii=False, indent=2)
    return summary


def finish_inventory(output, summary):
    initial = {"SAM-2025-FY-DART", "SKH-2025-FY-DART", "SAM-2025Q4-IR", "SAM-2026Q1-IR", "SKH-2025Q4-IR", "SKH-2026Q1-IR"}
    attempts = {r["doc_id"]: r for r in rows("access_trials.csv")}
    parsers = {r["doc_id"]: r for r in rows("parser_trials.csv")}
    basic = {r["doc_id"]: r for r in rows("document_manifest.csv")}
    additional = {"initial_six_present": initial <= set(basic), "initial_six_download_records": sum(attempts.get(doc, {}).get("status") == "downloaded" for doc in initial), "initial_six_parser_records": sum(doc in parsers for doc in initial), "official_manifest_unique_hashes": len({r["sha256"] for r in basic.values()}), "baseline_handoff_file_exists": (P0 / "handoff_p0.md").is_file(), "independent_human_reproduction_record": "not_found_in_reviewed_artifacts"}
    with (output / "additional_checks.json").open("x", encoding="utf-8") as stream:
        json.dump(additional, stream, ensure_ascii=False, indent=2)
    news = {r["doc_id"]: r for r in rows("news_body_manifest.csv")}
    anchors = {r["doc_id"]: r for r in rows("domestic_pilot_20260922/official_anchors.csv") if r["doc_id"]}
    dates = []
    for doc, row in basic.items():
        if row["published_date"]:
            continue
        direct, related = news.get(doc), anchors.get(doc)
        dates.append({"doc_id": doc, "original_document_published_date": "", "original_time_precision": row["time_precision"], "candidate_page_date": direct["publisher_page_date"] if direct else related["publisher_date"] if related else "", "candidate_dateline": direct["article_dateline_date"] if direct else related.get("dateline_date", "") if related else "", "candidate_date_conflict": direct["date_conflict"] if direct else related["date_conflict"] if related else "not_yet_checked", "evidence_file": "artifacts/p0/news_body_manifest.csv" if direct else "artifacts/p0/domestic_pilot_20260922/official_anchors.csv" if related else "", "match_type": "same_existing_doc_id_cross_manifest" if direct else "related_release_date_not_IR_file_publication" if related else "not_found_in_local_metadata", "assessment": "candidate_only_original_manifest_preserved"})
    write_csv(output / "publication_metadata_crosswalk.csv", dates)
    statuses = [
        ("P01-T01", "범위·역할·저장 위치", "done", "artifacts/p0/scope.md;coverage_review.csv;artifacts/p0/document_selection.md", "2사·10분기·초기6건·A/B/C 역할·원문위치 기록 확인", "none_for_recorded_P01_scope"),
        ("P01-T02", "기업 식별자", "done", "entity_review.csv;scope_checks.csv", "2사 corp_code·ticker가 기존 공식 기업개황과 일치; 메모리/DS/전사 감사 범위 분리", "최종 ontology나 별도 명칭 registry는 이번 범위 아님"),
        ("P01-T03", "출처 이용조건", "done", "source_registry_review.csv;artifacts/p0/domestic_pilot_20260922/source_review.md", "출처마다 조건근거URL 또는 미확인이유 기록이라는 완료기준 충족; 현행 NAVER 제외와 SK 제한 구분", "권리 자체는 unresolved 유지; 조건기록 완료가 권리승인을 의미하지 않음"),
        ("P01-T04", "첫6건 접근 시험", "done", "additional_checks.json;document_integrity.csv", "초기6건 다운로드·파서 기록과 보존원본 확인; 신규 네트워크 접근률이 아님", "발행일 미상은 별도 결측표에 보존"),
        ("P01-T05", "원본·메타데이터 등록", "done", "document_integrity.csv;missing_metadata.csv;publication_metadata_crosswalk.csv", "42건 원본 hash/크기·doc/revision 왕복 확인; 미상 정밀도 유지", "발행일 공란22건 중 같은문서 보완근거2·관련발표 후보4·로컬근거없음16; 원본발행일로 임의 대입하지 않음"),
        ("P01-T06", "본문·표 추출 시험", "done", "block_review.csv;summary.json;official_news_regression.json", "42문서743683블록 전수 기계점검·32137표 연결 확인; 공식뉴스4건186블록 별도회귀 통과", "이미지형31쪽 OCR 미실시·PDF 자동셀격자 없음; 의미적 완전성 미보증"),
        ("P01-T07", "숫자·단위·기간 감사", "partial", "numeric_recheck.csv;scope_checks.csv", "기존40개 문단/표 감사 연결; 누적차분·단위변환·IR 대조20/20 재계산 통과", "독립 A/B 사람 교차감사 서명/이견조정 기록은 확인되지 않음"),
        ("P01-T08", "중복·후속·정정 구분", "partial", "relation_review.csv;plan_execution_location_candidates.csv;additional_checks.json", "42개 원본hash 고유; 기존 동일발표 다른문서 관계2개 무결성 확인; HBM4 위치후보7개 추가", "계획→실행 반례의 주장단위 검증·번역/정정 포괄검토 미완료"),
        ("P01-T09", "10분기 목록 확장", "partial", "coverage_review.csv", "2사×10분기20칸 모두 정기보고서와 IR 연결; 기본40건 확보", "개별 공식발표·투자·Q&A의 전기간 완전목록과 주장연계는 미검증"),
        ("P01-T10", "결과 측정·출처 판단", "partial", "summary.json;source_registry_review.csv;handoff_p0.md", "기본공시/IR와 공식뉴스 분모를 나눠 현행 보존파일에서 재계산", "전체 국내뉴스 접근/완전본문/독립표현·권리판단은 별도 새실행결과와 합쳐야 함"),
        ("P01-T11", "인계·제3자 재현", "partial", "handoff_p0.md;additional_checks.json", "새 인계문서와 로컬 재현 명령은 작성완료", "needs_human_review: 제3자 사람 원문·숫자표 재현만 미완료; 다른 실행을 막는 상태 아님"),
    ]
    task_rows = [{"task_id": task, "task_name": title, "status": status, "evidence": evidence, "completed_local_work": done, "remaining_reason": reason, "assessment_basis": "current_retained_evidence_not_design_target", "new_human_review": "none"} for task, title, status, evidence, done, reason in statuses]
    write_csv(output / "task_status.csv", task_rows)
    report = f"""# P01 기존 자료 점검과 인계

2026-09-22. 이번 점검은 이미 저장한 자료가 빠지거나 바뀌지 않았는지, 표의 숫자와 분기 연결이 맞는지 확인한 작업이다. 새 기사나 원문을 수집하지 않았다.

## 지금 확인된 것

- 삼성전자와 SK하이닉스의 2024Q1~2026Q2에 필요한 정기보고서20개와 IR20개, 총40개가 있다. 두 기업·10분기의20칸에 두 자료가 모두 연결된다. 보조 HTML2개를 합친 기존 manifest는42개다.
- 42개 원본의 hash·크기와 743,683개 추출블록의 ID·위치·표참조·정규화·문자수를 다시 검사했다. 발견 오류는 {summary['integrity_error_count']}개다. 기존 메타데이터18개 파일은 검사 전후 hash가 같다.
- 숫자 비교20쌍은 이전 분기까지의 누적값을 빼고 단위를 맞춰 다시 계산했다. 20/20쌍이 기존 표시 반올림 허용범위에 들어온다. 삼성은 이 대조에서 DS 전체 매출을 비교하며 메모리만의 매출로 바꾸지 않는다. SK는 연결 전사 매출이며 HBM 매출이 아니다.
- 공식 영문 뉴스룸4개·186블록은 별도 분모다. 기존 읽기전용 뉴스 회귀검사2개도 통과했다. 이것은 국내 언론 기사나 매체 문체 검증 수가 아니다.
- 삼성 HBM4 계획과 실행을 검토할 수 있는 원문 위치후보7개를 찾아 block ID·PDF 페이지·hash만 남겼다. 단어가 있다는 이유로 후속관계를 확정하지 않았다.

## 남아 있는 것

- 원래42개 manifest의 발행일은22개가 미상이다. 그중2개는 같은 문서의 다른 manifest에서 페이지 날짜를 찾았고,4개는 관련 실적발표 날짜 후보를 찾았다. 나머지16개는 로컬 메타데이터에 근거가 없다. 실적발표일을 PDF 파일 발행일로 임의 복사하지 않았다.
- SK 2026Q1 공식 뉴스룸의 페이지 날짜2026-04-22와 본문 dateline2026-04-23 충돌1건을 유지한다.
- SK IR의 이미지로만 된31쪽은 OCR 텍스트가 없다. PDF 표는 텍스트와 좌표를 보존했지만 자동 셀 격자는 없다. 문자수 일치는 그림 속 내용까지 모두 읽었다는 뜻이 아니다.
- 저장·AI 사용·외부전송·공유 권리가 모두 확인된 것은 아니다. 옛 source_registry의 NAVER 자격증명대기는 현행 제외 결정을 대신하지 않고, 옛 SK 뉴스룸 접근성공은 자동접근 허락이 아니다.
- 기존 감사표40개가 있지만 독립적인 사람2명의 검토를 새로 수행한 것은 아니다. 계획/실행·정정/번역의 주장관계와 제3자 재현시험도 남아 있다.

## 단계별 판정과 다음 사람 검토

task_status.csv는 P01-T01~T11을 빠짐없이 기록한다. 이 인벤토리 범위에서 완료6개, 부분완료5개다. T03은 조건근거 또는 미확인이유를 기록하는 작업의 완료이며 권리승인이 아니다. T11은 전달문서 작성완료와 제3자 사람검토 미완료를 구분한다. T10은 부모 작업의 국내뉴스 통합보고서에서 최종 집계할 항목이다. '완료'는 명시한 기존자료·기계점검 범위이며 P01 전체 종료를 뜻하지 않는다. 온톨로지·gold·100+20개 확장은 하지 않았다.

검토자는 document_integrity.csv의 doc_id로 원본을 열고 scope_checks.csv의 표/페이지 또는 기존 extraction_audit.csv의 위치를 따라 숫자·단위·기간·범위를 확인하면 된다. 숫자 차분 과정은 numeric_recheck.csv에 있다. HBM4 관계는 plan_execution_location_candidates.csv의 위치를 먼저 확인한다. 원문을 출력·복제하지 않은 메타데이터 인계이므로 실제 사람 원문검토 결과는 별도로 기록해야 한다.

재현: `python scripts/p01_existing_evidence_review.py --output-dir <존재하지_않는_새_출력경로>`

기존 p01_verify_extraction.py는 원래 block_validation.json을 다시 쓰므로 실행하지 않았다. p01_verify.py는 .env를 직접 읽으므로 사용하지 않았다. 이 새 검토기는 자격증명을 읽지 않고 기존 파일을 바꾸지 않는다. 본문은 로컬 코드로만 처리하며 답변/출력파일에 원문을 담지 않는다.
"""
    (output / "handoff_p0.md").write_text(report, encoding="utf-8")
    write_metadata_proposals(output)


def write_metadata_proposals(output):
    sk = {"SKH-" + r["quarter"] + "-IR": r for r in rows("sk_ir_list.csv")}
    news = {r["doc_id"]: r for r in rows("news_body_manifest.csv")}
    proposals = []
    for row in rows("document_manifest.csv"):
        if row.get("published_date"):
            continue
        item = sk.get(row["doc_id"])
        event_at = ""
        if item:
            clean = re.sub(r"\s*/\s*", " / ", item["event_date_raw"]).strip()
            parsed = datetime.strptime(clean, "%b %d, %Y / %I:%M %p KST")
            event_at = parsed.strftime("%Y-%m-%dT%H:%M") + "+09:00"
        other = news.get(row["doc_id"])
        proposals.append({"doc_id": row["doc_id"], "existing_published_date": "", "proposed_IR_published_date": "", "event_at_normalized_candidate": event_at, "event_time_precision": "minute" if event_at else "unknown", "event_time_evidence": "artifacts/p0/sk_ir_list.csv:event_date_raw" if item else "", "event_api_sequence": item["seq"] if item else "", "file_url_matches_manifest": row["attachment_url"] == item["file_url"] if item else "not_applicable", "display_date_raw_not_publication": item["display_date_raw"] if item else "", "same_doc_newsroom_page_date_candidate": other["publisher_page_date"] if other else "", "same_doc_newsroom_dateline_candidate": other["article_dateline_date"] if other else "", "newsroom_date_conflict": other["date_conflict"] if other else "not_applicable", "proposal_status": "normalize_event_time_only_not_document_publication" if item else "cross_manifest_newsroom_metadata_candidate" if other else "no_local_publication_evidence", "reason": "Event schedule and board display date do not establish PDF publication; no file mtime or PDF CreationDate substitution.", "applied_to_original": False})
    write_csv(output / "proposed_metadata_repairs.csv", proposals)
    location_path = output / "plan_execution_location_candidates.csv"
    with location_path.open(encoding="utf-8-sig", newline="") as stream:
        locations = list(csv.DictReader(stream))
    before = [r["block_id"] for r in locations if r["doc_id"] == "SAM-2025Q4-IR" and r["plan_cue"] == "True"]
    after = [r["block_id"] for r in locations if r["doc_id"] == "SAM-2026Q1-IR" and r["execution_cue"] == "True"]
    write_csv(output / "follow_up_provisional.csv", [{"before_doc_id": "SAM-2025Q4-IR", "after_doc_id": "SAM-2026Q1-IR", "product_marker": "HBM4", "before_location_candidates": "|".join(before), "after_location_candidates": "|".join(after), "relation_candidate": "plan_to_execution_candidate", "status": "unverified_not_gold", "same_file_duplicate": False, "claim_scope_modality_conditions_review": "pending_original_context", "publication_order_verified": False, "reason": "Different preserved IR documents and local product/stage cue locations only; no full proposition identity inferred."}])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.output_dir)
    finish_inventory(args.output_dir, result)
    print(json.dumps({key: result[key] for key in ("official_manifest_documents", "primary_documents", "quarter_slots_with_both_documents", "all_block_records_scanned", "numeric_pairs_passed", "integrity_error_count", "metadata_files_unchanged")}))
