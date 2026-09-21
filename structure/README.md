# 기업리서치 반자동화 — 단계별 상세 설계

기준일: **2026-09-15** / 설계 v1.0

[최신 Notion 프로젝트](https://app.notion.com/p/3d00589711408057948dc5666ae044e3)와 [회의1](https://app.notion.com/p/3d505897114080558acfdcf184982330)을 기준으로 작성했습니다. 보관된 이전 상세기획서의 단계 번호는 사용하지 않습니다.

## 가장 먼저 읽을 내용

**삼성전자 메모리 사업·SK하이닉스로 P0·P1·P2의 자료·사건·지표 기준을 만들고, 리노공업·ISC에 소표본으로 적용한 뒤 P3~P8로 확장합니다.** 기업2곳은 같은 질문·기록 체계를 비교하기 위한 범위이며 팀원3명에 맞춰 기업3곳을 강제하지 않습니다.

이 폴더는 **설계서**입니다. 현재 103개 작업을 정의했으며 실행·라벨링·모델 학습·성능 달성을 의미하지 않습니다. 실제 데이터·코드·결과 파일은 각 단계에서 만들도록 구체적으로 명시했습니다. 성능·예산·최종 모델은 해당 연구 결과로 정합니다.

## 파일명과 Phase 번호

사용자가 요청한 문서 번호 P01부터 시작합니다. **P01 파일=Phase 0, P02 파일=Phase 1, …, P09 파일=Phase 8**입니다. 기존 Notion/Jira Phase 번호를 하나씩 밀어 바꾼 것이 아니라 문서 순번과 Phase 번호를 모두 표기한 것입니다.

| 설계서 | 최신 기획 단계 | 핵심 산출물 | 세부 작업 |
| --- | --- | --- | --- |
| [P01 · 데이터 가능성 조사](P01_phase0_data_feasibility.md) | Phase 0 | source_registry.csv: 출처별 접근·저장·재배포 조건과 근거 | 11개 |
| [P02 · 선행연구 및 개념·사건 양식 설계](P02_phase1_research_and_schema.md) | Phase 1 | literature_matrix.csv 및 research_map.md | 11개 |
| [P03 · Metric Ontology와 기업 간 적용 검증](P03_phase2_metric_ontology.md) | Phase 2 | metric_occurrences.csv / metric_catalog.csv | 12개 |
| [P04 · Annotation Pilot과 평가 데이터 설계](P04_phase3_annotation_pilot.md) | Phase 3 | annotation_guide_v1.md / annotation_assignments.csv | 12개 |
| [P05 · 관련성 분류·사건 추출·표준화 NLP Baseline](P05_phase4_nlp_baseline.md) | Phase 4 | baseline_protocol.md / run_manifest.json | 11개 |
| [P06 · Materiality 표현 연구와 검토 우선순위 모델](P06_phase5_materiality_modeling.md) | Phase 5 | materiality_protocol.md / representation_comparison.csv | 11개 |
| [P07 · Prior-state 검색·변화 탐지·정량 시나리오 엔진](P07_phase6_retrieval_change_scenario.md) | Phase 6 | event_store schema / asof_queries.sql | 12개 |
| [P08 · Review Card 시스템 통합과 피드백](P08_phase7_system_integration.md) | Phase 7 | pipeline_spec.md / run_config.yaml / run_manifest.json | 11개 |
| [P09 · 비교 실험·검토 효용·최종 보고서](P09_phase8_comparative_evaluation.md) | Phase 8 | evaluation_protocol.md / frozen_run_manifest.json | 12개 |

## 함께 사용할 문서

- [TASK_INDEX.md](TASK_INDEX.md): 103개 작업의 책임·선행·제출물과 실행 흐름.
- [DATA_CONTRACTS.md](DATA_CONTRACTS.md): 공통 ID·값·단위·시점·근거·라벨·검색·계산·피드백 필드.
- [REFERENCES.md](REFERENCES.md): 사용한 모든 참고자료의 링크·용도·확인 수준. 원문 미독·접근 실패도 표시.
- [P01_news_article_classification_design.md](P01_news_article_classification_design.md): 국내 기업뉴스의 기사 선정, 장르·전재·사건 관계 분류, 동일 사건·동일 사실의 표현 비교 설계.
- [DECISIONS.md](DECISIONS.md): 현재 실행 기준과 연구 후 정할 항목, 변경 기록 양식.

## 자료 범위

- 주 대상: 삼성전자 **메모리**와 SK하이닉스. 메모리·DS·전사를 다른 scope로 저장.
- 기간: **2024Q1~2026Q2**, 기업별10개 분기.
- 최초 접근 시험: 기업별 연속2분기 IR+사업보고서1개, 총6개.
- 이후: 정기보고서·IR을 전체 기간으로 확장하고 관련 공식 제품·투자 발표·공개 Q&A 연결.
- 한국어를 기본으로 사용. 영문은 보조자료이며 같은 발표의 중복을 표시.
- P2 메모리 검토: 동일 사건5~10개를 세 사람이 독립 작성.
- 후속 적용: 리노공업·ISC 같은 기간 연속2분기 자료에서 기업별3개 사건. **설계 수정용 adaptation**이며 독립 test가 아님.
- P3: 100~300개 사건 pilot. 문서 수·사건 수·독립 사건 family 수는 따로 집계.

## 3명 역할

| 역할 | 초기 책임 | 후속 책임 | 검토 |
| --- | --- | --- | --- |
| A | 삼성 자료·지표 후보·산업 정의 | 리노공업 적용·숫자/단위·계산·도메인 오류 | B 기업 원문을 교차 검토 |
| B | SK하이닉스 자료·사건 문헌·별칭 비교 | ISC 적용·NLP·검색·실험 재현 | A 기업 원문을 교차 검토 |
| C | 자료 관리 기준·중요성 문헌·사건 스키마 | gold 조정·평가 설계·통합·보고 | A/B 결과 통합, 자기 작성물은 A/B 검토 |

실명·기한은 회의에서 연결합니다. P4 이후 역할은 위 전문 영역을 기준으로 한 실행 제안이며 실제 역량·가용시간에 따라 작업별로 조정합니다. C에게 수집·라벨링·구현을 전부 몰지 않고 A/B가 원문 검증과 실행을 분담합니다.

## 실행 순서와 병행

1. Phase0 범위·최초 자료 시험과 Phase1 문헌 탐색은 병행.
2. P0의 실제 표본+P1 기준으로 P2 지표 registry 작성.
3. 메모리 공동 기록→기준 고정→리노/ISC adaptation→P3 가이드와 gold 확정.
4. P4 NLP baseline과 P6 event store 준비는 공통 contract로 병행 가능. P6 실제 예측 연결은 P4 interface 필요.
5. P5는 변화 특성 없는 baseline부터 시작. P6의 change interface가 나오면 P5 추가 feature 비교를 수행.
6. P4/P5/P6 고정 결과를 P7에서 연결.
7. P8은 test 열기 전 목표·비교군·설정을 고정한 뒤 시행.

**의존성 주의:** P5 최종 모델을 기다려야 P6를 시작하는 것은 아닙니다. P6 결과가 P5의 후속 비교 입력으로 들어갑니다. 이 관계를 작업별 선행 조건에 분리했습니다.

## 오늘 시작할 구체적인 작업

- A/B: P01-T01~T05에서 자기 기업의 접근 시험3개 문서를 등록하고 원문 위치·기간·scope를 적습니다.
- C: 같은 manifest 양식·출처 조건표를 만들고 P02-T01 검색 계획과 P02-T03 중요성 문헌을 시작합니다.
- B: P02-T02 사건 문헌을, A: P02-T04 지표 문헌을 병행합니다.
- 첫 점검에서는 링크 목록보다 **실제 작성한 문서1행·사건1행·문헌 비교1행**을 열어 검토합니다.

## 작업 운영 원칙

작업을 Jira로 옮길 때는 이 문서의 ID·목적·실행 순서·산출물·완료 기준·선행을 복사합니다. 예: `P03-T06 · 단위·기간 변환표 작성`. 이 폴더를 만들면서 Jira 이슈나 상태를 변경하지 않았습니다.

각 작업 결과에는 실행일, 실제 수행자, 입력·출력 버전, 검증 결과, 미해결 문제, 검토자를 적습니다. 예상과 다른 결과도 정리하면 연구 결과가 될 수 있습니다. 미실행과 실패는 완료와 구별합니다.

## 공통 설계 제약

- 과거 시점 비교에서 미래 정정·후속 실적·사후 주가를 사용하지 않습니다.
- 미상·미공개를0으로 채우지 않습니다.
- 메모리 매출과 DS 영업이익을 같은 사업 손익으로 계산하지 않습니다.
- 생산능력×가동률을 무조건 출하량으로 치환하지 않습니다.
- P2에서 읽고 기준을 고친 리노/ISC 사례는 깨끗한 기업 holdout이 아닙니다.
- 100~300개 사건·팀원3명의 결과는 표본 한계를 함께 보고합니다.
- 원문·LLM 출력은 검증 대상이며 실행 지시로 처리하지 않습니다.
- 라이브러리·모델·API·가격·사용조건은 실제 구현 시점에 공식 문서로 다시 확인하고 버전을 고정합니다.

## 검토 순서

먼저 DATA_CONTRACTS의 회사범위·시점·누락 규칙을 확인하고, 담당 Phase의 작업을 읽습니다. 단계가 끝날 때 산출물·원문·검증 결과를 연결해 다음 담당자가 재현할 수 있는지 확인합니다. 설계 변경은 DECISIONS에 기록하고 영향을 받는 Phase와 contract를 함께 업데이트합니다.
