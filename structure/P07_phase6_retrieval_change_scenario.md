# P07 · Phase 6 — Prior-state 검색·변화 탐지·정량 시나리오 엔진

> 문서 상태: 실행 설계 v1.0 / 기준일 2026-09-15. 설계와 작업 정의이며 연구 수행·구현·성능 달성 결과가 아닙니다.

[전체 목차](README.md) · [공통 데이터 규약](DATA_CONTRACTS.md) · [레퍼런스](REFERENCES.md) · [작업 인덱스](TASK_INDEX.md)

## 1. 이 단계에서 답할 질문

발표 직전까지 알려진 상태를 근거와 함께 찾고, 비교 가능한 변화만 계산하며, 필요한 가정이 없을 때 계산을 멈출 수 있는가?

- **책임 역할:** B 검색·event store, A 단위·변화·수식, C 시점·통합 검증
- **착수 조건:** P2 registry·비교 규칙, P3 검색용 사례, P4 EventCandidate. P5 최종 순위 모델 없이도 검색·변화 엔진은 개발 가능.
- **범위:** event store·historical snapshot·hybrid retrieval·delta·조건부 scenario. 미래 정보를 포함한 최신 요약을 과거 상태로 대체하지 않는다.
- **연결 에픽:** [KAN-10](https://qyurimoon.atlassian.net/browse/KAN-10). 실명·기한은 팀이 배정하며 여기서는 역할 기준으로 작성합니다.

## 2. 반드시 남길 산출물

- `event_store schema / asof_queries.sql`
- `retrieval_qrels.csv / retrieval_benchmark.md`
- `change_records.jsonl / calculation_registry.csv`
- `scenario_runs.jsonl / reproducibility_report.md`

산출물 경로는 저장소 루트의 `artifacts/p6/` 기준 제안입니다. 이 설계서 작성만으로 해당 데이터·코드가 생성된 것은 아닙니다. 원문·비공개 데이터는 P0에서 정한 보관 위치를 사용합니다.

## 3. 상세 설계와 판단 규칙

### 저장 모델과 시점

raw document, claim/event mention, event relation, metric registry, prior-state candidate, change record, scenario run을 별도 테이블로 둔다. 각 claim은 published_at(공개), effective_period(적용), observed_at(시스템 수집), revision 관계를 갖는다. 현재 수정된 행 한 개만 보관하면 과거 상태를 복원할 수 없으므로 append-only revision을 권장한다.

백테스트에는 historical-public 모드와 observed-live 모드를 구분한다. historical-public은 당시 공개된 원문을 뒤늦게 수집했어도 사용할 수 있으나 공개시점 근거가 필요하다. observed-live는 실제 시스템 관측시점도 cutoff 이하여야 한다. 날짜만 있고 시각이 불명확하면 같은 날짜 문서를 순서가 확인된 과거 근거로 쓰지 않거나 보수적 정책을 적용한다. 정책 이름을 run manifest에 적는다.

### Retrieval 파이프라인

기업·scope·metric·기간·공개시점 필터 → BM25 희소 검색 → embedding 검색 → 후보 합치기 → 재순위화 → 호환성 검사 순서의 후보 설계다. 희소 검색과 dense 검색 각각을 baseline으로 평가한다. [T05](REFERENCES.md)의 FTS5는 후보 구현이며 한국어 토큰화·수치 표현을 검증해야 한다. 단순 유사도 최고 문서가 prior-state 정답은 아니다.

query는 새 사건, qrels는 그 이전에 공개된 비교 가능한 주장과 근거 위치다. 정답 없음도 포함한다. 같은 문서 내 ‘전년 수치’는 신규 발표에서 회고한 값이지 독립적으로 당시 알려졌음을 보장하는 자료가 아니다. backtest prior에는 이전 공개 원문 또는 당시 version evidence를 요구한다.

### Change 종류와 abstention

new_information, repeated, numeric_revision, certainty_transition, effective_date_change, correction, contradiction_candidate, prior_not_found, not_comparable를 구분한다. 하나의 사건에 여러 change가 가능하면 배열로 둔다. 부인과 정정, 계획→실행을 단순 숫자 차분에 넣지 않는다. 서로 다른 출처 주장 충돌은 확정 정정으로 처리하지 않고 근거를 나란히 보여준다.

동일 정의·범위·기간의 v_old와 v_new만 delta=v_new-v_old를 계산한다. relative delta=delta/abs(v_old)는 분모 정의를 명시하고 0이면 unavailable 처리한다. % 비중의 차는 percentage points로 보존한다. 음수 기준값은 해석을 따로 명시하고 손실→이익을 단순 성장률로 과장하지 않는다. 누적→분기 값은 기간·회계범위·정정본이 호환될 때만 차분한다.

### Scenario 식과 한계

검증 가능한 수식 ID만 실행한다. 출하량×ASP=매출은 제품·기간·통화·단위 일치가 필요하다. 생산능력×가동률은 생산량 후보이며 출하량 계산에는 수율·재고·제품 mix 가정이 추가될 수 있다. 입력이 없으면 공식/시나리오만 표시하고 숫자 결과를 생성하지 않는다.

시나리오의 low/base/high 입력은 분석 가정이며 통계적 신뢰구간과 다르다. 입력 출처·관측/가정·버전·환율·반올림을 기록하고 [T06](REFERENCES.md)의 Decimal 같은 명시적 계산으로 재현한다. LLM은 산술의 권위가 되지 않는다. 계산 결과를 실제 회사 전망으로 표현하지 않는다.

## 4. 실행 작업 — 순서와 완료 기준

아래 번호는 설계서 내부 ID입니다. 예: `P07-T01`은 Phase 6의 첫 작업입니다. `P0-T01`처럼 Phase로 쓴 의존성은 해당 Phase 설계서의 T01을 뜻합니다. 한 작업이 담당자 기준 1~2일보다 커지면 기업·자료형·사건유형 단위로 하위 작업을 나누고 같은 완료 조건을 적용합니다.

### P07-T01 · store 스키마·키 정의

- **책임·검토:** B, C 검토
- **선행:** P2-T12,P4-T11
- **입력·참고:** DATA_CONTRACTS,O03

1. 문서·claim·revision·relation 테이블을 정의한다.
2. stable ID와 unique 제약을 정한다.
3. 공개/적용/관측 시점을 나눈다.
4. 외래키·원문 위치를 검사하는 마이그레이션을 설계한다.

- **제출:** `event_store_schema.sql`
- **완료 확인:** 과거 claim이 새 정정으로 덮어써지지 않음.
- **실패·미해결 처리:** 실패 입력/원문 위치·시도·원인·다음 확인 역할을 결과 기록에 남깁니다. 누락을 임의 값으로 채워 완료 처리하지 않습니다.

### P07-T02 · as-of 정책 구현

- **책임·검토:** B, C 검토
- **선행:** T01
- **입력·참고:** 공개시점·정정 원문

1. historical-public/observed-live 정책을 구현한다.
2. cutoff보다 늦은 문서를 제외한다.
3. 날짜만 있는 같은 날 자료 정책을 적용한다.
4. 정정 전후 snapshot을 재현한다.

- **제출:** `asof_queries.sql`
- **완료 확인:** 미래 자료 추가 후 과거 query 결과가 변하지 않음.
- **실패·미해결 처리:** 실패 입력/원문 위치·시도·원인·다음 확인 역할을 결과 기록에 남깁니다. 누락을 임의 값으로 채워 완료 처리하지 않습니다.

### P07-T03 · 검색용 query·qrels 작성

- **책임·검토:** A/B, C 조정
- **선행:** T02,P3-T12
- **입력·참고:** 이전·신규 발표 쌍

1. 새 사건별 이전 근거 후보를 찾는다.
2. 정답/부분 관련/부적합/정답 없음 기준을 작성한다.
3. 기업·기간·scope 불일치 hard negative를 넣는다.
4. train/dev/test query family를 분리한다.

- **제출:** `retrieval_qrels.csv`
- **완료 확인:** 정답 없음과 검색 실패를 구분 가능.
- **실패·미해결 처리:** 실패 입력/원문 위치·시도·원인·다음 확인 역할을 결과 기록에 남깁니다. 누락을 임의 값으로 채워 완료 처리하지 않습니다.

### P07-T04 · 희소 검색 baseline

- **책임·검토:** B, A 검토
- **선행:** T03
- **입력·참고:** T05·qrels

1. block 단위 인덱스를 만든다.
2. 기업·시점 필터를 적용한다.
3. 한국어·숫자·단위 토큰화를 비교한다.
4. BM25 topk와 latency를 저장한다.

- **제출:** `bm25_results.jsonl`
- **완료 확인:** 관련 수치가 다른 기간이면 false hit로 평가.
- **실패·미해결 처리:** 실패 입력/원문 위치·시도·원인·다음 확인 역할을 결과 기록에 남깁니다. 누락을 임의 값으로 채워 완료 처리하지 않습니다.

### P07-T05 · dense·hybrid 후보 비교

- **책임·검토:** B, C 검토
- **선행:** T04
- **입력·참고:** R06,R07,T04

1. 고정 embedding 모델로 후보를 생성한다.
2. BM25와 rank 기반 fusion을 비교한다.
3. 필요한 경우 작은 reranker를 추가한다.
4. dev에서 topk·fusion·latency를 선택한다.

- **제출:** `retrieval_benchmark.md`
- **완료 확인:** 같은 corpus·qrels·cutoff로 비교.
- **실패·미해결 처리:** 실패 입력/원문 위치·시도·원인·다음 확인 역할을 결과 기록에 남깁니다. 누락을 임의 값으로 채워 완료 처리하지 않습니다.

### P07-T06 · 호환성 검사·prior 선택

- **책임·검토:** A, B 구현/C 검토
- **선행:** T05
- **입력·참고:** P2 comparability

1. scope·제품·기간·정의·unit을 검사한다.
2. 부적합 후보에 이유를 붙인다.
3. 복수 적합 주장과 최신 공개순을 보존한다.
4. 정답 근거 없으면 abstain한다.

- **제출:** `prior_state_records.jsonl`
- **완료 확인:** 유사도만으로 prior를 확정하지 않음.
- **실패·미해결 처리:** 실패 입력/원문 위치·시도·원인·다음 확인 역할을 결과 기록에 남깁니다. 누락을 임의 값으로 채워 완료 처리하지 않습니다.

### P07-T07 · 숫자 delta 구현

- **책임·검토:** A, C 검토
- **선행:** T06
- **입력·참고:** T06·P2 unit rules

1. 절대차·비율·%p의 식 ID를 정한다.
2. 0·음수·범위값·누적차분 조건을 처리한다.
3. 원값·변환값·결과·반올림을 저장한다.
4. 호환 불가면 결과 없이 이유를 반환한다.

- **제출:** `numeric_changes.jsonl`
- **완료 확인:** 모든 계산에 입력 두 값·단위·기간·공식 추적.
- **실패·미해결 처리:** 실패 입력/원문 위치·시도·원인·다음 확인 역할을 결과 기록에 남깁니다. 누락을 임의 값으로 채워 완료 처리하지 않습니다.

### P07-T08 · 정성·revision change 구현

- **책임·검토:** B, A 검토
- **선행:** T06
- **입력·참고:** P1 관계규칙

1. 계획/실행·시점 변경·부인·정정을 분류한다.
2. 같은 발표 반복과 새로운 상태를 구별한다.
3. 출하/판매를 원문 동작으로 보존한다.
4. 충돌은 contradiction candidate로 남긴다.

- **제출:** `qualitative_changes.jsonl`
- **완료 확인:** 근거 없는 확정·상향·동일 사건 병합 없음.
- **실패·미해결 처리:** 실패 입력/원문 위치·시도·원인·다음 확인 역할을 결과 기록에 남깁니다. 누락을 임의 값으로 채워 완료 처리하지 않습니다.

### P07-T09 · 계산 공식·가정 등록

- **책임·검토:** A, C 검토
- **선행:** T07,P2-T08
- **입력·참고:** driver_edges·T06

1. 계산 가능한 edge만 formula로 선택한다.
2. 입력 단위·기간·허용범위·추가가정을 정의한다.
3. missing input 시 중단 정책을 작성한다.
4. 관측값과 분석가 가정 필드를 분리한다.

- **제출:** `calculation_registry.csv`
- **완료 확인:** 생산능력 증가율을 매출 증가율로 바로 사용하지 않음.
- **실패·미해결 처리:** 실패 입력/원문 위치·시도·원인·다음 확인 역할을 결과 기록에 남깁니다. 누락을 임의 값으로 채워 완료 처리하지 않습니다.

### P07-T10 · change interface·평가 고정

- **책임·검토:** C, A/B 검토
- **선행:** T07,T08
- **입력·참고:** qrels·gold change 사례

1. change 종류별 정확도·abstention을 계산한다.
2. prior 검색 오차와 change 오차를 분리한다.
3. P5용 feature의 available_at을 점검한다.
4. 고정 interface와 버전을 전달한다.

- **제출:** `change_benchmark.md, change_schema.json`
- **완료 확인:** P5-T10에 미래 정보 없는 변화 feature 제공.
- **실패·미해결 처리:** 실패 입력/원문 위치·시도·원인·다음 확인 역할을 결과 기록에 남깁니다. 누락을 임의 값으로 채워 완료 처리하지 않습니다.

### P07-T11 · scenario 실행·재현

- **책임·검토:** A, B 검토
- **선행:** T09,T10
- **입력·참고:** 공식·입력·가정

1. base/low/high 입력 세트를 만든다.
2. Decimal·통화·반올림 정책으로 실행한다.
3. 입력/공식/hash로 결과를 재실행한다.
4. 가정 민감도와 계산 불가 사례를 저장한다.

- **제출:** `scenario_runs.jsonl`
- **완료 확인:** 동일 입력·버전 재실행에서 같은 결과.
- **실패·미해결 처리:** 실패 입력/원문 위치·시도·원인·다음 확인 역할을 결과 기록에 남깁니다. 누락을 임의 값으로 채워 완료 처리하지 않습니다.

### P07-T12 · 전체 엔진 검증·인계

- **책임·검토:** C, 전원
- **선행:** T11
- **입력·참고:** store·검색·change·scenario

1. 미래문서·정정·미상시각·0분모 반례를 실행한다.
2. 카드용 prior/new evidence를 묶는다.
3. 필수 입력 누락시 표시할 이유를 확정한다.
4. 성능·실패·재현 결과를 정리한다.

- **제출:** `handoff_p6.md`
- **완료 확인:** 모든 카드용 변화·계산이 원문과 조건으로 추적 가능.
- **실패·미해결 처리:** 실패 입력/원문 위치·시도·원인·다음 확인 역할을 결과 기록에 남깁니다. 누락을 임의 값으로 채워 완료 처리하지 않습니다.


## 5. 필수 검증 시나리오

- [ ] cutoff 이후 정정본을 넣어도 이전 시점 결과는 유지된다.
- [ ] 같은 지표명이어도 scope·period가 다르면 계산을 거부한다.
- [ ] 0분모·통화 불일치·단위 미상은 숫자 결과를 반환하지 않는다.
- [ ] 계획→실행을 수치 증가로 변환하지 않는다.
- [ ] 생산능력만 있는 입력에서 출하·매출을 확정 계산하지 않는다.

## 6. 단계 종료와 다음 단계 전달

**종료 기준:** time-safe prior retrieval과 근거 연결 change가 재현되며 계산 가능한 경우만 수식·가정과 함께 결과를 낸다. 검색 정확도·정답 없음·불가율·계산 오류를 함께 보고한다.

**인계:** P5 후속 특성 비교에 change를 전달하고 P7에 prior/new evidence·변화·계산·불확실성 인터페이스를 전달한다.

결과 기록에는 완료 작업 ID, 산출물 경로·버전·hash, 실제 건수, 검증 결과, 검토 역할, 남은 문제와 후속 작업을 남깁니다. 미실행 검증을 통과로 표시하지 않습니다. 성능 목표·예산·표본 수 변경은 [결정 기록](DECISIONS.md)에 남깁니다.

## 7. 이 단계의 레퍼런스

- **N01 · [최신 Notion 프로젝트](https://app.notion.com/p/3d00589711408057948dc5666ae044e3)** — 개요 및 설명의 RQ1~5, 모듈7.1~7.11, Phase0~8, 기업 선정. 확인 수준: 2026-09-15 본문 확인; 보관 초안보다 우선.
- **R06 · [Reimers & Gurevych (2019), Sentence-BERT](https://aclanthology.org/D19-1410/)** — 문장 임베딩 후보·유사도 검색의 역할. 확인 수준: 서지·초록 확인; 유사도는 같은 사건의 증거가 아님.
- **R07 · [Thakur et al. (2021), BEIR](https://arxiv.org/abs/2104.08663)** — 희소/밀집 검색 비교와 다른 도메인 평가 설계. 확인 수준: 서지·초록 확인; 우리 금융 prior-state 검색을 따로 평가.
- **R08 · [Chen et al. (2021), FinQA](https://aclanthology.org/2021.emnlp-main.300/)** — 표·문장 근거와 계산 프로그램 연결 방식. 확인 수준: 서지·초록 확인; 데이터셋 전체 재배포 권한은 별도 확인.
- **O03 · [W3C PROV-O](https://www.w3.org/TR/prov-o/)** — 원문→추출→수정→계산의 출처·행위·작성 주체 연결. 확인 수준: 공식 표준 확인; v1은 관계형 기록으로 구현 가능.
- **T04 · [Sentence Transformers STS](https://www.sbert.net/docs/sentence_transformer/usage/semantic_textual_similarity.html)** — 임베딩·유사도 구현 후보. 확인 수준: 공식 문서 확인; 한국어·금융 적합성은 자체 평가.
- **T05 · [SQLite FTS5](https://www.sqlite.org/fts5.html)** — 희소 검색·BM25·인덱스·토큰화 설계. 확인 수준: 공식 문서 확인; 한국어 토큰화 별도 검증.
- **T06 · [Python decimal](https://docs.python.org/3/library/decimal.html)** — 금액·비율 계산의 정밀도와 반올림 규칙. 확인 수준: 공식 문서 확인; 입력 문자열·정밀도·반올림 설정 보존.
- **T07 · [Pydantic Models](https://pydantic.dev/docs/validation/latest/concepts/models/)** — 입출력 스키마·누락·타입 오류 검증 후보. 확인 수준: 공식 문서 확인; 강제 형변환과 엄격 검증을 구별.
- **C01 · [삼성 2025Q4 IR](https://images.samsung.com/kdp/ir/events/2025/2025_4Q_conference_kor.pdf)** — 메모리 전망·HBM4 양산 출하 계획, 메모리 매출/DS 이익 범위 구분. 확인 수준: PDF 본문 확인.
- **C02 · [삼성 2026Q1 IR](https://images.samsung.com/kdp/ir/events/2026/2026_1Q_conference_kor.pdf)** — HBM4 양산 판매 개시, 이전 계획과 후속 실행 연결. 확인 수준: PDF 본문 확인.

문헌·API를 실제 작업에 사용한 뒤 읽은 절·페이지·버전·실행일을 기록합니다. 확인한 개요와 아직 정독하지 않은 본문을 구별합니다.

