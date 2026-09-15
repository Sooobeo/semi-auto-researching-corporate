# 공통 데이터 규약 및 산출물 계약

기준일: 2026-09-15 / 제안 버전 v1.0. 각 Phase가 독립적으로 다른 필드를 만들지 않도록 사용하는 공통 설계입니다. 실제 스키마·코드는 해당 Phase에서 구현하고 사례 검증 후 버전을 고정합니다.

## 1. 기록 원칙

1. 원문(raw), 구조화(normalized), 사람의 판단(assessment), 계산 결과(derived)를 별도 층으로 둡니다.
2. 사실 레코드에는 근거가 필요합니다. 회사가 발표한 사실과 외부 검증된 사실은 다르므로 evidence_status를 보존합니다.
3. 모든 결과는 입력 ID·도구/모델·스키마·registry·설정·코드 버전으로 연결합니다.
4. 원문·주장·정정·사람 수정은 덮어쓰지 않고 새 revision을 추가합니다.
5. 값 0과 미상(null), 해당 없음, 미공개, 추출 실패는 다릅니다. numeric_value는 숫자 또는 null이고 missing_reason으로 사유를 구별합니다.
6. ID는 안정적인 문자열입니다. 회사코드·문서번호를 임의로 추측하지 않으며 공식 확인 값과 내부 ID를 분리합니다.
7. CSV는 UTF-8, JSONL은 줄마다 유효한 JSON 객체로 저장합니다. 숫자 원표현은 문자열, 정밀 계산용 값은 Decimal로 읽을 문자열을 권장합니다. CSV의 빈칸 의미는 해당 schema에서 정합니다.

## 2. 회사·사업 범위

| 필드 | 형식·의미 | 필수·검증 |
| --- | --- | --- |
| company_id | 내부 안정 ID | 필수 |
| legal_name | 공식 회사명 | 공식 출처 연결 |
| ticker / corp_code | 거래소 종목코드 / DART 고유번호 | 미확인 null; 다른 코드로 대체 금지 |
| scope_id | 전사/사업부/제품군 구분 | 사실마다 필수; 미상은 명시 |
| scope_name / parent_scope_id | 범위 이름과 상위 범위 | 메모리·DS·삼성 전체를 분리 |
| consolidation | consolidated / separate / segment / unknown | 비교 조건에 사용 |
| alias / language / evidence | 이름 변형과 근거 | alias 적용범위·유효기간 기록 |

삼성 메모리 매출과 DS 영업이익은 동일 scope가 아닙니다. SK하이닉스 연결 수치를 특정 제품군 수치로 바꾸지 않습니다. 리노공업 전사 수치에는 다른 사업이 포함될 수 있으므로 소켓/핀/의료기기 범위를 구분합니다.

## 3. 출처와 문서

### source_registry.csv

`source_id, provider, source_type, landing_url, terms_url, checked_at, authentication, manual_read, automated_access, storage_policy, sharing_policy, redistribution_policy, rate_limit_evidence, status, unresolved_reason`

저장/공유/재배포 가능은 각각 확인합니다. API 호출 제한 수치는 실행일의 공식 가이드에서 확인한 값만 넣습니다. 원문 공개와 재배포 허용은 동일하지 않습니다.

### document_manifest.csv

| 필드 | 뜻 | 검증 |
| --- | --- | --- |
| doc_id / revision_id | 문서·수집본의 안정 ID | 필수, revision 중복 금지 |
| source_id / source_url / attachment_url | 원출처·첨부 | 상세 URL과 홈페이지 분리 |
| title / company_ids / language | 문서 메타데이터 | 복수 기업 가능 |
| published_at / published_date | 정확 시각 / 날짜 | 정확 시각 미상은 null |
| time_precision / timezone | second/minute/date/unknown, 시간대 | 출처 근거와 함께 |
| observed_at | 시스템이 실제 관측한 시각 | published_at 대체 금지 |
| reference_period_start/end | 자료의 실적 대상 기간 | 발표일과 구별 |
| format / byte_size / sha256 | 원본 형식·크기·hash | 미저장·미측정 이유 |
| storage_uri / storage_policy | 보관 위치·범위 | 권한·원문 조건 준수 |
| source_revision_of / relation_type | 정정·번역·재보도·후속 | 대상 문서 존재 확인 |
| parse_status / parser_version | 추출 상태·방법 | 수동·자동·OCR 분리 |
| split_exposure | train/dev/test/adaptation/practice/unassigned | 사용 이력 보존 |

문서 전체가 한 기간으로 표현되지 않으면 reference periods 배열을 별도 필드/연결 테이블로 둡니다. 개별 claim의 기간이 최종 비교 기준입니다.

### blocks.jsonl

`block_id, doc_id, revision_id, block_type, page_number, section_path, raw_text, normalized_text, offset_mapping, table_id, row_index, col_index, header_refs, extraction_method, extraction_version`

페이지 번호는 문서 인쇄 번호와 파일 페이지 index를 구분합니다. 표는 셀 값뿐 아니라 단위·기간·사업범위 머리글을 header_refs로 연결합니다. offset 기준은 원문 block의 Unicode code point인지 UTF-16인지 명시하고 저장·평가 도구 간 통일합니다.

## 4. 사건·주장

### EventClaim 권장 필드

| 묶음 | 필드 | 처리 규칙 |
| --- | --- | --- |
| 식별 | event_id, event_family_id, claim_id, doc_id, revision_id | 문서·사건·개별 주장 분리 |
| 대상 | company_id, scope_id, product_id, actor | 근거 없는 기업 연결 금지 |
| 사건 | event_type, action_raw, modality, negation, conditions | 개발/양산/출하/판매 원문 동작 보존 |
| 지표 | metric_raw, metric_id, registry_version | 미확정 mapping은 null과 후보 목록 |
| 값 | value_raw, numeric_value, value_kind, direction, lower, upper | point/range/change/rate/share/qualitative 구분 |
| 단위 | unit_raw, canonical_unit, currency, scale | 원단위와 변환값 모두 유지 |
| 비교 | comparison_basis, denominator, prior_claim_id | YoY/QoQ/기존계획·비중 분모 구분 |
| 기간 | published_at/date, reference_period, effective_period, observed_at | 네 시점의 역할 분리 |
| 근거 | evidence[] | block_id, span 또는 표 위치, 허용된 인용 |
| 상태 | extraction_status, missing_reason, evidence_status | 발표 주장/검토/확인 수준 |
| 계보 | schema_version, model_version, run_id | 재현성 필수 |

modality 후보: actual_reported, plan, forecast, possibility, denial, unknown. 실제 회사 발표를 추출한 actual_reported가 외부 검증을 의미하지 않습니다.

missing_reason 후보: not_disclosed, not_found, ambiguous, not_applicable, parse_failed, incompatible, not_yet_checked. source가 공개하지 않은 것과 우리가 찾지 못한 것을 구분합니다.

### 가상 JSON 예시

다음은 형식 설명용 합성 사례입니다. 실제 삼성·SK 수치나 연구 결과가 아닙니다.

```json
{
  "event_id": "EXAMPLE-E001",
  "claim_id": "EXAMPLE-C001",
  "doc_id": "EXAMPLE-D001",
  "company_id": "EXAMPLE-CO",
  "scope_id": "EXAMPLE-MEMORY",
  "event_type": "capacity_plan_revision",
  "metric_raw": "생산능력",
  "metric_id": "example.capacity",
  "value_raw": "기존 계획 대비 20% 확대할 계획",
  "numeric_value": "20",
  "value_kind": "relative_change",
  "canonical_unit": "percent",
  "comparison_basis": "previous_plan",
  "modality": "plan",
  "prior_claim_id": null,
  "absolute_value": null,
  "missing_reason": "not_found",
  "evidence": [{"block_id": "EXAMPLE-B01", "location": "synthetic sentence"}],
  "schema_version": "example-1"
}
```

이 예시만으로 새 생산능력이나 매출을 계산할 수 없습니다. prior 값·단위·기간·가정이 필요합니다.

## 5. 지표 등록부·비교 조건

### metric_catalog.csv

`metric_id, canonical_name, definition, metric_kind, level, scope_constraints, product_constraints, canonical_unit, denominator_definition, period_type, occurrence_docs, occurrence_families, company_count, company_denominator, period_count, forecast_linkage_evidence, stability_notes, selection_status, definition_version`

### alias_registry.csv

`alias_id, metric_id, alias_raw, language, scope_constraints, unit_constraints, valid_from, valid_to, evidence_doc_id, evidence_location, mapping_status, reviewer`

### unit_rules.csv

`rule_id, input_unit, output_unit, multiplier, currency_condition, period_condition, precision, rounding, required_inputs, failure_reason, version`

### comparability record

`new_claim_id, prior_claim_id, company_match, scope_match, product_match, definition_match, period_match, unit_compatible, currency_compatible, value_kind_match, modality_relation, decision, reasons, rule_version`

decision: comparable / conditional / not_comparable / unknown. conditional에는 부족한 입력과 허용 가능한 계산을 명시합니다. 동일 % 기호만으로 비율·비중·증가율을 비교하지 않습니다.

## 6. Annotation·split

### annotation record

`annotation_id, annotator_id, claim_id, guide_version, registry_version, facts, assessments, evidence_refs, uncertainty_reason, started_at, completed_at, status`

### adjudication record

`adjudication_id, input_annotation_ids, adjudicator_id, field, previous_values, final_value, unresolved_reason, evidence_refs, rationale, changed_guide_version, created_at`

### split_manifest.csv

`item_id, item_type, doc_id, event_family_id, company_id, published_date, split, split_version, exposure_status, exclusion_reason, boundary_policy`

- split은 train/dev/calibration/test/embargo/adaptation/practice/excluded 등을 명시합니다.
- alias·규칙·threshold를 만드는 데 쓴 자료는 untouched test로 부르지 않습니다.
- 테스트 label을 학습·prompt 예시·active learning에 사용하지 않습니다.
- 시점 이전에 공개된 원문을 검색 인덱스에 넣는 것은 label 노출과 구별하되, cutoff·observed 정책을 지킵니다.
- company holdout과 time holdout을 구별하고, 2개 기업의 제한을 보고합니다.

## 7. 검색·변화·계산

### prior-state / retrieval

`query_event_id, cutoff, cutoff_mode, corpus_version, candidate_claim_id, retrieval_method, score, rank, compatibility, selection_reason, source_publication_evidence`

### change record

`change_id, new_claim_id, prior_claim_id, change_types, old_value, new_value, delta, relative_delta, unit, comparison_basis, formula_id, comparability, uncertainty, evidence_refs, available_at, rule_version`

prior_not_found와 repeated는 다릅니다. 정답이 없는 검색 결과에 강제로 prior를 붙이지 않습니다.

### scenario run

`scenario_id, event_id, formula_id, formula_version, input_values, input_units, input_source_ids, assumption_flags, scenario_name, currency_policy, rounding_policy, missing_inputs, output, output_unit, calculation_status, run_id`

status: computed / insufficient_inputs / incompatible_inputs / invalid_formula / error. computed가 아니면 output은 null이며 이유를 표시합니다. low/base/high는 가정 집합 이름이고 통계적 신뢰구간이 아닙니다.

## 8. Review Card·feedback

### card record

`card_id, card_version, event_id, company_scope, new_fact, prior_fact, change_summary, evidence_refs, materiality_assessment, uncertainty_fields, review_questions, scenario_refs, pipeline_status, run_id`

### feedback record

`feedback_id, idempotency_key, actor_id, card_id, card_version, action, field, before, after, evidence_refs, rationale, created_at, review_status, training_eligibility`

action 후보: confirm, correct_fact, irrelevant, investigate, update_assumption. UI session state와 영속 store를 구분합니다. 한 사람의 수정은 candidate로 들어가며 자동 gold 승격이나 test 학습을 허용하지 않습니다.

## 9. run manifest

`run_id, started_at, completed_at, input_manifest_hash, code_revision, dirty_diff_hash, dependency_lock_hash, model_id, model_revision, tokenizer_revision, schema_version, registry_version, policy_version, prompt_hash, seeds, hardware, cutoff_mode, budget, measured_usage, stage_statuses`

구현 전에는 이 필드가 ‘채울 설계’입니다. 모델·명령·단가·재현 결과를 존재하는 것처럼 미리 채우지 않습니다. API 키·토큰은 manifest에 포함하지 않습니다.

## 10. 공통 검증 항목

- 고유키 중복·외래키 단절·없는 원문 위치.
- 숫자0/null·missing_reason 일관성.
- offset의 정규화 전후 왕복과 표 머리글 연결.
- published/reference/effective/observed 시점 혼동.
- train/test family·번역·정정 중복, adaptation 재사용.
- raw·normalized·derived 값과 변환 provenance.
- 정책·모델·registry 버전 변경 시 구결과 덮어쓰기.
- 실패·미측정 항목을0 또는 정상 성공으로 취급하는지.

## 11. 평가 지표의 정확한 분모

| 지표 | 정의와 필수 조건 |
| --- | --- |
| 문서 접근률 | 본문 읽기 성공 고유 문서 / 실제 접근 시도 고유 문서 |
| 자동 추출률 | 정한 usable 기준 충족 문서 / 해당 방법 추출 시도 문서 |
| Precision/Recall/F1 | TP/FP/FN 정의·positive label·micro/macro·undefined 처리 명시 |
| 숫자·단위·기간 EM | 각각의 일치율과 전체 묶음 일치율을 별도 보고 |
| Span F1 | exact boundary와 relaxed overlap을 다른 지표로 보고 |
| Metric top-k | 정답 ID가 후보 k 안에 있는 매핑 건 / 평가 가능한 매핑 건; unknown 정책 별도 |
| Retrieval Recall@k | qrels의 적합 근거가 topk에 포함된 비율, query별 평균 방식 명시 |
| Important Recall@k | universe의 중요 사건 중 검토 상위k에 포함된 수 / universe 중요 사건 수 |
| NDCG@k | relevance gain·query group·tie·정답0 그룹 정책 사전 고정 |
| AP / PR-AUC | average precision과 사다리꼴 PR-AUC를 이름·계산법으로 구분 |
| 검토율 | 실제 검토한 고유 사건 / 전체 대상 고유 사건 |
| 수정률 | 수정된 카드 또는 필드 / 실제 검토한 카드 또는 필드; 단위 혼합 금지 |
| 비용/1000문서 | 실제 run 비용 / 입력 문서 수 ×1000; 관측수·환산임을 함께 표시 |
| 처리시간 | 초기 구축·cold start·warm 처리·API 대기·재시도 분리 |
| 일치도 | 조정 전 독립 라벨 기준; 척도·결측·표본수·유형별 결과 함께 보고 |

분모0은 NA/undefined 정책에 따라 보고하고 평가에서 제외한 건수를 함께 공개합니다. 신뢰구간은 문장 독립 가정보다 사건 family·날짜 그룹 의존성을 고려합니다. 이 통계 선택의 최종 근거는 P3/P5/P8에 남깁니다.

