# P01 권리 gate 읽기전용 검토 (2026-09-21)
- 현행 registry 18행을 메모리상의 Collector.fetch와 가짜 transport로 검사: 요청 0건; 실제 네트워크 0건.
- 초기 unresolved·excluded 행은 요청 전에 차단되며, 수집기의 각 redirect는 권리 검사를 다시 수행한다.
- 발견 1: 계약 not_inspected 행도 verified·필수 권한·발행기간만 채우면 통과했다; 계약 증거·이용권 유효기간 검사가 필요하다.
- 발견 2: audit는 최초 URL만 검사하며, 최종/redirect 권한 또는 storage_uri와 body_attempted=false의 모순을 놓칠 수 있었다.
- 두 경계를 보완한 뒤 구현 담당의 오프라인 테스트 24개 통과 보고를 받았고, 부모가 실제 후보39개 gate·audit를 실행해 본문요청0 및 기록 무결성 통과를 확인했다(final_validation.json).
- 공개 출처 검토 분모: news_source_trials.csv의 request_url 고유값 19개, trial_id 24개(성공 17·실패 6·부분 1).
- 위 19개는 상품·약관·도움말 URL이며, 기사/API 접근 성공률 또는 계약이 검증된 출처 수가 아니다.
- 신규 authorization 필드는 계약/공개허락의 적용 증거가 확인될 때까지 unresolved로 유지한다.
