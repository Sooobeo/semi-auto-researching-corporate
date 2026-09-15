# 실행 작업 인덱스

총 **103개 작업**. 문서 순번 P01~P09와 Notion Phase 0~8을 구분합니다. 선행에 적힌 `P0-T01`은 Phase 0의 T01, 즉 `P01-T01`을 뜻합니다. 같은 단계의 `T01`은 해당 파일 안의 작업입니다. 상태·실명·기한은 실행 도구에서 정하며 이 표는 완료 내역이 아닙니다.

## P01 / Phase 0 — 데이터 가능성 조사

[상세 설계](P01_phase0_data_feasibility.md)

| ID | 할 일 | 책임·검토 | 선행 | 제출 |
| --- | --- | --- | --- | --- |
| P01-T01 | 범위표·역할·저장 위치 고정 | C | 없음 | scope.md, coverage_matrix.csv |
| P01-T02 | 기업 식별자 확인 | A/B, C 검토 | T01 | entities.csv |
| P01-T03 | 출처별 이용조건 기록 | C, A/B 확인 | T01 | source_registry.csv |
| P01-T04 | 첫 문서 6개 접근 시험 | A/B, 상호 검토 | T02,T03 | access_trials.csv |
| P01-T05 | 문서 원본·메타데이터 등록 | A/B, C 통합 | T04 | document_manifest.csv |
| P01-T06 | 본문·표 추출 시험 | A/B, C 점검 | T05 | blocks.jsonl, parser_trials.csv |
| P01-T07 | 숫자·단위·기간 감사 | A/B 교차 검토 | T06 | extraction_audit.csv |
| P01-T08 | 중복·후속·정정 구분 | B, A 검토 | T05 | document_relations.csv |
| P01-T09 | 10개 분기 목록 확장 | A/B, C 빈칸 확인 | T07,T08 | coverage_matrix.csv v1 |
| P01-T10 | 측정 결과·채택 출처 결정 | C, A/B 검토 | T09 | data_feasibility.md |
| P01-T11 | 다음 단계 전달·재현 시험 | C 진행, 전원 | T10 | handoff_p0.md |

## P02 / Phase 1 — 선행연구 및 개념·사건 양식 설계

[상세 설계](P02_phase1_research_and_schema.md)

| ID | 할 일 | 책임·검토 | 선행 | 제출 |
| --- | --- | --- | --- | --- |
| P02-T01 | 연구 질문·검색 계획 확정 | C, A/B 검토 | P0-T01 | search_protocol.md |
| P02-T02 | 사건 추출 문헌 수집·정독 | B, C 검토 | T01 | literature_events.csv |
| P02-T03 | 중요성 문헌 구분 | C, B 검토 | T01 | literature_materiality.csv |
| P02-T04 | 지표·ontology 문헌 조사 | A, C 검토 | T01 | literature_metrics.csv |
| P02-T05 | 실제 사건 예시 묶음 구성 | A/B, 상호 검토 | P0-T05 | schema_seed_cases.jsonl |
| P02-T06 | 사건 단위 선택 기록 | B, 전원 검토 | T02,T05 | event_unit_decision.md |
| P02-T07 | 필드·타입·누락 규칙 작성 | C, A/B 검토 | T06,T03,T04 | event_schema.md |
| P02-T08 | 복수 주장·후속 관계 규칙 | B, A 검토 | T07 | event_relation_rules.md |
| P02-T09 | 중요성 후보 질문 작성 | C, A/B 적용 | T03,T07 | materiality_questions.md |
| P02-T10 | 처음 보는 사례로 양식 시험 | A/B, C 관찰 | T08,T09 | usability_notes.md, sample_annotations.jsonl |
| P02-T11 | 문헌 map·설계 인계 | C 통합, 전원 | T10 | research_map.md, handoff_p1.md |

## P03 / Phase 2 — Metric Ontology와 기업 간 적용 검증

[상세 설계](P03_phase2_metric_ontology.md)

| ID | 할 일 | 책임·검토 | 선행 | 제출 |
| --- | --- | --- | --- | --- |
| P03-T01 | 지표 후보 추출 범위 고정 | A, B 확인 | P0-T11,P1-T04 | metric_sampling.md |
| P03-T02 | 삼성 지표 등장 기록 | A, B 검토 | T01 | occurrences_samsung.csv |
| P03-T03 | SK하이닉스 지표 등장 기록 | B, A 검토 | T01 | occurrences_skhynix.csv |
| P03-T04 | 후보 집계·선정 근거 | A 통합, C 검토 | T02,T03 | metric_catalog.csv |
| P03-T05 | 대표명·별칭·계층 작성 | B, A 검토 | T04 | alias_registry.csv |
| P03-T06 | 단위·기간 변환표 작성 | B, C 검토 | T05 | unit_rules.csv |
| P03-T07 | 비교 가능성 판정 규칙 | A/B, C 통합 | T06 | comparability_rules.md |
| P03-T08 | driver 관계 근거 작성 | A, B 검토 | T04 | driver_edges.csv |
| P03-T09 | 메모리 공동 점검·버전 고정 | C, 전원 | T07,T08,P1-T10 | registry_v0.1_manifest.json |
| P03-T10 | 리노공업·ISC 전이 자료 선정 | A/B, C 검토 | T09 | transfer_manifest.csv |
| P03-T11 | 고정 기준 적용·예외 분석 | A 리노/B ISC, C 통합 | T10 | transfer_assessment.csv |
| P03-T12 | 최종 지표 등록부 인계 | C, A/B 승인 검토 | T11 | handoff_p2.md |

## P04 / Phase 3 — Annotation Pilot과 평가 데이터 설계

[상세 설계](P04_phase3_annotation_pilot.md)

| ID | 할 일 | 책임·검토 | 선행 | 제출 |
| --- | --- | --- | --- | --- |
| P04-T01 | 파일럿 표본 계획 고정 | C, A/B 검토 | P2-T12 | sampling_protocol.md |
| P04-T02 | 사건 family 그룹 생성 | B, A 검토 | T01 | event_families.csv |
| P04-T03 | 가이드·registry 기준본 저장 | C, 전원 | T01 | annotation_guide_v1.md |
| P04-T04 | 연습 annotation 실행 | A/B, C 조정 | T03 | practice_annotations.jsonl |
| P04-T05 | 본 표본 배정 | C | T02,T04 | annotation_assignments.csv |
| P04-T06 | 독립 사실 annotation | A/B | T05 | annotations_raw.jsonl |
| P04-T07 | 중요성 질문 독립 평가 | A/B | T06 | assessments_raw.jsonl |
| P04-T08 | 일치도·불일치 원인 분석 | C, A/B 검토 | T06,T07 | agreement_report.md |
| P04-T09 | 불일치 조정·gold 작성 | C, A/B 근거 제시 | T08 | adjudications.jsonl, gold_events.jsonl |
| P04-T10 | 시간·그룹 분할 고정 | C, B 누수 검사 | T02,T09 | split_manifest.csv |
| P04-T11 | label 품질·연결 검사 | A/B 교차, C 통합 | T10 | gold_validation.md |
| P04-T12 | dataset card·인계 | C, 전원 | T11 | dataset_card.md |

## P05 / Phase 4 — 관련성 분류·사건 추출·표준화 NLP Baseline

[상세 설계](P05_phase4_nlp_baseline.md)

| ID | 할 일 | 책임·검토 | 선행 | 제출 |
| --- | --- | --- | --- | --- |
| P05-T01 | 실험 프로토콜·환경 고정 | C, B 검토 | P3-T12 | baseline_protocol.md |
| P05-T02 | 파서·offset 연계 검사 | A, B 검토 | T01,P0-T11 | preprocess_audit.csv |
| P05-T03 | M0 사전·Regex baseline | A, B 검토 | T02 | rules_v1, predictions_m0.jsonl |
| P05-T04 | 관련성 M1 구축 | B, C 검토 | T02 | relevance_model, relevance_metrics.csv |
| P05-T05 | span·사건 M2 후보 구현 | B, A 검토 | T03,T04 | extractor_model, entity_predictions.jsonl |
| P05-T06 | metric 매핑·기업 범위 연결 | A, B 검토 | T03,P2-T12 | normalization_predictions.jsonl |
| P05-T07 | 입출력 검증 인터페이스 | C, A 검토 | T05,T06 | schemas·validation_report.md |
| P05-T08 | dev 비교·오류 분류 | A/B, C 집계 | T07 | dev_benchmark.md, error_analysis.csv |
| P05-T09 | confidence·fallback 정책 시험 | C, B 구현/A 검토 | T08 | fallback_policy.md, cost_log.jsonl |
| P05-T10 | 고정 모델 test 실행 | C, A/B 검토 | T09 | test_benchmark.md |
| P05-T11 | 오류 보완·인계 결정 | C, 전원 | T10 | model_selection.md, handoff_p4.md |

## P06 / Phase 5 — Materiality 표현 연구와 검토 우선순위 모델

[상세 설계](P06_phase5_materiality_modeling.md)

| ID | 할 일 | 책임·검토 | 선행 | 제출 |
| --- | --- | --- | --- | --- |
| P06-T01 | 표현 후보·가설 고정 | C, A/B 검토 | P3-T12 | materiality_protocol.md |
| P06-T02 | 라벨 분포·축별 신뢰성 분석 | A, C 검토 | T01 | label_structure_report.md |
| P06-T03 | feature 목록·시점 감사 | B, C 검토 | T01,P4-T11 | feature_registry.csv |
| P06-T04 | 단순 baseline 구축 | B, A 검토 | T03 | baseline_rankings.jsonl |
| P06-T05 | 표현별 모델 비교 | B, C 평가 | T02,T04 | representation_comparison.csv |
| P06-T06 | 시장 outcome 수집 가능성 판단 | A, C 검토 | P0-T03,T01 | outcome_feasibility.md |
| P06-T07 | 사건연구 보조 분석 | A/B, C 검토 | T06 | market_outcome_analysis.md |
| P06-T08 | 검토량·보정·abstention 선택 | C, A 검토 | T05 | operating_point.md |
| P06-T09 | 시간·기업 평가 | B, C 검토 | T08 | materiality_evaluation.md |
| P06-T10 | P6 변화 feature 후속 비교 | B, A/C 검토 | P6-T10,T09 | change_feature_ablation.md |
| P06-T11 | 표현 선택·운영 규칙 인계 | C, 전원 | T09; T10은 P6 완료 후 | materiality_decision.md, model_card.md |

## P07 / Phase 6 — Prior-state 검색·변화 탐지·정량 시나리오 엔진

[상세 설계](P07_phase6_retrieval_change_scenario.md)

| ID | 할 일 | 책임·검토 | 선행 | 제출 |
| --- | --- | --- | --- | --- |
| P07-T01 | store 스키마·키 정의 | B, C 검토 | P2-T12,P4-T11 | event_store_schema.sql |
| P07-T02 | as-of 정책 구현 | B, C 검토 | T01 | asof_queries.sql |
| P07-T03 | 검색용 query·qrels 작성 | A/B, C 조정 | T02,P3-T12 | retrieval_qrels.csv |
| P07-T04 | 희소 검색 baseline | B, A 검토 | T03 | bm25_results.jsonl |
| P07-T05 | dense·hybrid 후보 비교 | B, C 검토 | T04 | retrieval_benchmark.md |
| P07-T06 | 호환성 검사·prior 선택 | A, B 구현/C 검토 | T05 | prior_state_records.jsonl |
| P07-T07 | 숫자 delta 구현 | A, C 검토 | T06 | numeric_changes.jsonl |
| P07-T08 | 정성·revision change 구현 | B, A 검토 | T06 | qualitative_changes.jsonl |
| P07-T09 | 계산 공식·가정 등록 | A, C 검토 | T07,P2-T08 | calculation_registry.csv |
| P07-T10 | change interface·평가 고정 | C, A/B 검토 | T07,T08 | change_benchmark.md, change_schema.json |
| P07-T11 | scenario 실행·재현 | A, B 검토 | T09,T10 | scenario_runs.jsonl |
| P07-T12 | 전체 엔진 검증·인계 | C, 전원 | T11 | handoff_p6.md |

## P08 / Phase 7 — Review Card 시스템 통합과 피드백

[상세 설계](P08_phase7_system_integration.md)

| ID | 할 일 | 책임·검토 | 선행 | 제출 |
| --- | --- | --- | --- | --- |
| P08-T01 | 통합 인터페이스 점검 | C, A/B 검토 | P4-T11,P5-T11,P6-T12 | pipeline_spec.md |
| P08-T02 | 설정·실행 manifest | B, C 검토 | T01 | run_config.yaml, run_manifest.json |
| P08-T03 | stage 실행·재시도·resume | B, C 검토 | T02 | pipeline runner |
| P08-T04 | 카드 데이터 구성 | A, C 구현/B 검토 | T01 | review_card_schema.json |
| P08-T05 | 목록·상세·근거 화면 | C, A 검토 | T04 | review UI |
| P08-T06 | 피드백 영속 기록 | C, B 검토 | T05 | feedback store |
| P08-T07 | active learning 후보 큐 | B, A/C 검토 | T06 | active_learning_queue.csv |
| P08-T08 | 관측·비용·실패 화면 | B, C 검토 | T03 | run_dashboard, cost_report.csv |
| P08-T09 | end-to-end 반례 점검 | A/B, C 통합 | T05,T06,T08 | integration_report.md |
| P08-T10 | 팀 사용성 시험 | A 진행, B/C 참여 | T09 | usability_notes.md |
| P08-T11 | 운영·데모 인계 | C, A/B 재현 | T10 | operator_guide.md, demo_manifest.json |

## P09 / Phase 8 — 비교 실험·검토 효용·최종 보고서

[상세 설계](P09_phase8_comparative_evaluation.md)

| ID | 할 일 | 책임·검토 | 선행 | 제출 |
| --- | --- | --- | --- | --- |
| P09-T01 | 평가 질문·성공 기준 동결 | C, 전원 | P7-T11 | evaluation_protocol.md |
| P09-T02 | 평가 데이터 노출 감사 | B, C 검토 | T01 | split_audit_final.md |
| P09-T03 | 비교 시스템 버전 동결 | B, A/C 검토 | T02 | frozen_run_manifest.json |
| P09-T04 | 자동 benchmark 실행 | B, C 집계 | T03 | system_comparison.csv |
| P09-T05 | 구성요소 ablation | B, A 검토 | T03 | ablation_results.csv |
| P09-T06 | 사람 과업·순서 설계 | A, C 검토 | T01,T02 | review_study_protocol.md |
| P09-T07 | 검토 세션 실행 | 전원, A 기록/C 분석 | T06,P7-T11 | review_sessions.csv |
| P09-T08 | API·처리시간 비용 집계 | B, C 검토 | T04,T07 | cost_latency_report.md |
| P09-T09 | 차이·불확실성 분석 | C, B 검토 | T04,T05,T07,T08 | uncertainty_analysis.md |
| P09-T10 | 실패 사례·한계 정리 | A/B, C 통합 | T09 | failure_cases.md |
| P09-T11 | 최종 보고서·재현 묶음 | C, B 재현/A 검토 | T10 | final_report.md, reproducibility.md |
| P09-T12 | 데모·종료 검토 | 전원, C 정리 | T11 | demo_manifest.json, project_closeout.md |

## 회의1 작업 01~12와 대응

| 회의1 | 상세 설계 작업 |
| --- | --- |
| 01 범위 | P01-T01~T02 |
| 02 접근 조건 | P01-T03~T04 |
| 03 문서 목록 | P01-T05,T08~T09 |
| 04 추출 품질 | P01-T06~T07,T10~T11 |
| 05 사건 문헌 | P02-T02,T05~T08 |
| 06 중요성 문헌 | P02-T03,T09 |
| 07 지표 선정 근거 | P02-T04,P03-T01,T04,T08 |
| 08 사건 양식 | P02-T06~T11 |
| 09 지표 후보 | P03-T01~T05 |
| 10 별칭·단위·정의 | P03-T05~T09 |
| 11 공동 검토·리노/ISC 적용 | P03-T09~T11; 정식 대규모 pilot은 P04 |
| 12 결과 검토·다음 단계 | P01-T11,P02-T11,P03-T12; 후속 Phase 단계종료 |

## Jira 작업으로 옮길 양식

```text
제목: [설계 ID] 동작 + 결과물
목적:
선행 작업:
입력 자료·버전:
수행 방법:
1.
2.
3.
산출물·저장 위치:
완료 확인:
참고 설계서·레퍼런스 ID:
결과 기록:
- 실제 수행·검증:
- 결과물·버전:
- 실패·한계:
- 다음 담당에게 전달:
```

큰 작업은 1~2일 단위로 기업·형식·유형을 나눠 하위 작업을 만들되 서로 다른 완료 조건을 한 카드에 과도하게 묶지 않습니다. 과학적 결과를 보장하는 완료 조건 대신 ‘정해진 조건에서 실험·검증·결과 정리’를 사용합니다.

