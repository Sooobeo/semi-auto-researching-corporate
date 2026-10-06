# EventClaim 양식 0.1.0

기준 2026-10-05 · 구조 규약: structure/DATA_CONTRACTS.md v1.2 · 팀 고정 전 초안.

실행 계약은 [event_schema_v0.1.json](event_schema_v0.1.json)이다. top-level record_kind에 따라 event_claim과 business_relation을 구분한다. 식별·근거·계보는 공통이고 raw / normalized / assessment / derived를 서로 다른 속성으로 저장한다. JSON Schema는 자료형·필수항목·허용값·일부 조건을 검사하며 원문 정확성·이용권·ID 실재·비교 타당성을 자동 증명하지 않는다. 의미 검사기는 별도이며 경고를 완료로 바꾸지 않는다.

| 묶음 | 필드·타입 | 필수/미상 처리·반례 |
| --- | --- | --- |
| 식별 | claim_id, claim_revision_id, event_id, event_family_id: string | 안정 ID와 수정본 분리; 같은 제목만으로 family 합치지 않음 |
| 계보 | schema_version, registry_version, model_version, run_id, supersedes_record_id | 모델 미사용은 model_version=null; run·작성 주체 기록 |
| 출처 | provenance.doc_id/revision_id/source_id/source_url/final_url/rights_basis_ref/evidence | 실제 record는 원본 manifest·조건 registry와 연결; 미확인 URL로 허가를 대신하지 않음 |
| raw | claim_text, action_raw, metric_raw, value_raw, unit_raw, line_item_raw, speaker_raw, time_raw | 정확 원문 문자열 또는 null+field_missing_reasons; 제한 원문을 복제하지 않음 |
| normalized 대상 | company_id, scope_id, product_id, actor, entity_refs, relation_refs | 회사/scope 미상은 null+명시 사유; 회사 ID를 제품 ID로 쓰지 않음 |
| 사건 | event_type, modality, negation, conditions | 실제/계획/전망/가능/부인/미상 구별; 개발을 판매로 바꾸지 않음 |
| 수치 | numeric_value, lower, upper: Decimal 문자열/null; value_kind; direction | 0은 "0"; null은 사유 필수. range에는 두 endpoint 필요. comma·NaN 금지 |
| 단위 | canonical_unit, currency, scale, denominator | %증가율·비중·마진 구별; currency는 ISO 3자리 또는 null; scale 문자열 |
| 회계 | accounting_basis, adjustment_definition, fiscal_year/quarter, period_basis, consolidation | GAAP/non-GAAP/unknown/not_applicable; fiscal label을 calendar로 자동 변환하지 않음 |
| 시간 | temporal.published_at/date, timezone/offset/time_precision, reference_period, effective_period, observed_at, available_at/evidence | 날짜만 있으면 published_at=null. observed를 publication으로 복제하지 않음 |
| 재무 문맥 | financial_context.statement_type, balance_or_flow, period_duration, note_refs, concept_ids, adjustment_component_refs | 잔액 시점·기간 흐름, 분기·누적 구별; 비재무는 not_applicable |
| 비교 | comparison_basis, denominator, prior_claim_id, prior_state_status | prior 미발견과 반복 구별; 기존계획 +20%만으로 절대값 생성 금지 |
| 상태 | extraction_status, evidence_status, field_missing_reasons | partial/complete/unresolved. complete는 원문을 충분히 옮겼다는 잠정 판정이며 gold가 아님 |
| assessment | 작성 주체·질문·응답·이유·evidence_refs·review_readiness | assessment=null을 허용하므로 중요성 판단 미실시여도 fact 저장 가능 |
| derived | calculation_id, input_refs, formula/version, output/unit, missing_inputs, calculation_status | insufficient_inputs일 때 output=null; source fact 값과 계산 결과를 분리 |

Decimal 문자열 사용은 DATA_CONTRACTS §1.7 및 예시의 정밀 계산 표현을 따른다. 숫자 타입으로 강제 변환하지 않고 Decimal로 읽는다. 원문 금액과 scale, 정규화값을 함께 유지한다. accounting_basis의 unknown을 null이나 GAAP 기본값으로 바꾸지 않는다.

evidence는 block_id·doc/revision·위치·offset 기준·검증 상태를 가진다. Unicode code point, 0-based, [start,end)만 허용한다. 실제 source span이 없으면 start/end=null과 location_status=unlocated를 기록한다. 위치 미검증은 gold/정밀 숫자 근거에 사용할 수 없다. 표 셀은 table_id, row_index, col_index, header_refs를 같이 보존한다.

누락 코드는 not_disclosed / not_found / ambiguous / not_applicable / parse_failed / incompatible / not_yet_checked다. 확실히 공개하지 않은 것과 조사하지 않은 것을 구별한다. 해당 사실에 필요한 source 필드의 null은 field_missing_reasons의 경로로 이유를 연결한다.

원본 claim을 수정할 때 claim_id는 유지하고 claim_revision_id와 supersedes_record_id를 새로 둔다. 출처 자체의 새 정정 발행은 새 doc_id로 연결한다. 영어 사실·한국어 설명은 raw.claim_text와 assessment 설명으로 나누며 한국어 offset을 영어 근거에 사용하지 않는다.
