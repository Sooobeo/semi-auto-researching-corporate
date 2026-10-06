# 1번 자가검증·개선

초기 검사와 별도 agent 검토를 대조했다. 사람 검토가 아니다.

1. 새 EV 접두사 대신 P03 관계의 기존 event_id를 유지했다. 원본 자료는 변경하지 않았다. 수정 전 mapping은 stage_01_before_improvement에 보존했다.
2. 39는 annotation 작업 항목 수다. 고유 source claim_id는 33, relation_id는 6, endpoint는 3, 잠정 발표 event/family는 각 2다.
3. FY2025의 FY2024 비교열 3개는 FY2025 발표에 남겼다. 이전 표시와의 representation_overlap 3개를 추가했으며 correction_of로 단정하지 않았다.
4. annual reference는 family가 없는 보완 문서다. 전사 claim 24개의 retrospective_scope_dependency를 기록해 과거 cutoff에서 제외하도록 했다.
5. 초기 hash 검사가 hash의 존재만 검사하던 부분을 실제 snapshot과의 동등성 검사로 수정했다.
6. 새 평가 후보는 source_reservation 결과로 별도 관리한다. 문서 예약은 정답 확보·test 인증이 아니다. 표본의 음성/비정량/계획·부인/타기업 결측은 유지한다.

다음 단계 개선 과제: raw/normalized/assessment/derived 계약에 실제 표본을 매핑하고, 원문 위치·기간 헤더를 재조회한 후 가이드·스키마를 고정한다.
