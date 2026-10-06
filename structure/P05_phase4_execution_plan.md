# P05 · Phase 4 — 현재 P04 결과를 바탕으로 한 실행 설계

> 작성일 2026-10-06 / 설계 v0.1 / 상태: 다음 실행안. 이 문서는 현재 확보 자료에서 수행할 개발 작업을 정한다. P05 코드·예측·모델·실험 결과가 이미 생성됐다는 뜻은 아니다.

[기존 P05 전체 설계](P05_phase4_nlp_baseline.md) · [P04 실행 결과](../artifacts/us_equity/p3/execution_briefing.md) · [P04 dataset card](../artifacts/us_equity/p3/dataset_card.md) · [공통 데이터 규약](DATA_CONTRACTS.md)

## 1. 다음 단계에서 만들 것

**Microsoft 공식 실적 표의 선택 숫자·머리글·행 라벨을 받아, 원문 근거가 연결된 숫자 주장과 보고 사업부 관계 후보를 출력하는 M0 규칙 baseline을 만든다.** 실제 예측을 기존 agent 검토 자료와 비교해 단위·기간·scope·관계 연결 오류를 찾아 고친다.

현재는 인간 gold와 독립 train/dev/test가 없으므로, P05의 계약·파싱·규칙·검증 인터페이스 개발부터 진행한다. 인간 주석 부재 때문에 이 개발을 중단하지 않는다. 독립 성능 평가와 학습 모델 비교는 필요한 데이터가 마련됐을 때 별도로 실행한다. 기존 P05 설계의 전체 benchmark 종료 조건을 이번 제한된 개발의 종료 조건과 구분한다.

이번 개발의 질문은 다음 세 가지다.

1. 사람이 미리 정한 최종 값을 입력받지 않고, 선택 셀의 숫자·행 라벨·기간/단위 머리글에서 동일한 구조를 재구성할 수 있는가?
2. 근거 누락·정의 충돌·잘못된 단위/기간·미상 시점을 자동 검출하고, 임의 값 대신 검토 사유를 남길 수 있는가?
3. 후속 단계가 결과·실패·보류를 같은 인터페이스로 받아 원문과 실행 이력을 추적할 수 있는가?

## 2. 착수 시점의 실제 상태

작성 시점에 기존 `scripts/p04_verify_package.py`를 읽기 전용으로 재실행했고 **30/30 검사 통과**를 확인했다. 아래 수치는 P04 상태이며 P05 실험 결과가 아니다.

| 구분 | 현재 확보·실행 | 다음 단계에서의 용도 |
| --- | --- | --- |
| 기업·숫자 문서·발표 family | Microsoft 1개, release 2개, family 2개 | 동일 기업 adaptation 개발 |
| 숫자 주장 | 33개: 전사 24, 사업부 9 | 선택 셀 파싱·표준화 회귀 참조 |
| 보고 사업부 관계 | 6개, 고유 endpoint tuple 3개 | `reports_segment` 후보 생성·연결 회귀 참조 |
| 고유 주석 항목 | 39개: 숫자 33+관계 6 | 39개 독립 사건으로 세지 않음 |
| agent 본 주석·평가 | 각각 78개 | 참조 작성 이력; 학습 데이터나 인간 gold로 승격하지 않음 |
| 근거 위치·입력 packet | 84개·39개 | 선택 셀·표 머리글·표준 라벨, 본문 전체 아님 |
| scope 지원 문서 | 1개, 발행일 미상, 2026-10-05 관측 | 현재 상태 참고; 과거 시점 근거로 사용하지 않음 |
| 신규 FY2026 Q1 문서 | 1개 예약, 발행일 2025-10-29 | metadata만 확인; 이번 개발 입력에서 제외 |
| 인간 gold·독립 train/dev/test | 모두 0개 | 독립 성능 평가 미실행 |
| 현재 분할 | 기존 문서 3+주석 39=adaptation 42행, 예약 1행 | manifest의 43행을 43개 문서/사건으로 세지 않음 |

개발 release는 FY2024 Q4(2024-07-30)와 FY2025 Q4(2025-07-30)다. FY2025 자료의 FY2024 비교열 3개는 FY2025 발표 주장으로 유지한다. 두 family는 `LG-MSFT-EXPOSED-FY2024-FY2025-EARNINGS`라는 같은 누수 그룹에 있다. 인간 gold·독립 평가용 표본과 관련된 P04 미완료 항목은 그대로 유지한다.

## 3. 이번 범위와 조건부 후속 작업

| 작업 | 이번 실행 범위 | 후속 작업의 착수 조건 |
| --- | --- | --- |
| 선택 셀 입력 adapter·offset·단위/기간 파싱 | 진행 | 기존 허용 자료와 계약 사용 |
| M0 숫자·metric·사업부 이름 규칙 | 진행 | adaptation 사전·문서별 문맥 출처 기록 |
| `reports_segment` 후보 생성 | 진행 | 사업부 행·표 종류·기간 근거 필요 |
| 실제 예측과 agent 참조의 비교·오류 분석 | 진행 | 개발 회귀 결과로만 보고 |
| 전체 HTML의 표 발견·관련 셀 선택 | 현재 주 실행 범위에서 제외 | 별도 입력 범위·이용 조건·누락/추가 출력 감사 설계 |
| 문서 관련성 M1 | 보류 | 관련/무관 라벨, 학습용 데이터, 별도 검증 분할 |
| 문장 NER·사건 추출 M2 / embedding M3 | 보류 | 이용 가능한 영문 문장·span 라벨·독립 검증 자료·자원 확인 |
| 고객/공급/제품·계획/부인 관계 | 보류 | 허용 원문에서 직접 뒷받침하는 표본·정의·근거 |
| 독립 test benchmark | 보류 | 라벨·권리·본문·중복 감사, 모델/정책 사전 고정 |
| 중요성·투자 영향 판단, 전망 계산 | 이번 추출기의 출력 목표에 포함하지 않음 | P06/P07의 별도 prior·가정·비교·계산 계약 |

신규 FY2026 Q1의 숫자·본문을 이번 규칙 개발에 사용하지 않는다. 후속 사용 시 먼저 노출 이력과 split version을 갱신한다. 표 발견 규칙을 수정하는 데 사용하면 adaptation으로 이동하며, 그 자료를 untouched test로 보고하지 않는다. 발표일이 늦다는 사실만으로 독립 평가 적격성을 정하지 않는다.

기존 원문 prose의 AI 입력·학습 권리는 unresolved다. 현재의 최소 숫자·표준 라벨·기간·위치 기반 개발 범위를 유지한다. 학습 모델·외부 LLM·자동 수집 확대는 그 이용 목적에 대한 출처 조건이 확인된 뒤 별도로 설계한다. 이번 기본 실행에는 외부 호출·모델 다운로드·네트워크 수집을 넣지 않는다.

## 4. 입력·출력 계약과 정답 힌트 통제

### 4.1 파일별 역할

| 기존 파일 | P05에서 맡는 역할 | 추출기가 직접 읽는가? |
| --- | --- | --- |
| `p3/source_packets.jsonl`, `p3/evidence_index.jsonl` | 최소 셀·표 문맥과 근거 위치를 새 입력으로 변환 | 원본을 직접 읽지 않고 허용 필드 adapter를 거침 |
| `p3/annotation_reference.json`, `p2/metric_catalog.csv`, `p2/entity_catalog.csv` 등 | 고정된 개발 사전·scope/단위/기간 정책 | 필요한 사전 항목만 사용; adaptation에서 만든 이력 기록 |
| `p3/contract_records.jsonl` | nested 계약·원문 검증·숫자 배율의 참조 | 비교기·검증기만 읽음 |
| `p3/reviewed_agent_claims.jsonl`, `reviewed_agent_relations.jsonl` | 고정된 agent 회귀 참조 | 비교기만 읽음 |
| `p3/annotations_raw.jsonl`, `assessments_raw.jsonl` | 기존 작업의 provenance | 추출 입력에 포함하지 않음 |
| `p3/split_manifest.csv`, `split_policy.json`, `package_manifest.json` | 입력 허용 범위·hash·노출 검사 | 실행 시작 검사에 사용 |
| 예약 문서의 metadata·private 원문 | 예약 상태 확인 | 추출기가 접근하지 않음 |

기존 packet의 `item_id`와 `source_claim_id`에는 metric·scope·기간 정답이 문자열로 들어 있다. `source_record_ref`도 정리된 참조의 위치를 가리킨다. 이 값들을 지우지 않은 채 입력하면 문자열 분해만으로 답을 만들 수 있으므로 다음 계약을 적용한다.

- 새 `input_id`는 의미가 없는 식별자다. 원 packet/참조 항목과의 대응은 비교기 전용 `reference_links.jsonl`에 보관한다.
- 추출 입력에는 원 숫자 문자열, 행 라벨, 기간·연도·단위 머리글, 셀 위치, hash, 허용 문서 메타데이터와 문맥의 출처만 넣는다.
- `source_claim_id`, `source_relation_id`, 정답 item ID, `source_record_ref`, 정답 `metric_id`, 정답 period/scope 값, agent 응답·검토 결과는 넣지 않는다. 파일 이름을 분해해 기간을 결정하지 않는다.
- 숫자 셀 위치와 머리글의 연결이 이미 선택된 입력이라는 한계는 기록한다. 이것으로 문서 전체의 셀 발견·사건 발견 성능을 측정하지 않는다.
- packet의 scope label, USD/GAAP 문맥, 표의 segment/revenue 용도, 발표별 definition 매핑에는 사전 제공 문맥이 포함된다. 별도 `context_provenance`와 `context_origin=curator_provided`를 기록하고, 이 값의 일치를 독립적인 scope·회계기준 추론 성능으로 세지 않는다.
- `reports_segment` 입력도 출력 relation ID를 제공하지 않는다. 보고 표 종류·사업부 이름·회사·기간이라는 문맥에서 후보를 생성하며, 수치 파싱이 실패해도 명확한 관계 근거가 있으면 관계 후보를 별도로 보존한다.

### 4.2 숫자 표현

P05 출력은 **USD 기본 단위와 `scale=1`**로 통일한다. 원 배율과 부호는 별도 보존한다.

| 표현 | 실제 기존 필드·예 | P05 규칙 |
| --- | --- | --- |
| 계약 값 | `normalized.numeric_value="64727000000"`, `scale="1"` | 같은 기본 단위 계약으로 출력 |
| agent 참조 값 | `facts.numeric_value="64727"`, `scale="1000000"` | 비교 adapter에서 Decimal로 한 번 변환 |
| agent 참조의 기본 단위 | `facts.numeric_value_base_units="64727000000"` | 변환 결과와 대조 |
| 원문 표현 | `64,727`, unit header `millions` | 원문 문자열·source scale·위치를 보존 |

금액 계산은 Decimal로 수행하고 float 근사값을 정답으로 쓰지 않는다. 현금 capex의 괄호 음수는 원문에 보존하며 `positive_cash_capex`로 매핑할 때만 명시된 양수 지출 정책을 적용한다. 임의의 음수를 모두 양수로 바꾸지 않는다. 0·빈칸·dash·미상·실패는 따로 처리한다. 등록부의 파생 FCF나 margin을 원문에서 관측한 회사 실적으로 생성하지 않는다.

### 4.3 prediction과 실패 기록

P04 계약은 선택된 source claim과 agent 주석을 검증하는 계약이므로 새 예측을 그 source ID에 미리 맞춰 통과시키지 않는다. P05용 입력·예측 envelope를 별도 버전으로 만들고 공통 규약에 연결하는 adapter를 둔다.

- 예측의 기본 식별자는 `prediction_id`, `run_id`, `input_id`, `doc_id`, `revision_id`다. 실행 내부의 `candidate_claim_id`/`candidate_relation_id`와 기존 참조 ID는 분리한다.
- payload는 `raw / normalized / assessment / derived / provenance`를 구분한다. 회사·scope·metric·값·단위·기간·출처 상태는 후보의 사실 필드이고, 추출 검증 상태·불확실 사유·규칙 신뢰 신호는 별도다.
- envelope에 `schema_version`, `registry_version`, `rule_version`, `input_mode`, `evidence_refs`, `field_missing_reasons`와 `status`를 둔다. `status`는 `predicted / abstained / failed / quarantined`로 고정할 계획이다. 아직 enum이나 JSON schema 구현이 존재하는 것은 아니다.
- 회사 보고·미감사 표시 같은 출처 qualifier는 입력에 확인된 근거가 있는 범위에서 보존한다. 입력에 없는 감사 수준을 추정하거나 `externally_verified`로 올리지 않는다. `date_conflict_status`는 별도 감사가 수행되기 전까지 `not_yet_checked`다.
- 정의·별칭·기간이 모호하면 후보와 사유를 남긴다. 채택할 사실에 근거가 없거나 타입/단위가 잘못되면 격리하고 후속 store 입력으로 통과시키지 않는다.
- confidence는 `rule_signal`과 `score_type=uncalibrated_rule` 같은 해석으로 기록하고 확률은 null로 둔다. 공유 참조 일치율을 확률 보정 결과로 쓰지 않는다.
- `review_readiness`는 이번 개발의 historical comparison 목적에서 `needs_review`를 유지한다. 파싱 성공을 prior·scope·정의 정책 검토 완료로 바꾸지 않는다. P04의 MQ 응답을 예측하지 않는다.
- 모든 입력은 `input_results.jsonl`에 terminal status 한 행을 갖는다. 출력 후보 0개도 명시하고 `prediction_ids`, 실패 단계·이유·시도를 연결한다. 입력 수·결과 행 수·후보 수는 다른 분모다.

날짜는 `published_date`와 precision만 확인되면 정확 시각·시간대를 만들지 않는다. 보고 `reference_period`와 실제 관계 `effective_period / valid_from / valid_to`는 분리한다. 사업부의 FY2024 비교열은 FY2025 presentation definition을 유지한다. 전사 scope의 후향 지원 의존성 24개와 가이드의 사후 노출을 보존하고 역사적 blind 평가를 주장하지 않는다.

## 5. 실행 순서 — 각 번호 종료 후 자가검증·개선

이번 P05 개발도 **1 → 검증·개선 → 2 → 검증·개선 → 3 → 검증·개선 → 4 → 검증·개선 → 5**로 진행한다. 검증 통과의 의미는 아래 각 단계의 구현 조건에 한정한다. 아직 실행하지 않은 검사를 통과로 적지 않는다.

### 1번 · 프로토콜·입출력·실행 환경 고정

**수행:** P04 package hash를 검사하고 33 숫자/6 관계·2 release의 개발 범위와 예약 제외를 고정한다. 기존 P05-T01과 T07의 계약 작업을 먼저 수행한다. 입력 허용 목록·정답 접근 구분·예측 schema·숫자 표현·metric의 분모·제외 정책을 작성한다. 필요한 로컬 라이브러리·버전·하드웨어를 실제 확인하고 dependency lock을 남긴다. 예산 기본값은 외부 호출 0이다.

**산출물:** `baseline_protocol.md`, `input_manifest.csv`, `input_schema.json`, `prediction_schema.json`, `environment_manifest.json`, `input_snapshot.json`.

**자가검증:** 기존 P04 30개 검사 유지, source/code/schema hash 확인, 39개 항목 보존, reserved/legacy 입력 0개, base/source 배율 일치, 필요 라이브러리 import 확인. 알려지지 않은 정답 ID·전체 원문·사후 평가값이 허용 입력에 들어가면 실패시킨다.

**개선 후 다음 조건:** 필드·단위·입력 범위 충돌을 해결하고 실제 실행 명령을 기록했다. 독립 평가가 없다는 상태가 manifest에 명시돼 있다.

### 2번 · 선택 셀 입력·offset·문맥 adapter

**수행:** 기존 39개 packet에서 허용 입력만 만들어 추출 입력과 회귀 참조를 분리한다. raw 숫자·표준 라벨·공백/NBSP·머리글 연결·원 DOM 셀 기준 위치를 보존한다. 새 근거 ID가 기존 84개 위치로 돌아가는 매핑을 만든다. 숫자 입력 33과 관계 문맥 입력 6을 구분한다. 같은 근거가 재사용되는 경우에는 독립 원문 증거로 중복 계산하지 않는다.

**산출물:** `extractor_inputs.jsonl`, `reference_links.jsonl`, `evidence_map.jsonl`, `preprocess_audit.csv`, `context_provenance.jsonl`.

**자가검증:** 39/39 입력의 참조 연결, 해당 근거 위치 왕복, 정규화 전후 code point offset 복원, 누락/중복/원문 hash 불변 검사. 숫자0·괄호 음수·NBSP·누락된 unit/year header·잘못된 행열 연결을 넣은 합성 반례로 adapter가 값을 조작하거나 문맥을 상속하지 않는지 검사한다. 참조 파일을 추출 실행 경로에서 제외하고, 참조 정답만 바꿨을 때 고정된 입력의 예측 payload가 변하지 않는지도 검사한다.

**개선 후 다음 조건:** 모든 입력이 올바른 근거 또는 명시적인 실패 상태로 연결된다. 원래 item ID·정답 필드가 추출 입력에 남지 않았고, 사전 제공 문맥과 실제 관측 값을 구별했다. 원 source/packet/참조는 덮어쓰지 않는다.

### 3번 · M0 숫자·기간·지표·보고 사업부 관계 구현

**수행:** 7개 관측 metric의 명시적 영문 행 라벨, 3개 사업부 이름과 보고 표 문맥으로 후보를 생성한다. 숫자 parsing·unit scale·부호·instant/duration·분기/연간·연도·기간 시작 파생 근거를 각각 처리한다. 유사한 이름이거나 단위/scope가 모호하면 abstain한다. `reports_segment`는 보고 회사→보고 사업부 방향과 보고기간을 유지한다. 값·개체가 같이 등장한다는 이유만으로 고객/공급 관계를 만들지 않는다.

**산출물:** `rules_v0_1.json`, `rule_provenance.csv`, `predictions.jsonl`, `input_results.jsonl`, `normalization_audit.jsonl`.

**자가검증:** 서로 바뀐 row/year/quarter·annual 열, 잔액/흐름 혼동, 366/365일 연간 기간, 백만 배 중복, capex 이중 부호 변환, 모호 alias, 거꾸로 된 관계, 보고기간의 실제 유효기간 승격을 검사한다. 합성 반례에는 `synthetic=true`를 붙여 실제 source 주장·gold·평가 표본에 섞지 않는다.

**개선 후 다음 조건:** 규칙별 성공/보류/실패를 추적할 수 있다. 필수 타입·배율·근거·시점 오류는 수정했다. 지원하지 않는 입력은 정답을 채우지 않고 abstain/실패로 남는다. 예측을 보고 규칙을 바꾸면 새 rule version과 재실행을 기록한다.

### 4번 · 실제 예측 비교·오류 분석·근거 검증

**수행:** 결과 파일을 먼저 고정한 뒤 비교기가 agent 참조를 읽는다. 추출기는 이 비교 과정에서 정답을 받지 않는다. 후보는 doc/revision·근거 위치·대상 필드에 대한 사전 고정 규칙으로 one-to-one 매칭한다. 같은 참조를 여러 후보의 성공으로 중복 채점하지 않는다. 매칭 누락·추가 후보·동률 충돌은 각각 남긴다.

숫자·단위·기간·metric·scope와 관계 endpoint/역할/방향/보고기간을 따로 비교한다. 원문 위치 재조회가 필요한 경우 기존 허용 위치만 로컬에서 검증하고, source 원문 prose나 reserved 내용을 도구 출력·agent 입력으로 내보내지 않는다. 날짜 충돌·전체 본문 완전성 감사는 자동 셀 검증과 구분한다.

**산출물:** `reference_match_results.jsonl`, `metrics.csv`, `error_analysis.csv`, `development_report.md`, `validation_report.json`, `fallback_policy.md`.

**자가검증:** 바뀐 숫자·ID·누락된 입력·중복 후보·invalid schema·사후 의존성·관계 방향·감사 수준의 과장 오류가 결과와 분모에 반영되는지 검사한다. 숫자 파싱 실패를 낮은 중요성으로 바꾸지 않는다. reference에 없는 추가 후보를 자동 FP로 만들지 않는다. seed·처리시간·실패·미측정 항목을 실제 값으로 기록한다.

**개선 후 다음 조건:** 중요한 구조/연결 오류는 수정·재실행하고 미해결은 원인·범위·후속 작업을 기록했다. 보고서가 agent 참조와의 개발 회귀임을 명시한다. 복잡한 모델로 해결할 필요가 확인되지 않은 오류는 parser·registry·계약에서 먼저 고친다.

### 5번 · 버전 고정·개발 인계·다음 평가 조건 결정

**수행:** M0 기본값과 parser/adapter의 버전·출처·schema·입력·결과 hash를 고정한다. 원문 재배포 제한과 known failures, 조건부 모델·독립 평가의 미실행 상태를 인계한다. 근거 검증을 통과한 후보와 abstain/failed/quarantined를 구분해 후속 개발이 소비할 수 있는 인터페이스를 제공한다.

**산출물:** `model_selection.md`, `handoff_p4.md`, `execution_briefing.md`, `task_status.csv`, `package_manifest.json`, `verification_commands.md`.

**자가검증:** 고정된 입력으로 별도 출력 폴더에 재실행해 semantic payload가 같고 모든 입력에 결과가 남는지 확인한다. 실행 시각/run ID는 재실행마다 달라질 수 있으므로 동일성 비교에서 구분한다. P0~P3 입력 hash, reserved 제외, legacy 혼입 없음, private Git 제외, manifest의 현재 코드·결과 hash를 마지막에 대조한다.

**종료 조건:** 이번 1~5번 개발 산출물과 검사·개선·재현·실패 인계가 완성됐다. 상태는 `development_baseline_ready`다. 정식 P05 benchmark 완료, 인간 gold 확보, 독립 성능·일반화 측정은 별도 상태로 남긴다.

### 단계별 기록 형식

각 번호는 `stage_reviews/stage_01_initial.json`, `stage_01_improvements.md`, `stage_01_final.json` 같은 순서로 기록한다. gate는 `passed_with_explicit_limitations / needs_improvement / failed`를 구별하고, 다음 번호는 이전 번호의 최종 개발 gate를 확인한 뒤 시작한다. 초기 실패·이전 규칙·예측을 보존한다. final에는 검사명·실제 입력/출력 건수·통과/실패·미실행·코드/입력/결과 hash·미해결·다음 행동을 적는다. 미실행 독립 평가를 개발 gate 통과에 포함하지 않는다.

## 6. 무엇을 측정하고 어떻게 해석할 것인가

| 지표 | 현재 가능한 분모·판정 | 해석 |
| --- | --- | --- |
| 입력 보존·terminal result | 입력 39개, 항목별 결과 한 행 | 조용한 누락 방지·운영 추적 |
| schema/근거/배율 검사 | 실제 출력 후보 전체 및 입력 실패 별도 | 구현 계약 검사; invalid 후보는 격리 |
| 숫자 필드 개발 참조 일치 | 참조 33개에서 각 필드의 관측/제공 상태별 분모 | M0와 기존 agent 참조의 회귀 비교 |
| 숫자 전체 묶음·기간 일치 | 매칭·누락·abstain을 포함한 대상 33개와 평가 가능한 수 별도 | 원문 셀이 미리 선택된 조건부 비교 |
| `reports_segment` 필드·tuple | 참조 6개, 원 숫자 주장 참조 연결 따로 | 보고 사업부 관계에만 한정 |
| span exact·문자 겹침 | 숫자 대상 최대 33개; 성공/실패/비교불가 분리 | 같은 DOM 셀의 code point 범위; 문서/문장 span 성능 아님 |
| 처리시간·자원 | 실제 입력수·환경·초기화/처리·실패 기록 | 2문서·39항목 관측을 대량 운영 보장으로 확대하지 않음 |
| 독립 precision/recall/F1·관련성·NER·importance | 평가 가능한 독립 표본 0개 | null / not_evaluated |

관측한 값과 제공 문맥은 별도 열로 집계한다. `null`, `unknown`, `unresolved*`, `not_applicable` 상태가 같은 경우 상태 일치와 관측 값 일치를 구분한다. 분모0은 null이고 0%/100%로 표시하지 않는다. 실패 때문에 관측 항목을 분모에서 조용히 빼지 않는다. 관측 가능한 참조가 있는데 예측이 실패/abstain한 경우 해당 참조를 회귀 비교 분모에 남긴다.

현 참조는 선택 항목만 포함해 모든 실제 주장과 추가 후보의 정답을 포괄하지 않는다. 따라서 매칭되지 않은 후보의 옳고 그름과 전체 pipeline FN/FP를 확정할 수 없고, 독립 precision/recall/F1을 계산하지 않는다. 합성 반례 통과는 규칙 검증이며 새로운 실제 문서의 성능 표본이 아니다. 같은 두 family에서 여러 seed·rule version을 실행해도 독립 표본이 늘어나지 않는다.

## 7. 산출물 위치와 재현 구조

제안 경로는 `artifacts/us_equity/p4/`이고 실행별 결과는 `runs/<run_id>/`에 둔다. 기존 P04 동결 파일을 수정하지 않는다.

```text
artifacts/us_equity/p4/
  baseline_protocol.md
  input_manifest.csv / input_snapshot.json / environment_manifest.json
  input_schema.json / prediction_schema.json
  extractor_inputs.jsonl / reference_links.jsonl / evidence_map.jsonl
  context_provenance.jsonl / preprocess_audit.csv
  rules_v0_1.json / rule_provenance.csv
  runs/<run_id>/
    run_manifest.json
    predictions.jsonl / input_results.jsonl / normalization_audit.jsonl
    reference_match_results.jsonl / metrics.csv / error_analysis.csv
    validation_report.json
  stage_reviews/
    stage_01_initial.json / stage_01_improvements.md / stage_01_final.json
    ... stage_05까지 같은 형식의 기록
  development_report.md / fallback_policy.md
  model_selection.md / task_status.csv / handoff_p4.md
  execution_briefing.md / package_manifest.json / verification_commands.md
scripts/
  p05_prepare_inputs.py
  p05_rule_baseline.py
  p05_validate_predictions.py
  p05_compare_reference.py
  p05_verify_package.py
```

위 경로와 스크립트는 생성 계획이다. 현재 존재하거나 실행에 성공했다는 기록이 아니다. 원문·이용 제한 자료를 보관할 경우 기존 `private/` 제외 정책을 적용한다.

run manifest에는 실행 시각, input/code/schema/registry/rule/dependency hash, 환경, input mode, exposure, 참조를 읽은 시점, 시도·실패 수, 실제 시간·자원·외부 호출 수를 기록한다. input ID와 결과를 추적할 수 있게 하며 자격증명을 포함하지 않는다. 재현 명령은 코드 구현·실행 후 확인된 실제 CLI로 작성한다.

## 8. 기존 P05 작업과의 대응

| 기존 작업 | 이번 1~5번의 대응·상태 |
| --- | --- |
| P05-T01 프로토콜·환경 | 1번에서 개발 범위 고정 |
| P05-T02 parser·offset | 2번에서 선택 셀/머리글 범위 구현 |
| P05-T03 M0 규칙 | 3번에서 구현 |
| P05-T04 관련성 M1 | 관련/무관 학습·평가 자료가 마련될 때까지 보류 |
| P05-T05 span·사건 M2 | 문장·span 라벨·허용 입력·검증 자료 마련까지 보류 |
| P05-T06 metric·개체 매핑 | 3번의 exact label·scope/단위 제약 구현; embedding 보류 |
| P05-T07 인터페이스 | 1번에서 먼저 정의하고 2~4번에서 구현·검증 |
| P05-T08 dev 비교 | 4번의 adaptation 회귀로 제한; 정식 dev benchmark와 구분 |
| P05-T09 confidence·fallback | 4번에서 미보정 규칙 신호와 호출 disabled 정책 기록 |
| P05-T10 고정 test | 독립 test 준비까지 보류 |
| P05-T11 선택·인계 | 5번에서 개발 M0 인계; 정식 모델 비교는 보류 |

## 9. 독립 평가로 넘어가기 위한 후속 조건

이 조건들은 현재 1~5번의 개발을 막는 승인 절차가 아니라, 독립 benchmark를 실행하기 전에 마련할 데이터·운영 요구다.

1. 의도한 수집·분석·모델 입력/학습·외부 전송 용도의 출처 조건을 축별로 확인한다. 선택 셀 참조 조건을 본문 corpus 권리로 확대하지 않는다.
2. 원문 숫자·기간·scope·관계·근거에 대한 실제 사람의 독립 기록과 조정, 작성/검토 주체·시점·노출을 확보한다. agent 초안을 사용한 도움의 범위도 남긴다.
3. 새 문서의 본문·날짜·표/인용·정정·번역·비교열·family 중복을 감사한다. 고객/공급 관계·계획/부인·무관 대조를 포함하려면 별도 표본·라벨이 필요하다.
4. 학습/검증/test 배분은 실제 기업·기간·family 분포와 표본 규모에서 새 split version으로 정한다. 기존 노출 자료는 adaptation에 남긴다. 관측한 문서 2개만으로 비율·시간 경계를 억지로 만들어 독립 train/dev/test를 주장하지 않는다.
5. test 정답을 열기 전에 규칙·사전·모델·threshold·평가 매칭·unknown·추가/누락 후보 판정·전체 문서 기준 분모를 고정한다. 독립 test에 가능한 통제를 적용하고 접근 이력과 남은 한계를 적는다.

이후 실제 개발 오류와 새 데이터 규모를 보고 M1/M2/M3 후보와 자원을 선택한다. 모델 이름이나 기존 연구의 점수를 정확성 목표로 미리 채택하지 않는다. P06에는 추출 불확실성을 포함한 feature 계약, P07에는 근거 연결 후보 계약을 넘길 수 있지만, 현재의 unknown MQ 응답을 중요성 정답으로 학습시키지 않는다.

## 10. 이 설계의 검토 기준

설계 검토에서는 현재 수치·버전·분할을 P04 manifest와 대조하고, 각 단계의 입력/산출물/검증/다음 조건, ID 정답 힌트 차단, 숫자 표현, source/derived 구분, 실패 보존, 개발/독립 평가 분모 구분을 확인한다. 이번 문서 작성으로 P05 예측·실험·검증 통과 상태를 생성하지 않는다.

근거는 위에 연결한 저장소의 P04 실제 산출물, 기존 P05 설계, 공통 규약이다. 새로운 모델·라이브러리·논문 성능을 조사하거나 채택한 문서가 아니며, 모델 구현을 시작할 때 해당 공식 문서·라이선스·현재 버전을 확인해 실행 manifest에 남긴다.
