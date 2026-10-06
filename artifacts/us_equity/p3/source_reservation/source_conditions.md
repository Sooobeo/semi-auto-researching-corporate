# P04 단일 문서 예약의 출처 조건

기준일 2026-10-06. 대상은 [Microsoft FY2026 Q1 공식 release](https://www.microsoft.com/en-us/Investor/earnings/FY-2026-Q1/press-release-webcast) 한 문서다. 다른 기업·기간으로 확장하지 않았다.

[Microsoft 공식 Terms of Use](https://www.microsoft.com/en-us/legal/terms-of-use)를 현재 웹으로 읽고 직접 로컬 사본과 대조했다. 표시 갱신일은 2022-02-07이다. Documents 절의 정보 목적 개인·비상업 이용, 고지 유지, 미변형, 네트워크 게시 제한을 확인했다. 이는 기존 P03의 좁은 개인 사실 참조 운영 판단을 적용한 것이며 포괄 수집·AI 코퍼스 권리의 확인이 아니다. 자동 접근을 명시적으로 포괄 허락하는 약관으로 해석하지 않는다. 원문 AI 입력·학습은 unresolved, 원문 외부 전송·공유·재배포는 이 경로에서 금지로 처리한다.

robots 확인 뒤 같은 `www.microsoft.com` 호스트에서 약관과 대상 문서를 각각 한 번 직접 요청했다. redirect·재시도 없이 호스트 요청 시작 간격 최소 2초를 적용했다. robots 허용과 HTTP 200을 이용권의 근거로 삼지 않는다. 403/429, robots 금지, 요청 실패 또는 redirect면 중단하고 후보 실패를 보존하도록 구현했다.

HTML 원본·robots·약관은 `private/`에 미변형 저장했다. 원문 고지를 유지하고 Documents 절의 고지와 제한을 `private/permission_notice.txt`에 동봉했다. 전체 private 경로의 Git 제외와 저장한 세 파일의 SHA-256 재검사를 확인했다. 원문 prose·표 값·정답은 도구 응답, agent 입력, 공개 파일에 내보내지 않았다. 발표 날짜와 문서 ID·hash·URL·관측시각·HTML 구조 존재 여부만 노출했다.

후보 1개, 문서 접근 시도 1개, 원본 예약 1개다. 정책 요청 2개는 이 분모에 넣지 않는다. HTML 파싱과 body/table 존재 확인은 완전 본문 감사가 아니다. 발행일은 dateline의 날짜이며 정확 시각은 만들지 않았다. 페이지 날짜와 dateline의 수동 대조, 본문 완전성, 수치·scope, 비교열 재등장 및 누수 감사는 미완료다. 숫자·라벨 추출과 parser 적응은 수행하지 않았다. 상태는 `reserved_document_unlabeled`이며 독립 인간 gold·미노출 test 성능이 아니다.

메타데이터: `document_manifest.json`, `reservation_summary.json`. 권리 축: `source_registry.csv`. 요청/실패 보존: `access_trials.jsonl`. 검증: `verification_runs.jsonl`. 스크립트는 예약 결과 덮어쓰기를 거부하며 후속 `verify`는 네트워크 없이 저장본만 검사한다.
