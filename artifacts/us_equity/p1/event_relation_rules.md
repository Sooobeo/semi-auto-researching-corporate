# 복수 주장·후속·정정 규칙

2026-10-05 · 0.1.0 · 실제 기업의 계획→실행 쌍 검증 대기.

1. 회사·scope·제품·metric·기준 기간·modality·화자 중 비교 의미가 다른 항목을 별도 claim으로 분리한다. 표의 각 회사/segment/기간/metric 셀도 의미 단위별로 분리하며 단위·기간 머리글은 공통 evidence로 연결한다.
2. 하나의 claim에 여러 블록 근거를 허용한다. 리드 숫자와 표의 scope가 다르면 통합하지 않고 충돌 두 위치를 보존한다.
3. exact_duplicate는 파일 hash가 같거나 검증된 동일 파일이다. 비슷한 제목·숫자만으로 중복 확정하지 않는다. 중복 파일은 재수집 로그를 추가하며 새로운 doc_id를 만들지 않는다.
4. repeated는 새 발표가 기존 claim을 재서술하며 새 동작·숫자·조건이 없다는 비교 판정이다. prior_not_found는 검색 실패 상태이므로 repeated로 바꾸지 않는다.
5. translation_of / reprint_of는 별도 문서이나 같은 발표 family다. 실제 원문/전재 기원 미확인은 unknown으로 남긴다.
6. correction_of는 출처가 정정이라고 밝힌 새 발행 문서다. 별도 doc_id·새 발표 family와 correction_of 관계·새 공개시점을 기록한다. source revision은 같은 URL 관측본의 revision으로 기록한다. 새 정정 family와 이전 family를 leakage_group으로 연결하고 split에서 함께 제어한다. 서로 다른 발표 family를 정정이라는 이유만으로 동일 발표로 합치지 않는다.
7. follow_up_of는 새 발표의 독립 family다. 계획→실행, 개발→검증→생산→출하→판매가 바뀌면 해당 단계의 원문 action과 modality를 남긴다. 숫자가 없어도 새 동작은 follow-up일 수 있다.
8. contradicts / denies / terminates / narrows / expands는 원문이 명시하거나 비교 규칙이 지지할 때 claim/관계 pair에 판정한다. 유사도 score만으로 판정하지 않는다.
9. 관계 양끝·방향·scope·시점·modality의 충돌은 따로 남기고 available_at 기준 상태를 조회한다. 회사 발표와 외부 확인 수준을 구별한다.
10. 한국어 설명은 assessment/번역 record로만 연결한다. 영어 span의 위치를 한국어 문장 길이로 계산하지 않는다.

합성 반례: “A plans to supply samples to B”와 “A ships commercial units to B”는 공급 단계가 다르다. 첫 claim은 plan, 후자는 출처가 보고한 actual_reported이며 외부 사실 확인은 별도다. 첫 문서의 계획 금액이 후속 문서에 없으면 매출 금액을 자동 승계하지 않는다.
