# P04 → 후속 개발 인계

**허용되는 인계는 adaptation 개발 자료다.** 인간 gold·미노출 test가 없으므로 독립 benchmark·P04 전체 완료로 보고하지 않는다. P05 모델 실행은 이번 요청 범위에서 시작하지 않았다.

1. `dataset_card.md`의 파일별 읽기 계약부터 확인한다. 계약의 `normalized.numeric_value`는 base USD이고 reviewed의 `facts.numeric_value`는 원 배율이다.
2. `split_manifest.csv`와 `split_policy.json`을 함께 읽어 39개 주석 항목을 adaptation으로 유지한다. FY2026 Q1 예약 본문은 개발 입력에 추가하지 않는다.
3. facts 검토는 `reviewed_agent_claims.jsonl`·`reviewed_agent_relations.jsonl`, 원문 계약/근거는 `contract_records.jsonl`·`evidence_index.jsonl`, 질문 판단은 `assessment_reviews.jsonl`을 사용한다.
4. 결과를 재계산하려면 `verification_commands.md`의 새 보고서 경로를 지정한다. 생성 스크립트는 기존 결과 덮어쓰기를 거부한다.
5. 후속 독립 평가 전에 실제 사람 A/B와 조정자의 기록, 원문 이용 범위·본문/날짜 감사, 유형·무관 대조, prior·정의 정책을 확보하고 모델/정책과 split을 새 버전으로 고정한다.

미해결 상태는 `unresolved_cases.csv`의 78행/39항목이다. 설계 작업별 미완료 조건은 `task_status.csv`에 있다. 원문/정답 접근을 통제하는 운영 체계와 인간 소요시간은 아직 없다. 예약을 열면 노출 이력부터 업데이트해야 하며 파일이 새롭다는 이유로 untouched test를 주장하지 않는다.
