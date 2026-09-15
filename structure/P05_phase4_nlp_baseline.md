# P05 · Phase 4 — 관련성 분류·사건 추출·표준화 NLP Baseline

> 문서 상태: 실행 설계 v1.0 / 기준일 2026-09-15. 설계와 작업 정의이며 연구 수행·구현·성능 달성 결과가 아닙니다.

[전체 목차](README.md) · [공통 데이터 규약](DATA_CONTRACTS.md) · [레퍼런스](REFERENCES.md) · [작업 인덱스](TASK_INDEX.md)

## 1. 이 단계에서 답할 질문

규칙과 가벼운 로컬 모델로 어디까지 정확하게 추출하며, 어떤 오류에만 더 복잡한 모델이 필요한가?

- **책임 역할:** C 실행·평가 공통, B 모델·사건 추출, A 숫자·지표 규칙·오류 검토
- **착수 조건:** P3 gold·split·가이드, P2 registry 고정. 원문 파서 오류는 추출 모델 오류와 구분.
- **범위:** 관련성→NER→사건·관계→지표 매핑의 개별 및 연결 benchmark. 고급 모델을 전부 구현하는 것이 목표는 아니며 단순 baseline 이후 개선 필요성을 검증한다.
- **연결 에픽:** [KAN-8](https://qyurimoon.atlassian.net/browse/KAN-8). 실명·기한은 팀이 배정하며 여기서는 역할 기준으로 작성합니다.

## 2. 반드시 남길 산출물

- `baseline_protocol.md / run_manifest.json`
- `predictions_<run_id>.jsonl / metrics.csv`
- `error_analysis.csv / model_selection.md`
- `extractor interface·검증 가능한 실행 코드(후속 구현 작업)`

산출물 경로는 저장소 루트의 `artifacts/p4/` 기준 제안입니다. 이 설계서 작성만으로 해당 데이터·코드가 생성된 것은 아닙니다. 원문·비공개 데이터는 P0에서 정한 보관 위치를 사용합니다.

## 3. 상세 설계와 판단 규칙

### 모델 비교 순서

M0: 사전·Regex·수치/단위/날짜 규칙. M1: 문서/문장 관련성 TF-IDF + Logistic Regression 또는 Linear SVM. M2: 사건 인자 CRF 또는 작은 한국어 encoder. M3: 필요할 때만 encoder relation extraction·embedding metric matching. M1 문서 분류와 M2 span extraction은 같은 과업의 점수인 것처럼 직접 비교하지 않는다. 각 stage의 공통 입력·출력과 전체 pipeline 성능을 함께 보고한다.

### 모델과 학습 데이터

설치 버전·모델 revision·tokenizer·라이선스·데이터 cutoff를 manifest로 고정한다. [R04/R05](REFERENCES.md)는 후보 연구 근거이며 즉시 채택 지시가 아니다. 100~300건으로 큰 모델을 fine-tuning하면 불안정할 수 있으므로 규칙·동결 encoder·간단 분류를 먼저 평가한다. 테스트를 반복 조회하며 규칙을 고치지 않는다. 사전·IDF·alias 확장도 train/dev에서만 만들고 테스트 기원 항목을 표시한다.

### 입력 보존과 span

document→block→sentence의 원문 위치 매핑을 보존한다. Unicode 정규화·공백 수정 전에 raw_text를 보존하고 offset mapping을 작성한다. 긴 문서의 chunk overlap에서 같은 인자를 중복 이벤트로 만들지 않는다. 표 머리글의 단위·기간·scope는 숫자 셀과 함께 추출한다. 숫자만 맞고 잘못된 행에 연결되면 실패다.

### 평가 단위

관련성 precision/recall/F1/AP, span exact F1와 relaxed F1(별도), 기업·metric top1/topk, 값·단위·기간 exact match, 사건 tuple 전체 정확도를 구분한다. 입력 후보에서 누락된 사건은 최종 pipeline FN에 포함한다. 조건부 추출 성능과 전체 입력 기준 성능을 나란히 제시한다. 원문 근거가 없는 예측은 사실 레코드로 통과시키지 않는다.

### 선택적 LLM 비교

API 호출은 optional backend로 설계한다. disabled 상태에서도 모든 입력에 결과/오류 레코드가 남아야 한다. dev에서 선정한 복합관계·미정 지표·낮은 confidence 유형에만 호출하는 정책을 비교한다. 입력 범위·모델 ID·prompt hash·응답·token·비용·실패를 기록하고 구조·근거를 검증한다. API 비용 실험을 실제 실행하려면 당시 사용 가능한 모델·단가·예산을 재확인한다. 문서는 특정 미검증 endpoint를 확정하지 않는다.

### 오류에 따른 다음 행동

파서 누락은 P0 보완, scope/단위는 규칙과 registry, 같은 사건 연결은 P1/P6, 모호한 gold는 P3 조정으로 보낸다. 모델 크기 증가가 모든 실패의 기본 대응은 아니다.

## 4. 실행 작업 — 순서와 완료 기준

아래 번호는 설계서 내부 ID입니다. 예: `P05-T01`은 Phase 4의 첫 작업입니다. `P0-T01`처럼 Phase로 쓴 의존성은 해당 Phase 설계서의 T01을 뜻합니다. 한 작업이 담당자 기준 1~2일보다 커지면 기업·자료형·사건유형 단위로 하위 작업을 나누고 같은 완료 조건을 적용합니다.

### P05-T01 · 실험 프로토콜·환경 고정

- **책임·검토:** C, B 검토
- **선행:** P3-T12
- **입력·참고:** T01,T02,split manifest

1. 과업별 입력·출력·metric을 정의한다.
2. 실행 환경·모델 후보·seed를 적는다.
3. train/dev/test 접근 원칙을 고정한다.
4. 하드웨어·시간·API 예산을 기록한다.

- **제출:** `baseline_protocol.md`
- **완료 확인:** 비교 대상과 test 공개 조건이 사전에 정의.
- **실패·미해결 처리:** 실패 입력/원문 위치·시도·원인·다음 확인 역할을 결과 기록에 남깁니다. 누락을 임의 값으로 채워 완료 처리하지 않습니다.

### P05-T02 · 파서·offset 연계 검사

- **책임·검토:** A, B 검토
- **선행:** T01,P0-T11
- **입력·참고:** blocks·gold evidence

1. 원문/정규화 텍스트 매핑을 검사한다.
2. 문장·chunk ID를 부여한다.
3. 표의 기간·단위 상속을 확인한다.
4. 잘못된 gold span과 파서 실패를 구분한다.

- **제출:** `preprocess_audit.csv`
- **완료 확인:** 근거 위치 왕복 검사에서 실패 유형 보고.
- **실패·미해결 처리:** 실패 입력/원문 위치·시도·원인·다음 확인 역할을 결과 기록에 남깁니다. 누락을 임의 값으로 채워 완료 처리하지 않습니다.

### P05-T03 · M0 사전·Regex baseline

- **책임·검토:** A, B 검토
- **선행:** T02
- **입력·참고:** P2 registry·train

1. 기업·제품 alias 사전을 만든다.
2. 수치·단위·기간·modality 규칙을 작성한다.
3. 한 문장 복수 숫자와 표 행열 매핑을 처리한다.
4. 원문 근거 없는 값은 abstain한다.

- **제출:** `rules_v1, predictions_m0.jsonl`
- **완료 확인:** 대표 성공·반례·unknown 입력을 검증.
- **실패·미해결 처리:** 실패 입력/원문 위치·시도·원인·다음 확인 역할을 결과 기록에 남깁니다. 누락을 임의 값으로 채워 완료 처리하지 않습니다.

### P05-T04 · 관련성 M1 구축

- **책임·검토:** B, C 검토
- **선행:** T02
- **입력·참고:** 관련/무관 문서 gold

1. train에서만 TF-IDF를 fit한다.
2. 간단 분류기를 학습한다.
3. dev에서 threshold와 class weighting을 비교한다.
4. 중요 사건이 필터에서 탈락한 사례를 기록한다.

- **제출:** `relevance_model, relevance_metrics.csv`
- **완료 확인:** 필터 후 성능과 전체 FN을 함께 보고.
- **실패·미해결 처리:** 실패 입력/원문 위치·시도·원인·다음 확인 역할을 결과 기록에 남깁니다. 누락을 임의 값으로 채워 완료 처리하지 않습니다.

### P05-T05 · span·사건 M2 후보 구현

- **책임·검토:** B, A 검토
- **선행:** T03,T04
- **입력·참고:** R02,R04·gold train

1. CRF 또는 한국어 encoder 후보를 비교 계획대로 선택한다.
2. BIO span과 숫자·기간 관계를 학습한다.
3. 긴 문서 chunk 및 overlap을 처리한다.
4. dev에서 복수 사건·부정·전망 오류를 분석한다.

- **제출:** `extractor_model, entity_predictions.jsonl`
- **완료 확인:** 문서 분류 점수와 사건 추출 점수를 혼합하지 않음.
- **실패·미해결 처리:** 실패 입력/원문 위치·시도·원인·다음 확인 역할을 결과 기록에 남깁니다. 누락을 임의 값으로 채워 완료 처리하지 않습니다.

### P05-T06 · metric 매핑·기업 범위 연결

- **책임·검토:** A, B 검토
- **선행:** T03,P2-T12
- **입력·참고:** alias registry·T04

1. exact alias 후보를 먼저 만든다.
2. scope·unit 불일치 후보를 제거한다.
3. 필요 시 embedding topk를 생성한다.
4. 불명확한 후보는 unresolved로 보존한다.

- **제출:** `normalization_predictions.jsonl`
- **완료 확인:** 모호한 alias를 확정 ID로 강제하지 않음.
- **실패·미해결 처리:** 실패 입력/원문 위치·시도·원인·다음 확인 역할을 결과 기록에 남깁니다. 누락을 임의 값으로 채워 완료 처리하지 않습니다.

### P05-T07 · 입출력 검증 인터페이스

- **책임·검토:** C, A 검토
- **선행:** T05,T06
- **입력·참고:** DATA_CONTRACTS,T07

1. 공통 EventCandidate 응답을 정의한다.
2. raw/normalized/evidence/confidence를 분리한다.
3. 잘못된 타입·비어 있는 근거를 격리한다.
4. 모델 실패를 missing prediction 로그로 남긴다.

- **제출:** `schemas·validation_report.md`
- **완료 확인:** 실패 레코드도 입력 ID로 추적.
- **실패·미해결 처리:** 실패 입력/원문 위치·시도·원인·다음 확인 역할을 결과 기록에 남깁니다. 누락을 임의 값으로 채워 완료 처리하지 않습니다.

### P05-T08 · dev 비교·오류 분류

- **책임·검토:** A/B, C 집계
- **선행:** T07
- **입력·참고:** T01,dev predictions

1. stage별 metric과 전체 tuple을 계산한다.
2. 기업·유형·문서형식별 오류를 분리한다.
3. FN/FP의 원문과 예측을 비교한다.
4. 작은 데이터에서 seed 변동을 보고한다.

- **제출:** `dev_benchmark.md, error_analysis.csv`
- **완료 확인:** 단계 간 다른 과업을 같은 metric으로 비교하지 않음.
- **실패·미해결 처리:** 실패 입력/원문 위치·시도·원인·다음 확인 역할을 결과 기록에 남깁니다. 누락을 임의 값으로 채워 완료 처리하지 않습니다.

### P05-T09 · confidence·fallback 정책 시험

- **책임·검토:** C, B 구현/A 검토
- **선행:** T08
- **입력·참고:** T03,dev 오류·예산

1. confidence의 근거를 점수/보정 확률/규칙으로 구분한다.
2. API 미사용 정책을 기본 비교군에 둔다.
3. 선택적 호출 조건·상한·실패 대체를 고정한다.
4. LLM 결과도 근거·스키마 검증을 통과시킨다.

- **제출:** `fallback_policy.md, cost_log.jsonl`
- **완료 확인:** 테스트 데이터로 threshold를 조정하지 않음.
- **실패·미해결 처리:** 실패 입력/원문 위치·시도·원인·다음 확인 역할을 결과 기록에 남깁니다. 누락을 임의 값으로 채워 완료 처리하지 않습니다.

### P05-T10 · 고정 모델 test 실행

- **책임·검토:** C, A/B 검토
- **선행:** T09
- **입력·참고:** 고정 모델·test manifest

1. 모델·사전·prompt·threshold를 고정한다.
2. test를 한 번 계획대로 평가한다.
3. 처리 실패도 분모에 포함한다.
4. 가중치·버전·결과 hash를 저장한다.

- **제출:** `test_benchmark.md`
- **완료 확인:** test 확인 후 수정 모델은 새 버전과 새 평가 계획 필요.
- **실패·미해결 처리:** 실패 입력/원문 위치·시도·원인·다음 확인 역할을 결과 기록에 남깁니다. 누락을 임의 값으로 채워 완료 처리하지 않습니다.

### P05-T11 · 오류 보완·인계 결정

- **책임·검토:** C, 전원
- **선행:** T10
- **입력·참고:** benchmark·원문 사례

1. 성능·비용·재현성을 비교해 기본 모델을 선택한다.
2. 파서/정의/라벨/모델 문제를 담당 단계로 보낸다.
3. P5/P6가 받을 예측 필드와 confidence를 확정한다.
4. 추가 모델이 불필요한 경우 그 이유를 남긴다.

- **제출:** `model_selection.md, handoff_p4.md`
- **완료 확인:** 선정 이유와 알려진 실패 유형이 결과로 연결.
- **실패·미해결 처리:** 실패 입력/원문 위치·시도·원인·다음 확인 역할을 결과 기록에 남깁니다. 누락을 임의 값으로 채워 완료 처리하지 않습니다.


## 5. 필수 검증 시나리오

- [ ] 문서 머리글의 단위와 다른 행의 숫자를 연결하면 실패 처리한다.
- [ ] 원문 공백 정규화 후에도 evidence span을 복원한다.
- [ ] 같은 문장 복수 회사·지표가 서로 잘못 연결되지 않는다.
- [ ] LLM 미사용·timeout·schema 오류 입력에서도 pipeline 추적이 유지된다.

## 6. 단계 종료와 다음 단계 전달

**종료 기준:** 공통 benchmark에서 최소 규칙 baseline과 관련 과업의 학습 baseline을 비교하고 선택 근거·오류·재현 설정을 남겼다. 성능이 낮으면 범위·데이터·가이드를 보완하며 모델 학습 자체를 성공 결과로 쓰지 않는다.

**인계:** P5에는 추출 불확실성을 포함한 features, P6에는 근거가 연결된 표준 사건 후보, P7에는 버전 고정 extractor interface.

결과 기록에는 완료 작업 ID, 산출물 경로·버전·hash, 실제 건수, 검증 결과, 검토 역할, 남은 문제와 후속 작업을 남깁니다. 미실행 검증을 통과로 표시하지 않습니다. 성능 목표·예산·표본 수 변경은 [결정 기록](DECISIONS.md)에 남깁니다.

## 7. 이 단계의 레퍼런스

- **R02 · [Zheng et al. (2019), Doc2EDAG](https://aclanthology.org/D19-1032/)** — 문서 단위 사건·분산된 인자·여러 사건의 표현 설계. 확인 수준: 서지·초록 확인; 중국어 자료 성능을 한국어 예상 성능으로 사용 금지.
- **R04 · [Park et al. (2021), KLUE](https://arxiv.org/abs/2105.09680)** — 한국어 NER·RE 평가 방식·모델 후보 조사. 확인 수준: 서지·초록 확인; 금융 사건 전용 gold와 별도.
- **R05 · [Yang et al. (2020), FinBERT](https://arxiv.org/abs/2006.08097)** — 금융 도메인 적응의 비교 후보와 한계. 확인 수준: 서지·초록 확인; 영어 금융 모델을 한국어 정답기로 쓰지 않음.
- **R06 · [Reimers & Gurevych (2019), Sentence-BERT](https://aclanthology.org/D19-1410/)** — 문장 임베딩 후보·유사도 검색의 역할. 확인 수준: 서지·초록 확인; 유사도는 같은 사건의 증거가 아님.
- **T01 · [scikit-learn model evaluation](https://scikit-learn.org/stable/modules/model_evaluation.html)** — 각 metric의 분모·평균 방식·undefined 조건 확인. 확인 수준: 공식 문서 확인; 설치 버전과 문서 버전 맞추기.
- **T02 · [scikit-learn cross validation](https://scikit-learn.org/stable/modules/cross_validation.html)** — 시간 분리·그룹 분리·누수 방지 평가 설계. 확인 수준: 공식 문서 확인; 일반 TimeSeriesSplit만으로 사건 묶음 분리가 보장되지 않음.
- **T03 · [scikit-learn calibration](https://scikit-learn.org/stable/modules/calibration.html)** — 보정 곡선·확률 평가·별도 보정 데이터 운영. 확인 수준: 공식 문서 확인; 낮은 Brier만으로 보정 품질 단정 금지.
- **T04 · [Sentence Transformers STS](https://www.sbert.net/docs/sentence_transformer/usage/semantic_textual_similarity.html)** — 임베딩·유사도 구현 후보. 확인 수준: 공식 문서 확인; 한국어·금융 적합성은 자체 평가.
- **T07 · [Pydantic Models](https://pydantic.dev/docs/validation/latest/concepts/models/)** — 입출력 스키마·누락·타입 오류 검증 후보. 확인 수준: 공식 문서 확인; 강제 형변환과 엄격 검증을 구별.

문헌·API를 실제 작업에 사용한 뒤 읽은 절·페이지·버전·실행일을 기록합니다. 확인한 개요와 아직 정독하지 않은 본문을 구별합니다.

