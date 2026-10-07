# P08 실행 결과 · 2026-10-07

Microsoft 공식 FY2024 Q4·FY2025 Q4 release 2건·발표 family 2개. 기존 최소 숫자·표준 라벨·기간·위치 사실 참조만 사용했다. 신규 원문 수집/외부 LLM 0회. 정확 발표 시각·날짜 충돌·사후 전사 문맥·사업부 표시 정의·관계 유효기간은 미확인이다. 전체 본문 수동 감사와 사람 검토는 미실행이다.

추출 재실행·검증 39/39 candidate → P07 비교 처리 39/39 candidate(세 시점 변화 시도 126개) → P06 검토 사유 39/39 → 카드 연결 39/39 candidate, 33/33 card 검증. 정상 연결에서 실패/제외 0개. 파일 feedback 실사용 0건, 사람 gold 0개. 숫자33·관계6은 공유 근거이며 독립 사건39개가 아니다.

P08 피드백/schema·빈 결과·오염·장애·resume·timeout 반례 30/30 통과. 같은 카드 버전의 서로 다른 run 수정 충돌·이력 보존과 변경된 카드 버전의 검토 미상속도 확인했다. `integration_resume_013`은 extract/compare 재사용 후 나머지 실행을 완료했고 full run 카드 의미 hash가 일치했다. 같은 agent 검사이며 팀원 재실행은 미실행이다. `resilience_tests.json` 참조.

현재 batch elapsed/단계별 실측 시간은 run_manifest/cost_report에 있다. 외부 호출 0과 운영 비용 0원을 혼동하지 않으며 운영 비용·메모리 peak는 null이다. 테스트용 actor/수정은 임시 journal에만 쓰고 실제 feedback/gold로 저장하지 않았다.

화면 adapter는 integration_snapshot.py와 p08-p09-site-0.1 schema다. 기존 P05/P06/P07 조회를 유지하면서 카드·목록/상세·세 모드·질문·공식 입력·검토 초안·내보내기·로컬 가져오기·실제 로컬 실행을 연결했다. 브라우저 범위·API 검증과 게시 상태는 별도 browser_qa.json·local_api_validation.json·site_update_manifest.json에 기록한다.

실패와 수정 전 개발 run은 보존했다. `integration_debug_001`의 검증 의존성 실패, `integration_resume_005`의 Windows 일시 파일 교체 실패, 변경 코드로 재실행한 후속 run을 최종 검증에 합산하지 않는다. 최종 활성 입력은 integration_012이다.
