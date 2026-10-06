# 2번 자가검증·개선

실자료 39레코드의 계약/원문 위치 검사와 독립 통합 검사를 수행했다. 초기 mapper 실패와 초기 가이드 원본은 contract_revisions/initial 및 stage_02_before_improvement에 보존했다.

- 현금흐름 statement_type의 P1 enum 불일치를 수정했다.
- capex source_numeric_value가 이미 부호 변환된 값이었던 문제를 수정하고 원 괄호 음수와 양의 cash outlay 변환을 함께 보존했다.
- 보고 사업부의 보고기간을 실제 관계 유효기간으로 사용하지 않도록 reference/effective를 분리했다.
- company_reported의 원 unaudited qualifier와 기간 시작일 유도 방식을 별도로 보존했다. 날짜 충돌 수동 감사 미실시를 완료로 표현하지 않도록 수정했다.
- 가이드 자체의 후속정보 노출 때문에 A/B도 엄밀한 미노출 as-of 평가자가 아니라는 점을 기록했다. 현재 결과는 retrospective cutoff simulation이다.
- 주석 계약에 provenance와 필드별 null 사유, scope의 과거 근거 상태를 추가했다. annotator_kind 명칭과 instant duration=null을 통일했다.

반례는 원문 span·없는 ID·scope·정의·가짜 시각·미래 근거·관계 방향/효력·null·허위 gold·배율/부호·헤더·hash·unaudited 누락·기간 유도·미실시 감사 오표시를 포함한다. 숫자는 최종 validation JSON에서 재계산한다.

다음 단계: 고정된 raw packet과 공통 가이드만 A/B agent에 배정하고, 연습 결과를 먼저 검사한 후 본작업을 수행한다. 인간 주석·gold·본문 완전성은 별도 미완료 항목이다.
