# P05 웹 화면 실행·배포 기록 — 2026-10-06

공유 주소: https://corporate-research-p05.sooobeo.chatgpt.site

기존 GitHub 저장소의 `web/p05/`에 정적 화면, 최소 사실 snapshot exporter, 로컬 Python companion server와 실행 안내를 추가했다. 기존 P05 동결 코드·입력·패키지는 수정하지 않았으며 `p05_verify_package.py`의 30/30 검사를 유지했다. 별도 데이터베이스나 새 ID/PW 저장소는 만들지 않았고 Sites 계정 인증과 지정 사용자 allowlist를 사용했다. 접근 범위는 소유자와 사용자가 지정한 팀원 1명이다. 초대와 권한 설정은 native Sites 도구로 수행했다.

공유 화면은 m0_004의 숫자 33개·보고 사업부 관계 6개 및 원문 위치·검토 상태·검증 결과를 표시한다. 전체 본문을 복제하지 않았다. 39/39 일치는 공유 개발 참조 회귀이며 인간 gold/독립 성능 평가는 0/not_evaluated다. 웹 금액 표시는 큰 정수에 BigInt를 사용하고 원 Decimal 문자열을 보존한다.

로컬 실행은 `python web/p05/server.py`로 시작한다. 화면의 다시 실행 버튼이 실제 P05 추출 → 원문 위치 검증 → agent 참조 비교를 호출한다. 실제 API 재실행에서 입력 39·후보 39·필드 비교 오류 0을 확인했다. 실행 결과는 p4_web_runs에 새로 저장하며 기존 동결 파일을 덮어쓰지 않는다. 로컬 서버는 loopback에만 바인딩하고 경로 allowlist와 요청 토큰/Origin 검사를 적용했다. private/키/임의 파일 접근 차단과 다른 Origin의 쓰기 거절을 확인했다.

공유 사이트는 게시된 snapshot을 표시하며 로컬 실행을 자동으로 동기화하지 않는다. 새 결과를 공유하려면 exporter로 snapshot을 갱신한 뒤 같은 Site에 재게시한다. 서버·브라우저 간의 실행 상태를 가장하는 버튼은 공유 화면에 넣지 않았다.

JavaScript 문법, 정적 자산 참조, snapshot 개수/단위/날짜/검토 상태와 로컬 API를 확인했다. 현재 환경의 브라우저 목록이 비어 있어 실제 브라우저 렌더·모바일 시각 QA 및 WebMCP live validation은 unavailable로 기록했다. 반응형 CSS와 키보드용 버튼/포커스/대화상자를 작성했으나 시각 QA 통과로 보고하지 않는다.

Sites 등록은 1회, 배포는 버전 1로 성공했다. Windows의 WSL bash/드라이브 tar 경로 문제는 Git Bash와 TAR_OPTIONS=--force-local을 사용하는 기존 공식 workflow 재실행으로 해결했다. main GitHub 저장소의 Git 이력·remote는 그대로이며, 사이트 배포용 checkout/archive는 Git 제외 private에 두었다. 자격증명은 stdin/세션 메모리로만 전달하고 파일·공개 결과에 저장하지 않았다.

- project_id: appgprj_6ac4af31b39c8191b7d3d8876d313876
- saved version: appgprj_6ac4af31b39c8191b7d3d8876d313876~appgver_b93010c3820081919c5f42b784767382
- deployment: appgdep_6ac4b21585a0819185e5e22800937dce
- pushed site source: ed090a09f522b02348ddb09da45965f387b1fb9b
- publication: succeeded
- audience: custom (owner + 1 designated viewer)

로컬 사용·갱신 방법은 [웹 화면 안내](../../../web/p05/README.md)에 있다.
