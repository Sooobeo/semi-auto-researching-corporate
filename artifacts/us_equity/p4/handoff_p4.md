# P05 → 후속 개발 인계

`active_run.json`이 최종 실행을 가리킨다. `validated_candidates.jsonl`은 검증 통과한 P05 envelope 39개, `candidate_store_records.jsonl`은 공통 raw/normalized/assessment/derived 규약으로 옮긴 개발 후보 39개다. P04 정답 ID를 부여하거나 P04 annotation schema 통과로 승격하지 않았다. 원문·schema·규칙·실행·근거 ID를 provenance로 유지한다.

`relation_claim_links.jsonl`은 같은 문서/행/보고기간의 숫자 후보에 연결한 보고 사업부 관계 6개다. 공유 근거이며 6개 추가 숫자 관측이 아니다. `withheld_results.jsonl`은 실패·보류·격리 결과용이며 이번 최종 실행은 0개다. 전체 결과와 분모는 run의 `input_results.jsonl`을 읽는다. 빈 파일을 미완료 작업 완료 증거로 해석하지 않는다.

숫자값은 Decimal 문자열, USD 기본 단위, scale=1이다. 원 숫자·source_scale·source_numeric_value·부호 정책은 별도다. 기준 기간은 normalized.temporal.reference_period, 발표일은 published_date다. 기간 시작은 derived이며 관계 실제 effective/valid 날짜는 null이다. 날짜는 일 정밀도로만 처리한다. evidence_map을 통해 원 P04 위치 84개로 돌아갈 수 있다.

모든 후보는 adaptation/needs_review, 미보정 규칙 신호, 확률 null이다. 전사 scope의 2026년 후향 의존성 24개는 과거 기준 검증 근거로 쓰지 않는다. 사업부 표시 정의는 발표별로 유지하며 같은 이름만으로 비교하지 않는다. prior·정의 정책·실제 관계 유효기간은 미완료다. 중요성 MQ·외부 사실 확인·예측 실적을 생성하지 않는다.

원문은 기존 private에 그대로 있고 공유 파일에 복제하지 않았다. 출처 조건 확인일은 2026-10-05이며 최소 사실 참조 범위다. prose AI 입력·학습·외부 전송은 허용으로 승격하지 않았다. 전체 표/본문 자동 발견, 다른 기업, M1/M2/M3, 사람 gold 및 독립 benchmark는 후속 조건이 충족될 때 실행한다.
