# Prior state·시간 정책 초안

2026-10-05 · 0.1.0 · actual retrieval 시스템·qrels 미구현.

신규 claim은 어떤 cutoff로 판단했는지 retrieval record에 cutoff/cutoff_mode/corpus_version/source_publication_evidence를 기록한다. cutoff_mode=publication_as_of는 원 공개시점, observation_as_of는 시스템이 실제 관측한 시점을 제한하며 두 모드를 혼합하지 않는다. available_at은 모드와 publication 근거·observed 정책에서 파생하며 계산 방법·시간대·근거를 보존한다.

published_at이 검증된 경우 원 시간대/UTC offset·DST를 함께 보존하고 UTC로 비교한다. 날짜만 알려진 prior는 하루를 정확 시각 하나로 만들지 않는다. 같은 날짜 intra-day cutoff에는 포함 여부를 unknown으로 두거나 보수적으로 제외하며 boundary_policy=date_only_excluded_in_intraday_query를 기록한다. 이후 날짜 단위 조회에 포함할 때도 date precision을 유지한다. 시각 충돌이 있는 문서는 양쪽 raw 값/위치를 보존하고 시간 정확도 요구 조회에는 보류한다.

candidate 검색 후 회사·scope·제품·정의·회계기준·실제 기간·기간 길이·단위·통화·value_kind·modality·관계 문맥을 각각 판정한다. 신규 claim이 forecast라면 같은 미래 대상 기간의 prior 계획/forecast와 비교한다. 전기 actual과 forecast를 같다고 보지 않는다. 예외 계산은 required input과 formula rule을 명시한다.

비교 가능한 후보가 없으면 prior_not_found이며 prior_claim_id=null이다. 반복임을 확인했을 때만 repeated다. 없어진 이전값을 0으로 만들거나 % 변화로 절대값을 생성하지 않는다. incompatible과 ambiguous는 not_found와 별도로 기록한다.

정정본은 그 정정의 공개시점 이후에만 사용한다. retrospective_reconstruction은 현재 작성시점을 보존하고 당시 실제 작성 전망/판단으로 표시하지 않는다. 새 follow_up은 이전 기록을 덮어쓰지 않고 별도 family·claim로 연결한다. relation의 valid/effective 기간과 available/published 시점을 모두 제한한다.

한국기업 자료는 활성 retrieval corpus에서 제외한다. 이번 스키마·가이드 개발 자료는 adaptation/practice 노출을 남기며 독립 test로 부르지 않는다. 번역·전재·정정 계보는 family 단위 분리, 계획→실행은 독립 family여도 같은 사업 에피소드의 누수 위험을 별도 검토한다.
