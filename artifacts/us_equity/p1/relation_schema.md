# 사업 관계 주장 양식 0.1.0

2026-10-05 · event_schema_v0.1.json의 record_kind=business_relation으로 검증한다.

관계는 관계의 존재를 주장한 원문과 방향·양끝 개체·역할·scope·시점·modality를 기록한다. company_id만으로 모든 관계 당사자를 표현하지 않는다. registry에 없는 대상은 object_entity_id=null과 not_disclosed/not_yet_checked 사유를 두며 이름을 추측하지 않는다. 미연결 이름은 raw.speaker_raw/claim_text와 별도 후보 기록으로 보존한다.

| 후보 relation_type | 방향·역할 | 채택 조건·반례 |
| --- | --- | --- |
| supplies_to | supplier→customer | 공급 동작·대상·제품 scope 근거 필요; 샘플 평가 계획은 actual 공급으로 바꾸지 않음 |
| develops | company→product/service | 실제 개발/계획 단계 기록; 개발과 양산/판매 구별 |
| offers | company→product/service | 제공·판매 원문과 적용 시점 필요; 출시 예고는 plan/forecast 유지 |
| partners_with | 명시 주체→명시 상대; 대칭 판단은 registry 규칙 | 협업 발표의 목적·scope·조건 필요; 인명 동시 등장만으로 생성 금지 |
| competes_with | 명시 주체→명시 경쟁 상대·시장 scope | 경쟁 주장·화자·시점 필요; 같은 섹터 소속만으로 확정 금지 |
| belongs_to_industry | company→industry | 산업 정의·근거·유효기간 필요; 공통 산업 변화가 인과관계를 뜻하지 않음 |
| unknown | 미확정 | relation_type 미확정 이유와 원문 보존; 다른 후보 중 억지 선택 금지 |

후보만 정의했고 실제 문서에서 각 타입이 발생했다고 주장하지 않는다. relation_catalog는 후속 P03에서 필요성과 실제 범위를 보고 선정한다.

필수 연결은 relation_id / relation_revision_id / claim_id / event_id / event_family_id, subject_entity_id / object_entity_id / subject_role / object_role / direction / scope_id, product_service_ids, valid_from/to, temporal.effective_period/publication/observed/available, modality/negation/conditions, evidence_status/extraction_status/field_missing_reasons다. speaker는 raw.speaker_raw와 normalized.speaker로 구별한다. registry_version·run_id·schema_version은 공통 계보에서 상속한다.

원문 관계 사실은 normalized에 있고 실적 영향 판단은 assessment에 있으며 규모 계산은 derived에 둔다. 계약 축소라도 금액·기준 기간·대상 매출이 미공개이면 derived.calculation_status=insufficient_inputs, output=null이다. 관계 변경은 이전 claim/관계 ID와 supersedes를 연결하고 이전 기록을 덮어쓰지 않는다.
