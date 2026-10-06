# P07 · Phase 6 실행 설계 — 이전 발표와 비교하고 가능한 계산만 수행하기

> 실제 실행 2026-10-06: `change_002`에서 file store·세 시점 모드·exact/희소 검색·호환 검사·change·공식 계산/중단 계약을 실행하고 검증·재현과 사이트 버전 2 게시를 완료했습니다. [실행 결과](../artifacts/us_equity/p6/execution_briefing.md). 독립 qrels·change gold·정식 검색/변화 평가는 미실행이며 아래 내용은 실행 전 설계 이력입니다.

> 작성일 2026-10-06 / v0.1 / 상태: 실행 전. 검색·비교·계산 프로그램을 만들 실행안이며 실제 검색 정답·변화량·scenario가 생성됐다는 기록이 아니다.

[전체 로드맵](P06_P09_execution_roadmap.md) · [P07 연구 설계](P07_phase6_retrieval_change_scenario.md) · [공통 규약](DATA_CONTRACTS.md) · [사이트 업데이트 계약](SITE_PHASE_UPDATE_CONTRACT.md) · [다음 P08](P08_phase7_execution_plan.md)

## 1. 이번에 만들 것

**새 발표의 항목과 관련된 이전 공개 정보를 찾고, 같은 기준으로 비교할 수 있을 때만 변화량을 계산한다.** 이전 정보가 없거나 사업부·기간·회계 정의가 다르면 이유를 함께 보여준다. 계산에 필요한 값이 없는 경우에도 정상적으로 중단 결과를 반환하는 엔진을 만든다.

사이트에서는 ‘새 값’, ‘이전 값’, ‘기준이 맞는가’, ‘무엇이 바뀌었는가’, ‘왜 계산할 수 없는가’를 나란히 확인한다. 같은 이름의 사업부라도 정의가 바뀌었다면 값 두 개를 바로 빼지 않는다.

## 2. 현재 자료와 범위

| 실제 자료 | 수량/상태 | 사용할 용도 |
| --- | --- | --- |
| P05 후보 | 숫자 33개·`reports_segment` 6개 | 검색·비교 adapter의 개발 입력 |
| release/family | Microsoft 2개/2개, 같은 노출 그룹 | adaptation 사례; 독립 검색 benchmark 아님 |
| 기존 P03 비교 | `p2/applied_002/comparability_results.jsonl` 21행 | 결과 동결 후 별도 회귀 대조; 검색 정답으로 사용하지 않음 |
| scope 지원 문서 | 발행일 미상·2026-10-05 관측 | 현재 검토 문맥; 과거 검색에 자동 포함 금지 |
| prior ID·관계 유효시점 | P05에서는 미확인 | 이번 엔진에서 후보/미확인/부적합을 구분 |
| 독립 qrels·사람 change gold | 없음 | Recall@k·change 정확도 미평가 |

후보 지표는 매출·영업이익·순이익·CFO·현금 설비투자 지출·총자산·현금 및 현금성자산이다. 자료 확보 상태를 다시 확인한 뒤 실제 계산 가능 조합을 정한다. 33개 숫자 모두에 delta나 재무 비율이 생긴다고 가정하지 않는다.

현재 `reports_segment`는 보고 관계이지 고객·공급·경쟁 관계가 아니다. 새로운 사업 관계 종류·계획→실행·정정은 실제 허용 자료가 마련됐을 때 확장하며, 우선 합성 반례로 계약 동작을 확인한다. 신규 FY2026 Q1 예약 본문은 개발에서 열지 않는다.

## 3. 파일 store와 시점 정책

사용자의 DB 없는 2인 운영 요구에 맞춰 `event_store_records.jsonl`과 문서·registry manifest를 기준 저장소로 사용한다. ID 참조·중복·revision·조회 검사는 프로그램에서 수행한다. 기존 설계의 SQL/SQLite는 지금 필수 구현으로 채택하지 않는다. 검색 인덱스는 파일 manifest에서 재생성할 수 있는 파생 결과다.

원래 P05 후보는 변경하지 않고 P07 sidecar로 연결한다. 공개 날짜/시각, 실제 대상 기간, 적용 시점, 시스템 관측, 정정·revision을 각각 보존한다. 관계의 `valid_from/to`가 없으면 null이며 발표일이나 실적 기간으로 채우지 않는다.

### 검색 모드

| 모드 | 포함 조건 | 화면·평가 표현 |
| --- | --- | --- |
| `historical_public` | 당시 공개된 원문과 필요한 문맥/정의가 cutoff 이전임을 근거로 확인 | ‘당시 공개 정보 기준’; 확인되지 않은 의존성은 제외/보류 |
| `observed_live` | 위 공개 조건에 더해 실제 시스템 관측도 cutoff 이전 | ‘시스템 관측 기준’; 2026년에 수집한 자료를 2025 실시간 결과로 쓰지 않음 |
| `current_review` | 현재 확인 가능한 개발 자료로 사후 검토하되 관측·사후 문맥을 표시 | ‘현재 자료로 재검토’; 과거 backtest 성과로 보고하지 않음 |

기본 개발 화면은 `current_review`를 명확히 표시하고 두 과거 모드도 별도로 검사한다. 공개 날짜만 있는 경우 `prior.published_date < new.published_date`인 자료만 확실한 선행 후보로 허용한다. 같은 날짜 자료는 정확한 순서 근거가 없으면 `same_day_order_unknown`으로 보류한다. 00:00·시간대·DST를 임의로 만들지 않는다.

P05의 `availability_dependencies`와 `scope_status_as_of`를 필드별로 검사한다. 원문 숫자가 예전에 공개됐더라도 필요한 정의가 사후 문맥에만 의존하면 역사적 비교 적합성이 생기지 않는다. 과거 모드에서 계산 가능한 건수가 0이어도 사실대로 기록한다. 원문에 있는 정의 근거를 새로 확인한 경우 새 sidecar·revision으로 연결하고 기존 P05를 고치지 않는다.

run manifest에 모드·cutoff·날짜 정밀도·문맥 포함 정책·corpus hash·정책 버전을 남긴다. query와 corpus를 동결한 상태에서 미래 revision을 추가한 테스트는 과거 query 결과가 유지되는지 확인한다. 늦게 수집한 과거 문서로 corpus 자체가 바뀐 경우에는 새 corpus 버전으로 구분한다.

## 4. 검색과 prior 선택

기업/지표 또는 관계 타입 → 시점 → scope/기간/정의 조건 → 최소 라벨의 희소 검색 → 후보 호환성 검사 순서로 구현한다. 현재 입력이 선택 표 셀·표준 라벨이므로 전체 영문 본문을 인덱싱한 검색이라고 표현하지 않는다.

처음에는 exact key baseline과 로컬 희소 검색을 비교한다. 모든 후보에는 검색 방법·rank·선택/탈락 사유·원문 위치·공개시점 근거를 남긴다. embedding·hybrid·reranker는 자료 권리·실제 필요·dev qrels·모델 버전이 확보된 경우의 후속 작업이다. 미실행 dense 결과를 빈 점수나 추정 정확도로 채우지 않는다.

`retrieval_qrels.csv`의 독립 정답은 사람이 작성·감사한 경우에만 채운다. 자동 생성 후보는 `retrieval_review_candidates.jsonl`로 분리한다. ‘검색되지 않음’은 제한된 corpus 안에서의 결과이며 이전 공개 정보가 세상에 없다는 증거가 아니다. corpus coverage, no-hit, 모든 후보 부적합, 시점 근거 미확인을 다른 사유로 보존한다.

새 release 안의 전년 비교값은 **현재 발표가 회고한 수치**다. 이를 과거 당시의 독립 발표로 사용하지 않는다. 이전 release의 실제 claim과 연결하는 경우 문서·revision·정의·노출 이력을 모두 확인한다.

## 5. 비교·계산 계약

### 서로 다른 비교 종류

| 비교 | 조건 | 결과 이름 |
| --- | --- | --- |
| `same_period_revision` | 같은 실제 대상 기간·scope·지표·정의의 수정 주장 | 수정 차이; 정정 관계가 확인되지 않으면 정정으로 확정하지 않음 |
| `yoy` | 전년 대응 기간, 같은 기간 길이/흐름 성격·scope·회계 정의 | 전년 대비 변화; 동일 기간 수정과 분리 |
| `within_release_comparison` | 한 발표 안의 현재/비교 열과 머리글 조건 확인 | 해당 발표 기준 비교; 역사적 prior 검색 성과 아님 |
| `relation_state` | 관계의 양끝·방향·종류·scope·상태·시점 근거 확인 | 관계 상태 변화/미확인; 매출 delta로 변환 금지 |

FY2025 release의 FY2024 사업부 비교열은 `msft-segment-presentation-fy2025`를 유지한다. FY2024 release의 같은 사업부 이름과 자동 병합하지 않는다. 정의 불일치는 `not_comparable` 또는 추가 근거가 필요한 `needs_review`로 남긴다.

비교 검사에는 company, scope, definition, metric, GAAP/non-GAAP, currency/unit/scale, 실제 기간·기간 길이, balance/flow, modality, 출처 revision, 시점/문맥 의존성을 포함한다. 결과를 보고 호환 규칙을 완화하지 않는다.

### 숫자와 공식

- 절대차: `new - old`. 비율: `(new - old) / abs(old)`를 사용한다면 분모 정의를 기록하고 old=0에서는 비율 null을 반환한다.
- 음수 기준·손실→이익은 원값과 방향을 보여주며 일반 성장률처럼 설명하지 않는다. 비중 차이는 `%p`와 상대 변화율을 구별한다.
- P05 정규값은 USD base unit·`scale="1"`이다. source scale을 재차 곱하지 않는다. Decimal 문자열로 계산하고 출력 정밀도·반올림 정책을 보존한다.
- 누적→분기 차분은 포함 기간·회계 범위·revision이 맞을 때만 허용한다. 총자산 같은 시점 잔액을 분기 손익이나 현금흐름과 같은 방식으로 차분하지 않는다.
- 처음 검토할 공식은 동일 기간/전사/scope의 영업이익률과 **프로젝트 FCF = CFO - 양의 현금 설비투자 지출**이다. 입력이 맞는지 확인한 조합만 계산하며 회사 발표 FCF와 별도 metric으로 둔다.
- 순이익과 CFO의 차이는 설명용 차이일 뿐 완전한 현금흐름 대사가 아니다. 비현금/운전자본 조정 항목 없이 reconciled로 기록하지 않는다.

`calculation_registry.csv`에 공식 ID/버전, 입력 역할·부호·단위·기간·scope, 필요 문맥, 허용 범위, rounding, output kind를 등록한다. `financial_reconciliations.jsonl`에는 원문 보고 target이 없거나 조정 입력이 부족한 경우 `incomplete`/`not_applicable`과 null 잔차·사유를 남긴다. 숫자 대사가 맞아도 원문 전체 감사 완료로 취급하지 않는다.

### scenario와 사람 가정

현 자료에 없는 ASP·출하량·수율·재고·회사 guidance를 추정해 채우지 않는다. `scenario_runs.jsonl`의 `computed` 외 상태에서는 output이 null이고 필요한 입력 목록을 반환한다. 실제 가정이 없는 최초 run에는 계산 불가 사례를 기록한다. 테스트용 low/base/high 가정은 synthetic 파일에 분리한다.

회사 guidance, 사람 가정, 파생 전망은 각각 연결한다. 사람 가정이 생기면 `research_assumptions.jsonl`에 동일 미래 기간·scope·근거·반대 근거·작성/검토·supersedes 이력을 남긴다. 과거 자료로 지금 작성한 가정은 사후 재구성으로 표시한다. 가정 집합을 통계적 신뢰구간이나 회사 실제 전망으로 표현하지 않는다.

## 6. 실행 순서

| 작업 | 수행 내용 | 산출물·완료 조건 | 기존 연구 작업 연결 |
| --- | --- | --- | --- |
| P07-E01 | P05/registry 입력·노출·ID·권리·hash 감사, 파일 store adapter | `input_snapshot.json`, store/schema; 원본 보존·참조 연결 | T01 |
| P07-E02 | 세 검색 모드·cutoff·날짜/의존성 정책 구현 | `asof_policy.json`, `asof_query_cases.jsonl`; 미래/미상시각 반례 차단 | T02 |
| P07-E03 | query·candidate universe·qrels gate 정의 | `retrieval_protocol.md`, 검토 후보·정답 미확인 상태 | T03 |
| P07-E04 | exact/희소 검색·rank·no-hit/제외 이유 구현 | `retrieval_results.jsonl`, `retrieval_benchmark.md`; 같은 corpus/cutoff | T04/T05의 제한 baseline |
| P07-E05 | 비교 종류·호환 검사·prior 선택/보류 구현 | `prior_state_records.jsonl`, 호환 검사 필드별 결과 | T06 |
| P07-E06 | 수치/관계 change·현재 자료 비교 adapter | `change_records.jsonl`, `numeric_changes.jsonl`, `qualitative_changes.jsonl`; 입력 근거 추적 | T07/T08/T10 |
| P07-E07 | 공식·재무 계산·대사·scenario 중단/가정 계약 구현 | registry·scenario·reconciliation·assumption 상태 | T09/T11 |
| P07-E08 | 반례·출력 동결 후 P03 회귀 대조·재현 | `validation_report.json`, `reproducibility_report.md`; 회귀와 독립 점수 분리 | T12 |
| P07-E09 | 같은 사이트에 이전/새 정보·비교·계산 화면 추가하고 게시 | Phase export·화면·`site_update_manifest.json` | 최신 웹 요구 |
| P07-E10 | P06 후속 feature와 P08 카드 입력 인계 | `change_schema.json`, `change_benchmark.md`, `handoff_p6.md` | T10/T12 |

P06 최종 중요성 모델 없이도 E01~E10 개발을 진행한다. 독립 qrels/change gold가 없으면 benchmark에는 후보/계산 상태·회귀 결과만 넣고 Recall·정확도는 null/NA로 남긴다. P03의 21행은 같은 development 자료의 비교 회귀이며 검색 정답 universe가 아니다.

## 7. 파일·명령·검증

코드는 `scripts/p07_*.py`, 산출물은 `artifacts/us_equity/p6/runs/<run_id>/`에 둔다. 기존 P03/P04/P05 registry·결과·package를 수정하지 않는다. CLI 제안은 `p07_run.py`의 source run, cutoff-mode/cutoff, comparison policy, output run-dir와 `p07_verify_package.py`다. 아직 구현되지 않았으므로 실제 실행 명령으로 배포하지 않는다.

필수 반례와 실제 검증:

- 미래 revision·관계 문맥·사후 scope 지원을 넣어도 동결 corpus의 과거 query에 포함되지 않는다.
- date-only 같은 날 자료, 발행일 미상, observed-live에서 늦은 관측을 각각 보류한다.
- 동일 이름 사업부의 정의 차이, 다른 통화/scale, balance/flow, 실제 기간 불일치를 잡는다.
- 원문 0과 missing, old=0 비율, 음수 기준, `%`/`%p`, source scale 2중 적용을 구별한다.
- current release 전년 비교열을 과거 독립 문서로 선택하지 않는다.
- relation 방향/양끝/상태·시점 오류와 계획→실행을 숫자 delta로 바꾸는 오류를 잡는다.
- FCF의 capex 지출 부호를 한 번만 적용하고, CFO 대사 입력 누락에서는 incomplete를 반환한다.
- scenario 입력 부족/가정 없음/공식 오류는 숫자 결과 없이 사유를 반환한다.
- prior/change/calculation마다 원래 후보·문서/revision·근거·정책·공식이 연결된다.
- 같은 입력·정책 재실행의 의미 결과가 같고, synthetic 건수와 실제 후보 건수가 분리된다.

검색 시도 query 수, 후보 있음/없음, 시점 제외, 호환 가능/불가/미확인, change 계산/보류, formula 계산/실패의 분모·분자를 각각 보고한다. 항목별 복수 사유 수와 고유 항목 수를 혼합하지 않는다.

## 8. 사이트·인계·종료 조건

‘이전 정보와 비교’ 화면에서 검색 모드·기준 시점, 양쪽 문서/실제 기간/scope/정의, 원값·변화·검사 사유를 보여준다. ‘계산’ 상세에는 입력값·기간·공식·프로젝트/회사 정의 구별·입력 부족을 표시한다. 관계는 보고 상태와 유효시점 미상을 유지한다.

공유 화면에는 안전한 결과 snapshot만 게시하고 로컬 엔진과 구분한다. [사이트 업데이트 계약](SITE_PHASE_UPDATE_CONTRACT.md)의 export·검증·같은 프로젝트 게시를 완료한다. P06 변화 feature 연결 후에도 새 run으로 검증·화면 게시를 갱신한다.

**개발 종료:** 파일 store·time policy·prior 후보/보류·호환·change·가능한 계산/중단·재현·사이트 게시가 작동하고 P06/P08 계약을 전달했다. **연구 종료:** 독립 qrels/change 정답과 검색/변화 평가가 실제 수행된 범위에만 적용한다. 계산 불가 비율이 높거나 역사적 적합 건수가 0인 결과도 숨기지 않는다.
