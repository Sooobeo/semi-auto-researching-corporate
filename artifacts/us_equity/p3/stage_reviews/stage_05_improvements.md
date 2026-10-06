# 5번 자가검증·개선

1. 독립 검사기는 root 구현을 읽지 않고 source metadata·원주석으로 split 43행과 의존성 27개를 재구성했다. 27개 변형 반례를 차단했다. 신규 비교열을 읽지 않았으므로 예약 후보의 독립성은 인증하지 않았다.
2. 초기 계획의 미확보 문구와 coverage gap이 실제 예약 상태와 달랐다. 초기본을 보존하고 후보 1개 예약·라벨 0·독립성 미확인으로 갱신했다.
3. base USD 계약과 백만 USD 주석의 읽기 계약을 dataset card에 나란히 적었다. 전용 인계 검사기의 배율·부호·참조 변형을 검사했다.
4. 인계 검사 초안이 전사 scope를 entity 집합에서 잘못 찾아 24개를 거부했다. 실패 보고서·초기 코드를 보존하고 registry scope 필드로 수정했다. 회사 ID를 scope로 바꾸는 반례를 추가한 최종 결과 39/39 및 13/13 통과.
5. reviewed 파일에서 생략된 date_conflict_status가 감사 완료로 오해되지 않도록 본문·날짜 수동 감사 미실행을 문서에 명시했다. 초기 agent 초안과 인간 gold의 경계를 task_status·phase_status·빈 gold 상태에 일관되게 기록했다.
6. source/input/가이드/주석/4번 검토 파일의 기존 hash를 대조하고 public 파일 manifest와 재실행 명령을 고정한다. private 원문과 정책은 Git 제외 상태로 유지하며 신규 예약의 본문은 읽지 않는다.
7. 통합 검사 초안에서 Windows text stdin의 CRLF가 Git 파일명에 CR을 붙여 private 제외 대조를 잘못 실패시켰다. 실제 파일 노출이 아니라 검사기 입력 인코딩 문제였다. NUL 구분 binary stdin(`git check-ignore -z`)으로 수정해 정확한 경로 10개를 비교했다. 실패 진단은 `package_integration_initial.json`에 보존했다.
