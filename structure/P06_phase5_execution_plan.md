# P06 · Phase 5 실행 설계 — 무엇을 먼저 확인할지 정리하기

> 실제 실행 2026-10-06: `review_002`에서 최초 검토 목록을 만들고, P07 연결을 별도 `review_change_003`/`review-0.2.0`에 저장했습니다. 현재 개발·검증·재현 및 사이트 버전 2 게시 완료. [실행 결과](../artifacts/us_equity/p5/execution_briefing.md). 중요성 모델·독립 평가·ablation은 미실행이며 아래 내용은 실행 전 설계 이력입니다.

> 작성일 2026-10-06 / v0.1 / 상태: 실행 전. 현재 자료로 개발할 검토 목록과, 추가 데이터가 있어야 수행할 중요성 연구를 구분한다. 코드·순위·모델·검증 결과는 아직 생성되지 않았다.

[전체 로드맵](P06_P09_execution_roadmap.md) · [P06 연구 설계](P06_phase5_materiality_modeling.md) · [사이트 업데이트 계약](SITE_PHASE_UPDATE_CONTRACT.md) · [다음 P07](P07_phase6_execution_plan.md)

## 1. 이번에 만들 것

**추출한 항목에 ‘왜 확인해야 하는가’, ‘무엇이 아직 부족한가’, ‘다음에 무엇을 볼 것인가’를 붙여 검토 목록을 만든다.** 현재는 중요성 정답이 없으므로 금액이 크거나 이익이 증가했다는 이유만으로 중요도를 확정하지 않는다.

처음 보는 사람은 사이트에서 항목을 선택해 숫자·기간·사업 범위·근거와 함께 확인 질문을 읽을 수 있어야 한다. 예를 들어 사업부 정의가 다른 항목에는 ‘이전 발표와 같은 기준인지 확인 필요’를 보여준다. 이는 검토 사유이지 기업 가치나 매수·매도 판단이 아니다.

## 2. 착수 조건과 실제 입력

착수 시 [P05 active run](../artifacts/us_equity/p4/active_run.json)을 읽고 `scripts/p05_verify_package.py`로 동결 상태를 확인한다. 공식 결과는 `m0_004`이며 숫자 33개·보고 사업부 관계 6개, 총 39개 후보가 있다. 모든 후보는 검토 필요 상태이고 사람 gold·독립 train/dev/test는 0개다.

| 입력 | 용도 | 사용 제한 |
| --- | --- | --- |
| `p4/candidate_store_records.jsonl` | 원문/정규화/판단/파생 층을 보존한 기본 입력 | P04 gold schema나 인간 정답으로 취급하지 않음 |
| `p4/validated_candidates.jsonl` | P05 예측·ID·근거의 교차 확인 | 개발 후보이며 외부 사실 보장 아님 |
| `p4/relation_claim_links.jsonl` | 숫자·관계 공유 근거와 중복 검토 연결 | 숫자와 관계를 독립 표본으로 합산하지 않음 |
| P05 입력/근거/문맥 provenance | 필드 누락·scope·시점 사유 추적 | 사후 제공 문맥을 과거 당시 정보로 바꾸지 않음 |
| P04 split/exposure·인계 | adaptation·예약 문서·미완료 확인 | 기존 agent assessment를 중요성 학습 정답으로 사용하지 않음 |

기본 입력 루트는 `artifacts/us_equity/`다. reserved FY2026 Q1 본문, 기존 한국기업 artifact, P05 참조 답안은 실행 입력에서 제외한다. 원문 전체를 새로 수집하거나 외부 LLM에 보내지 않는다.

## 3. 지금 할 개발과 조건부 연구

| 작업 | 현재 실행 | 추가 착수 조건 |
| --- | --- | --- |
| 후보/누락 정보/검토 사유 adapter | 진행 | 검증된 P05 후보와 provenance |
| 시간순·사유별 검토 목록 | 진행 | 정해진 정렬 정책·동일 후보 집합 |
| 원문 사실·판단·불확실성 표시 | 진행 | 근거와 missing reason |
| 사람 간 중요성 표현 비교 | 미실행으로 기록 | 독립 사람 assessment, 조정 전 기록, 충분한 분포 |
| 분류/순위 모델 학습·확률 보정 | 보류 | 오염 감사된 train/dev/calibration과 사람 정답 |
| 중요 사건 recall·NDCG 평가 | 보류 | 사건 단위 universe·중요성 정답·독립 test |
| 시장 반응 분석 | 기본 경로에서 제외 | 가격 권리·거래일·발표시각·연구 프로토콜을 별도 확보 |
| P07 변화 feature | 최초 run에서는 missing | P07 검증된 change와 이용 가능 시점 |

원래 P06의 전체 연구 종료 조건을 이번 개발 완료 조건으로 대신하지 않는다. 개발을 진행하되 `formal_materiality_benchmark_complete=false`를 유지한다.

## 4. 데이터·정렬 계약

P05 레코드는 수정하지 않는다. 새 sidecar는 `record_id`, 원래 `candidate_claim_id` 또는 `candidate_relation_id`, `prediction_id`, family·문서·revision·원래 run 참조로 연결한다.

### feature

`feature_registry.csv`에는 feature명, 원천 필드/ID, raw/normalized/assessment/derived 구분, 변환식, missing 정책, 공개시점 근거, 관측시점, 사용 모드, train-fit 여부, 누수 위험, 버전을 적는다. `feature_records.jsonl`에는 후보별 값·원천·이용 가능 여부를 기록한다.

현재 사용할 것은 지표/관계 종류·scope·modality·근거 연결 상태·필수 필드 누락·정의/시점 검토 사유다. 과거 시점의 feature는 각 문맥 의존성까지 당시 이용 가능했는지 확인한다. 확인되지 않으면 `historical_eligible=false` 또는 미확인으로 남긴다. 현재 시점 검토 목록을 과거 시점 중요성 예측이라고 부르지 않는다.

`prior`, novelty, 변화량, 재무 영향 규모는 현재 없는 값이므로 null과 `not_yet_checked`/`prior_not_available` 사유를 둔다. 최신 실적·사후 주가·평가자의 정답·차기 발표는 입력 feature로 쓰지 않는다. 관계의 존재만으로 매출 기여도나 인과 feature를 만들지 않는다.

### 검토 목록

`ranking_predictions.jsonl`의 최소 필드 제안:

```text
review_item_id, source_record_refs, event_family_id, review_group_id,
review_session_id, policy_version, ordering_method, position,
review_reasons, missing_features, suggested_checks,
review_readiness, materiality_label, materiality_score,
score_type, probability, historical_eligible, exposure_status, run_id
```

기본 목록은 확인할 사유별로 묶고, 각 묶음 안에서는 공개 날짜와 안정 ID로 정렬한다. 날짜 미상과 같은 날짜의 동률 처리 규칙을 명시한다. ‘사유별 보기’와 ‘시간순 보기’는 같은 후보 universe를 사용하며 실패/보류 항목도 유지한다.

학습·검증 전에는 `materiality_label=null`, `materiality_score=null`, `probability=null`, `score_type=not_estimated`다. 목록 위치를 중요성 확률이나 높은/낮은 등급으로 바꾸지 않는다. 현재 39개 후보, 고유 검토 묶음, 발표 family 2개를 별도 집계한다. 숫자와 연결 관계의 중복 근거는 묶어 보여주되 원래 후보를 삭제하지 않는다.

`review_readiness`와 `evidence_status`는 별도 축이다. P06 정렬만으로 P05의 `needs_review`를 `supported`로 승격하지 않는다. 사유가 해소되면 새로운 검토 기록과 근거로 상태를 갱신하고 원래 후보의 상태를 보존한다.

## 5. 실행 순서

아래 `E` ID는 이 실행안의 작업이다. 원래 연구 설계의 `T` ID와 구분한다.

| 작업 | 수행 내용 | 결과·종료 조건 | 기존 연구 작업 연결 |
| --- | --- | --- | --- |
| P06-E01 | P05 hash·입력 수·권리·exposure·사람 라벨 부재 감사 | `input_snapshot.json`, `readiness_report.md`; 39개 입력 보존 또는 변경 이유 명시 | T01/T02 |
| P06-E02 | 검토 단위·누락·사유·정렬·동률·모드 계약 고정 | `materiality_protocol.md`, 입출력 schema; 후보와 사건 수 구분 | T01/T03 |
| P06-E03 | feature adapter·필드별 시점 감사 구현 | registry와 후보별 feature; 모든 값에 원천/사유 | T03 |
| P06-E04 | 시간순/사유별 목록·중복 근거 연결 구현 | `baseline_rankings.jsonl`, `ranking_predictions.jsonl`; 모든 입력의 결과/실패 상태 | T04 |
| P06-E05 | 학습·보정·평가 gate와 미실행 보고 구현 | `label_structure_report.md`, `representation_comparison.csv`, `calibration_report.md`; 점수 null·실제 사유 | T02/T05/T08/T09 |
| P06-E06 | 계약·반례·보존·의미 재현 검사 | `validation_report.json`, `reproducibility_report.md`; 실패는 별도 보존 | 필수 검증 |
| P06-E07 | 같은 사이트에 검토 목록·사유·확인 질문 추가하고 게시 | 실제 Phase adapter·화면·`site_update_manifest.json` | 최신 웹 요구 |
| P06-E08 | 개발 선택·미실행 연구·P07 입력 인계 | `materiality_decision.md`, `model_card.md`, `handoff_p5.md` | T11 |

E05는 결과를 만들어내는 학습이 아니라 gate와 상태 보고부터 구현한다. representation comparison 행에는 `execution_status`, 평가 건수, metric null 사유를 포함한다. 시장 분석은 `outcome_feasibility.md`에 현재 미실행 이유를 남기고, 실제 수집을 하지 않았으면 빈 `outcome_manifest.csv`의 의미도 명시한다.

P07 완료 후 별도 `P06-E09`로 change adapter·available-at 감사·같은 사이트 갱신을 수행한다. 독립 dev가 있으면 원래 T10의 ablation을 실행하고, 없으면 `change_feature_ablation.md`에 연결 검증과 성능 미평가를 분리한다. 새 run을 만들며 원래 test를 반복 선택에 사용하지 않는다.

## 6. 파일·실행 인터페이스

새 코드는 `scripts/p06_*.py`, 산출물은 `artifacts/us_equity/p5/runs/<run_id>/`에 둔다. P05 파일명 glob에 포함되는 `scripts/p05_*.py`는 추가·수정하지 않는다.

구현할 CLI 계약은 `p06_run.py`의 입력 P05 run/adapter 경로, 출력 run-dir, 정책 경로와 `p06_verify_package.py`의 입력 run-dir다. **이 CLI는 아직 없으며 실행 가능한 명령으로 안내하지 않는다.** 실제 구현 후 `--help`와 현재 환경에서의 재실행 결과를 운영 안내에 기록한다.

각 run에는 protocol·schema·feature/목록·실패 상태·입력/출력 hash·코드/의존성/정책 버전·검증·모델 카드·인계·사이트 게시 기록을 남긴다. 미구현 모델의 ID·패키지 버전·실험 점수를 미리 채우지 않는다. 기존 설치 환경과 단순 파일 처리를 출발점으로 사용하고 추가 패키지·모델 다운로드는 실제 필요와 권리를 확인한 경우만 수행한다.

## 7. 의미 있는 검증

- 현재 39개 입력 모두가 목록 또는 명시적 오류/보류에 연결되고, relation 공유 근거를 추가 숫자로 세지 않는다.
- 큰 금액·증가 방향·재무 수치 없는 관계가 자동 중요/무관 판정으로 바뀌지 않는다.
- prior 없음·시점 미상·scope 충돌이 0점·낮은 중요성으로 치환되지 않는다.
- 사후 scope 문맥·미래 정정·차기 실적을 넣은 반례를 과거 feature 검사에서 차단한다.
- 새 규칙 실행만으로 검토 완료·확률 보정·사람 gold가 생기지 않는다.
- 동률·날짜 미상·입력 순서 변경에도 정해진 목록 의미와 stable ID가 유지된다.
- 같은 입력·정책 재실행의 의미 결과가 같고 timestamp/run ID 차이는 별도 비교한다.
- 독립 평가 분모 0이면 metric은 null/NA이고 미실행 사유를 보여준다. 합성 반례는 실제 표본 건수와 분리한다.

기존 P04/P05 package 검증을 읽기 전용으로 다시 확인한다. 브라우저 확인 여부는 실제 수행에 맞게 기록한다.

## 8. 사이트에서 보일 결과와 종료 조건

‘검토할 항목’ 화면에 날짜·지표/관계·scope 필터, 검토 사유별/시간순 보기와 항목 상세를 추가한다. 상세에는 현재 주장, 원문 위치·허용된 숫자, 부족한 정보, 확인 질문을 보여준다. 기본 화면에 모델 내부 점수나 가짜 정확도를 넣지 않는다. 기존 추출 결과도 계속 조회할 수 있어야 한다.

[사이트 업데이트 계약](SITE_PHASE_UPDATE_CONTRACT.md)에 따라 allowlist export와 검증, 같은 프로젝트 게시 성공을 확인한다. 실행 결과에 연결된 후보 수·검토 묶음 수·독립 평가 미실행을 표시하고 게시한 run/시각을 남긴다.

**개발 종료:** 입력 보존·feature/검토 사유·정렬·반례·재현·사이트 반영을 확인하고 P07이 읽을 계약을 인계했다. **정식 연구 종료:** 독립 라벨·모델·일치도·운영점·평가 조건이 실제 수행된 경우에만 별도로 인정한다. 현재 자료만으로는 정식 연구 완료가 아니다.

브리핑은 ‘목록에 무엇이 추가됐는지 → 실제 후보/검토 단위 → 확인할 이유의 예 → 실행·게시 검증 → 아직 판단할 수 없는 것’ 순서로 작성한다.
