# P04 연결·라벨 검증 상태

human gold 0건이므로 gold 품질 인증은 미실행이다. 아래는 agent 개발 산출물에 대한 검사 결과다.

| 검사 | 실행 결과 | 범위·한계 |
| --- | --- | --- |
| 원자료 계약 | 39/39 통과, 부정 사례 22/22 차단 | 33 숫자+6 관계, 선택 근거 위치 84개 |
| 원본 및 agent 계약 | 최종 본 주석 78/78, 평가 78/78 통과 | 각 39항목×2 agents; 공유 자료·규칙 |
| 조정 연결 | 39/39 | 양쪽 원본 annotation ID·assessment ID·근거 추적 |
| 숫자 표현·인계 연결 | 39/39, 변형 사례 13/13 차단 | 백만 배 중복·원 부호·참조·관계 방향·허위 gold 검사 |
| 인간 주석·원문 수동 감사 | 0건 | 자동 XPath/셀 대조가 전체 본문·사람 감사의 대체가 아님 |
| 평가 가능한 독립 test | 0건 | 신규 문서 1개는 unlabeled reservation |

첫 인계 검사기는 scope ID를 entity ID 집합에서 찾는 오류로 전사 24개를 잘못 거부했다. registry의 `entity_id`와 `scope_id`를 분리하고 회사 ID를 scope로 바꾼 반례를 추가했다. 실패 보고서와 초기 코드는 `stage_reviews/`에 보존했고 최종 검사가 통과했다.

날짜 정밀도는 date, 전체 날짜 충돌 감사는 미완료다. 관계 `reference_period`를 실제 사업 `effective_period`로 대체하지 않았다. 회사 보고·미감사 수치와 외부 확인 사실을 구분한다. 과거 scope 근거 부족 24개, 사업부 표시 정책 9개, 관계 실제 유효기간 6개, prior 부족 39개는 각각 미해결 행으로 남았다. 이들은 false/0/낮은 중요성으로 변환되지 않았다.

원자료 위치·offset 검증은 `contract_validation_final.json`, 본 주석 연결은 `stage_reviews/main_check_final.json`, 인계 검증은 `stage_reviews/handoff_validation_final.json`, 분할 검증은 `stage_reviews/stage_05_independent.json`에서 확인한다. 사람 IAA·시스템 precision/recall은 null이다.
