# P04 분할·누수 감사

현재 분할은 adaptation과 라벨 없는 예약 후보만 포함한다. `split_manifest.csv` 43행은 기존 문서 3+주석 항목 39=adaptation 42행, 신규 문서 예약 1행이다. train/dev/test와 human gold는 0건이다. 누수 검사 통과를 평가 세트 인증으로 해석하지 않는다.

- 발표 family 2개와 support 문서 1개는 `LG-MSFT-EXPOSED-FY2024-FY2025-EARNINGS`에 묶었다. 숫자 33개와 관계 6개를 원 문서·event·family·원본 주석에 연결했다.
- FY2025 자료의 FY2024 사업부 비교열 3개와 FY2024 발표를 서로 다른 독립 평가로 나누지 않았다. `dependency_edges.csv`의 표현 중복 3개를 같은 그룹에 보존했다.
- 발행일 미상의 annual scope 지원 문서는 사건 분모에서 제외했다. 2026-10-05 관측을 2024/2025 근거로 소급하지 않으며 관련 24개 의존성을 미해결로 유지했다.
- 날짜만 알려진 두 release에 자정 timestamp를 만들지 않았다. 가이드가 이미 후속 시점을 포함한 점도 노출 이력에 기록했다.
- FY2026 Q1은 2025-10-29 발표라는 metadata만 확인했다. 개발 경계 후보 2025-07-30 뒤지만 본문·비교열·정정/family 중복은 검사하지 않았다. `PENDING-US-MSFT-FY2026-Q1`은 임시 그룹이며 `test_eligible=false`다.
- 예약 본문이나 라벨을 개발 자료에 넣지 않았다. test 정답은 존재하지 않으며 접근 분리는 절차적이다. OS ACL로 격리된 test 보관소가 아니다.
- legacy 한국 입력은 0건이다. source hash·revision·원래 event ID·기존 group ID를 유지했다.

독립 검증과 변형 반례의 상세 결과는 `stage_reviews/stage_05_independent.json`, 파일별 수치 계약 검사는 `stage_reviews/handoff_validation_final.json`에 기록한다. 이후 변경은 새 split version과 audit가 필요하다. 예약을 test로 승격하려면 권리·본문·시점·중복 감사, 실제 독립 주석, 모델/정책 동결과 평가 정답 접근 기록을 별도로 수행해야 한다.
