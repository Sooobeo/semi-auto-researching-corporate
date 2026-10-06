# P04 주석 가이드 v1.2

2026-10-06 · 현재 표본: Microsoft 공식 실적 발표의 최소 재무 사실·보고 사업부 관계. 버전 식별자 `us-p3-guide-1.2`. 최종 hash는 stage 2 기준본 manifest에 고정한다. 이 가이드는 agent 개발 주석에 적용하며 인간 pilot 완료를 뜻하지 않는다.

## 범위와 입력

`source_packets.jsonl`의 33 숫자 항목과 6 보고 관계 항목을 사용한다. 원문에서 확인한 숫자 셀·기간/연도/단위 머리글·표준 재무 라벨·사업부 이름·위치만 전달한다. 전체 문서나 영문 prose는 AI에 입력하지 않는다. 원문 HTML은 권리별 private 위치에 보관한다. 신규 FY2026 Q1 예약 문서의 내용은 이 가이드 개발·주석 작업에서 열지 않는다.

주석 단위는 item_id로 식별하는 숫자 claim 또는 reporting_relation이다. 39 작업 항목의 source numeric claim_id는 33개이며 관계 6개는 그 중 6개를 참조한다. 발표 event와 family는 각각 2개이다. 현재 실적 발표 안에서 함께 공표된 주장들을 묶은 anchor이며 일반적으로 문서 하나를 사건 하나로 강제하지 않는다.

작성자는 `annotation_reference.json`의 등록 ID·별칭과 이 가이드, 해당 source packet 및 `evidence_index.jsonl`의 위치 참조만 사용한다. 다른 작성자 답, `contract_records.jsonl`의 변환 정답, P03 계산 결과를 보지 않는다. 어떤 자료를 보았는지 exposure_log에 기록한다. agent A/B는 독립된 작업 맥락과 파일에서 작성하지만 동일 자료·가이드를 공유한다. 두 agent의 비교는 인간 독립 주석이나 시스템 추출 정확도의 증거가 아니다.

## 사실 작성

1. packet item_id/doc_id/revision/hash/event/family와 근거 위치를 유지한다. source_claim_id를 재생성하지 않는다.
2. 원문 value_cell의 숫자 원표현을 보존하고 Decimal 문자열로 처리한다. 통화·단위가 같은 셀만 정규화한다. million은 scale=1000000이다. `numeric_value`는 원 배율의 값이고 `numeric_value_base_units`는 값×scale이다.
3. 괄호로 표시된 음수는 raw에 보존한다. Additions to property and equipment는 `positive_cash_capex`의 양의 현금 지출로 표현하며 별도 sign_policy를 기록한다. 비현금 투자·finance lease·전체 투자현금흐름으로 확대하지 않는다.
4. 회사 전체, 각 보고 사업부 scope를 분리한다. 같은 revenue라도 entity/scope/definition_version을 같이 기록한다. 회사·사업부 이름은 annotation_reference의 검증된 ID를 사용한다.
5. FY2024 발표의 사업부 표시와 FY2025 발표의 표시를 별도 정의로 보존한다. FY2025 문서에 있는 FY2024 비교열은 FY2025 공개시점의 주장이다. 같은 이름·같은 과거 기간이라는 이유로 이전 표시와 차이를 계산하거나 원인을 추측하지 않는다.
6. Three Months/Twelve Months와 해당 연도 머리글로 Q4/연간을 구분한다. Microsoft의 이 표본은 6월30일 결산이며 Q4=4월1일~6월30일, 연간=전년7월1일~해당년6월30일이다. 시작일 계산은 header-derived임을 기록한다. 잔액은 as_of_date가 있는 instant이고 flow 기간과 섞지 않는다. 연간 366/365일을 보존한다.
7. 발표 날짜만 확인된 자료는 published_at=null, time_precision=date다. observed_at을 발표 시각으로 대체하지 않는다. 발행시각·자료 대상기간·실제 적용기간은 구분한다.
8. actual_reported는 회사가 발표한 값이다. evidence_status에 unaudited/company_reported를 보존한다. 외부 검증·인간 gold로 바꾸지 않는다.
9. `reports_segment` 방향은 reporting_company → reported_segment다. 이 관계는 회사가 표에서 해당 사업부를 보고했다는 주장이다. 고객·공급·제품 관계나 실적 영향으로 해석하지 않는다. reference_period는 표의 보고기간이며 valid_from/to와 실제 effective_period는 미확인이다. P03의 source effective_period 원값은 이력에 보존한다.
10. 관계 근거의 scope·화자·부정·조건·modality를 보존한다. 이 좁은 표본에서 부정/조건 텍스트는 별도로 확보되지 않았다. 관계가 전체 기업 역사에서 언제 시작됐는지 만들지 않는다.

## 근거와 시점

숫자 span은 원래 DOM cell 텍스트의 Unicode code point 0-based [start,end)다. raw cell은 공백 정규화 전 문자열을 사용한다. 원문 slice가 value_raw와 일치하는지 검사한다. 표 셀·행/열·기간/연도/단위 헤더의 XPath와 문서 revision을 함께 보존한다. 재조회하지 않은 위치는 검증됐다고 표시하지 않는다.

전사 consolidation 보완 근거는 FY2025 annual reference이고 발행일 미상·2026-10-05 관측이다. 현재 시점의 후향적 변환에는 이 dependency를 표시할 수 있지만 2024/2025 당시 화면의 source fact로 소급하지 않는다. 주석 packet의 historical assessment에는 이 보완 문서 내용이나 후속 자료를 제공하지 않는다. 해당 scope 판단은 당시 근거 충분성을 별도로 평가한다.

현재 두 release의 비교열 연결은 representation_overlap이다. 새 정정이라고 확인하지 않은 자료에 correction_of를 붙이지 않는다. 새로운 독립 발표는 별도 family로 보존하고 관련 사건/정정의 leakage edge로 분할 위험을 검토한다.

## assessment 작성

facts와 assessment는 별도 파일/필드로 저장한다. 검토 시점은 각 원 발표 날짜의 date precision이며 같은 날짜의 정확한 순서는 미상이다. 다른 평가자 답·사후 주가·후속 실적·정정은 보여주지 않는다. 가이드 자체에 후속 발표의 비교열과 후향 scope 보완 이력이 있으므로 root 및 A/B 모두 `retrospective_cutoff_simulation`과 `guide_contains_post_cutoff_context`를 기록한다. 후속 원문을 packet에서 제외해도 주석자의 사후 지식을 제거했다거나 미노출 as-of 평가를 했다고 주장하지 않는다.

사실을 구조화하는 것만으로 실제 중요성 응답을 만들지 않는다. MQ01~MQ05는 기존 사업 가정·전망·재무문맥이 필요하므로 현재 최소 숫자 packet만으로 근거가 부족하면 unknown/not_assessed를 사용한다. MQ06은 근거 위치·기간·scope의 충분성, MQ07은 prior와의 비교 가능성, MQ08은 검토 행동을 묻는다. prior를 제공하지 않은 이 독립 주석 작업에서 MQ07은 unknown이고 prior_not_provided를 남긴다. 판단 불가를 낮은 중요성/no로 바꾸지 않는다.

`review_readiness`는 원문 사실 검토용 목적과 과거 비교용 목적을 구분한다. 이번 assessment 목적은 historical_comparison이므로 prior 미제공/정의·scope 불확실성을 이유로 needs_review로 남긴다. supported는 외부 사실 검증의 의미가 아니다. 명시적 비교 쌍·조건을 실제 확인하기 전 not_comparable을 단정하지 않는다.

## 독립 원본·연습·조정

agent A/B의 annotator_kind는 agent이며 실제 agent 실행과 작성 방법을 기록한다. 스크립트로 전수 작성했다면 agent_authored_deterministic_annotation이라고 밝힌다. created_at/실행 시간은 실제 실행값이며 인간 소요시간으로 세지 않는다. AI 결과를 복제해 인간 주석자 이름을 붙이지 않는다.

연습은 Q4/연간/잔액/현금 capex/사업부 현재값·과거 비교열/관계를 포함한 고정 표본으로 한다. 연습의 불일치를 검토해 필요하면 가이드 새 버전을 기록한 뒤 본작업을 실행한다. 연습과 본작업 양쪽에 나타난 항목은 노출 이력을 유지하며 독립 표본 두 건으로 세지 않는다. 현재 전체 집합은 adaptation이며 test로 사용할 수 없다.

원본 annotation은 append-only인 개별 파일로 보존한다. 조정 전 값으로 일치도를 계산한다. numeric/단위/기간/company/scope의 exact match와 전체 tuple, span exact/overlap을 각각 보고한다. 점수 분모에서 제외한 unknown/NA와 undefined는 별도 보고한다. 사람 일치도는 인간 원본이 없으면 null이다. agent와 자동 변환의 일치율은 구현 일관성만 확인한다.

조정은 input_annotation_ids·필드·원값·선택값·근거·이유·조정자 종류를 기록한다. 해결할 수 없는 필드는 unresolved이다. agent 검토 결과는 `reviewed_agent_events/relations`로 저장한다. 정식 `gold_events/relations`에는 실제 독립 인간 원본과 조정 근거가 없는 행을 넣지 않는다.

추가 보존 위치: annotation provenance에는 `doc_sha256`, `source_record_ref`, `offset_basis`, `availability_dependency_refs`, 원 P03 relation의 `source_effective_period` 이력을 연결한다. 숫자 facts에는 `accounting_basis`, `evidence_status`, `speaker`, `period_start_derivation`, `scope_status_as_of`를 둔다. 전사 scope ID는 유지하되 당시 scope 근거 상태는 `unresolved_retrospective_dependency`, 사업부는 `reported_segment_in_selected_table`이다. null마다 `field_missing_reasons`에 facts 필드 경로와 해당 없음/미상의 이유를 남긴다. 잔액의 `duration_days`는 null이다.

## 최종 검사

- 숫자 33, 관계 6, source claim 33, 발표 event/family 2, endpoint 3을 다른 분모로 센다.
- 없는 ID·틀린 source revision·값/scale·기간/year/단위 header·원문 span·관계 방향을 거부한다.
- unknown/null에는 이유를 둔다. 0은 실제 숫자다.
- 원본·기존 p0/p1/p2·작성자 독립 원본은 덮어쓰지 않는다.
- 개발/연습 자료와 정정·번역·중복·공유 주장 lineage가 test로 새지 않게 한다.
- 미라벨 예약 문서는 표본 확보와 노출 관리를 위한 자료이며 현재 test 정답/성능 분모에 넣지 않는다.
- 공개 산출물은 허용된 최소 사실·좌표·hash·판정만 담는다. 원문 prose·보호된 원본은 Git에서 제외한다.


## v1.1 연습 전 보완

A/B가 서로의 답을 보지 않은 상태에서 공통 naming/enum의 누락을 각각 발견했다. `annotation_clarifications_v1_1.json`에 전사/사업부 definition_version 명명, USD/GAAP의 선정 자료 문맥, preserve/outflow_to_positive, balance/flow, 기간 유도 문자열과 provenance 표현을 고정했다. 특정 항목의 숫자/정답은 추가하지 않았다. 숫자·span·기간은 계속 raw cell과 머리글에서 계산한다.

원 1.0 가이드/계약 및 stage2 freeze는 보존한다. 이 버전은 stage3의 연습 및 본 주석에 적용하고 mapper 1.0 기록은 출처 비교용으로 유지한다. 공통 metadata 제공으로 작성자는 완전 비보조 추출자가 아니며 결과는 공유 입력 위의 agent 구현 일관성이다.


## v1.2 연습 응답 척도 보완

첫 연습에서 숫자/원문 대응은 통과했으나 MQ06의 partially_supported와 MQ08의 investigate_then_defer처럼 응답 vocabulary가 확장됐다. v1.1 원본은 유지하며 본작업 전에 P1 질문 후보의 명시적 응답 범위를 적용해 다시 연습한다. 복합 판단과 부분 지지는 reason에 기술하고 response는 허용된 한 값을 선택한다.

- MQ01~MQ05: yes / no / unknown / not_applicable.
- MQ06: sufficient / insufficient / unknown / not_applicable. 질문은 원문 위치·기간·scope 연결의 충분성이다. 부분만 확인됐을 때 무엇이 부족한지 reason에 적고 이 네 값 중 판단한다. 전체 문서 완전성이나 실적의 외부 진실성은 판정 대상이 아니다.
- MQ07: comparable / conditional / not_comparable / unknown. prior 미제공이면 unknown이다.
- MQ08: maintain / revise / investigate / defer / not_applicable / unable_to_judge. 조사 후 보류하려는 복합 행동은 대표 행동 하나와 reason으로 기록한다.

이 수정은 척도의 통일이며 A/B에게 특정 항목의 응답을 지정하지 않는다. facts와 독립 판단 이유는 보존한다. 두 번째 연습 이후 불일치가 남으면 본 주석의 원본을 유지하고 다음 단계에서 필드별로 비교한다.
