# P02 검증 범위

2026-10-05 · 실제 실행 결과는 schema_validation_report.json이 기준본이다.

Draft 2020-12 스키마 자체, 합성 정상 사례 6건, 실패해야 할 오류 사례 22건을 jsonschema 4.26.0과 의미 검사기로 확인했다. 정상·오류 기대 결과를 합친 검사 28건 중 최종 통과 수는 JSON 보고서에 저장한다. synthetic 상태를 독립 인간/gold/test로 바꾸는 입력, 날짜만 주어진 자료의 정확 시각 생성, null을 계산한 절대값으로 변환, 숫자 형식·방향·offset·필드 연결 불일치를 거부한다.

영문 source 실제 양식 0건, 원본 표/본문 수동 감사 0건, 독립 인간 주석 0건, gold 0건이다. 실제 영어 추출 성능·원문 보존·권리 허용·팀 사용성 검증은 미완료다. 합성 결과를 해당 지표에 포함하지 않는다.

source body가 없는 상태의 pending record는 schema_seed_cases.jsonl에 별도 저장했으며 claim schema에 맞는 실제 fact로 바꾸지 않았다. 반례 fixture와 generated examples의 ID는 SYN이며 실제 CIK·ticker를 생성하지 않았다.
