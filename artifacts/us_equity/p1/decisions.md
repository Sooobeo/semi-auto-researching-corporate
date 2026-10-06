# P02 잠정 결정 이력

2026-10-05 · 작성자 Codex · 팀 승인 여부: 미확정.

| ID | 구현 결정 | 근거/한계 |
| --- | --- | --- |
| P02-001 | 원자 claim 기본 단위 + event/family + 다블록 evidence | event_unit_decision.md; 실제 독립 사례 검증 대기 |
| P02-002 | raw/normalized/assessment/derived 분리 | DATA_CONTRACTS §1·4; agent 의견을 fact에 넣지 않음 |
| P02-003 | JSON Schema 2020-12, Decimal 문자열, 명시 null/누락 사유 | DATA_CONTRACTS §1.7; 형식과 의미 검증 구별 |
| P02-004 | 다차원 MQ 질문, review_readiness 별도, 합산 점수 보류 | materiality_schema_candidates.md; 인간 일치도·효용 미측정 |
| P02-005 | 날짜만 알려진 prior intraday 조회 보수 제외 초안 | prior_state_policy.md; 팀 정책 확인 필요 |
| P02-006 | 이번 미국 개발 사례 adaptation/practice, 폐기 한국 입력 제외 | DATA_CONTRACTS·P04; test/gold 자동 승격 금지 |
| P02-007 | 관계 후보 정의와 수치 없는 사건을 유지 | relation_schema.md; 관계 존재→매출 영향 변환 금지 |

새 source-backed 사례·실패 검사로 변경할 때 schema/guide version·이전값·새값·이유·영향 사례 ID를 추가한다. 이번 결정은 팀 확정·성과 목표 확정이 아니다.
