# P05 웹 화면

팀원용 공유 화면과 내 PC 실행 화면은 같은 HTML/CSS/JavaScript를 사용합니다. 별도 데이터베이스나 모델 설치가 필요 없습니다. 기존 P05 동결 코드·자료는 수정하지 않습니다.

## 내 PC에서 열기

저장소 루트의 PowerShell에서 다음을 실행하고 표시된 주소를 브라우저로 엽니다.

```powershell
$env:PYTHONIOENCODING='utf-8'
python web/p05/server.py
```

주소는 `http://127.0.0.1:8765`입니다. ‘다시 실행’ 버튼은 현재 Python으로 P05 추출 → 원문 위치 검증 → agent 참조 비교를 실행합니다. 결과는 `artifacts/us_equity/p4_web_runs/<run_id>/`에 새로 저장합니다. 서버를 닫으려면 터미널에서 Ctrl+C를 누릅니다. 다른 포트는 `--port 8766`처럼 지정합니다.

## 팀원에게 공유하는 화면

`dist/`에는 게시된 결과 snapshot과 정적 화면만 있습니다. Sites의 계정 로그인·지정 사용자 접근 권한으로 보호하며, 별도 ID/PW 데이터베이스를 만들지 않습니다. 공유 화면은 게시 시점의 결과를 보여주며 로컬 Python 실행 기능과 구분됩니다.

신규 로컬 실행을 공유 화면에 반영하려면 먼저 다음으로 snapshot을 만듭니다. `--run-dir`를 생략하면 기존 공식 active run을 사용합니다.

```powershell
python web/p05/snapshot.py --run-dir artifacts/us_equity/p4_web_runs/<실행 ID>
```

이후 같은 Sites 프로젝트에 수정 버전을 게시합니다. 배포 ID는 `.openai/hosting.json`에 저장되어 있습니다. 원문 HTML·prose·private 파일·키·토큰은 게시 파일에 포함하지 않습니다. 내보내기는 동결된 숫자/표준 라벨/기간/위치만 허용합니다.

## 화면 구성

- 추출 결과: 입력/후보/개발 참조 일치 개수, 항목 선택, 숫자와 기간 및 원문 근거
- 실행·검증: 처리 흐름, 단위·근거·기간 검사, 합성 반례, 결과 상태
- 범위와 남은 일: 데이터 범위, 사전 제공 문맥, 독립 평가와 날짜/사업부 정책 미완료

회귀 일치율을 새 문서 정확도로 표시하지 않습니다. 모든 후보의 검토 필요 상태를 유지합니다. 웹 화면의 금액 표시는 Decimal 원 문자열을 보존하고 큰 정수는 BigInt로 표시합니다.
