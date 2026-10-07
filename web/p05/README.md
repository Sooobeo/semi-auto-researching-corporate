# P05 웹 화면

## P08·P09 현재 구현 — 2026-10-07

통합 카드·실행 현황·파일 기반 검토 이력·비교 검증/평가를 추가했습니다. 현재 게시 대상은 P08 `integration_012`(후보39→카드33), P09 `evaluation_005`입니다. 실제 게시 버전/상태는 해당 run의 site_update_manifest.json에 기록합니다. [실제 운영 명령](../../artifacts/us_equity/p7/operator_guide.md)을 참조하세요.

같은 로컬 서버의 ‘내 PC 통합 실행’은 P05 추출/위치 검증→P07→P06→카드→feedback snapshot→검증을 실행합니다. 검토 초안은 이 기기에만 저장되며 파일로 내보내고 소유자가 로컬에서 검증해 가져온 뒤 새 결과를 재게시합니다. 정적 공유 화면은 PC 원격 실행·자동 공동 저장을 하지 않습니다. 원래 후보는 보존하고 충돌/자체 신고 actor·시각/학습 제외를 명시합니다.

P09는 S0/S1/S3의 같은 개발 입력 비교, 공학 검사12/12·합성/장애 반례37/37, 전체 보류/미계산124 결과를 보여줍니다. 독립 정확도·중요성·검색 Recall·사람 사용성·검토시간 절감은 미평가입니다. 사람 gold·qrels·독립 test·사람 세션0, 전체 비용·1000문서 비용·메모리 peak 미측정입니다. 기존 P05/P06/P07 결과 조회는 유지합니다.

```powershell
python web/p05/integration_snapshot.py --p08-run artifacts/us_equity/p7/runs/integration_012 --p09-run artifacts/us_equity/p8/runs/evaluation_005
node web/p05/verify-integration.mjs
```

아래는 이전 단계의 운영 이력입니다. 상단의 통합 기능과 함께 사용할 수 있습니다.

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

## 다음 Phase에서의 화면 갱신

2026-10-06 사용자 요청에 따라 P06~P09 실행 때 이 사이트의 기능·결과도 함께 갱신하고 같은 프로젝트에 게시합니다. 주소는 `https://corporate-research-p05.sooobeo.chatgpt.site`를 계속 사용하며 현재 2인 접근을 유지합니다. Phase별 기능과 검증은 [실행 로드맵](../../structure/P06_P09_execution_roadmap.md), 게시 절차와 내보내기 범위는 [사이트 업데이트 계약](../../structure/SITE_PHASE_UPDATE_CONTRACT.md)을 따릅니다.

현재 `snapshot.py`와 서버의 실행 버튼은 P05용입니다. 후속 실행 때 해당 Phase adapter와 화면을 실제 구현하고 검증합니다. 문서 작성만으로 새 Phase가 실행되거나 사이트가 자동 동기화된 것은 아닙니다.

## P06·P07 실제 구현 — 2026-10-06

검토할 항목, 이전 정보와 비교, 재무 계산 화면을 추가했습니다. P06 `review_change_003`, P07 `change_002`의 검증 결과 snapshot을 사용합니다. P05 기존 추출·로컬 실행은 유지하며 버튼에 `P05 추출 재실행`을 명시했습니다. P06·P07을 브라우저 버튼으로 실행하거나 공동 저장하는 기능은 없습니다.

실행 CLI는 아래와 같습니다. 존재하지 않는 새 run 경로를 사용해야 하며, 기존 결과를 덮어쓰지 않습니다.

```powershell
python scripts/p06_run.py --run-dir artifacts/us_equity/p5/runs/<새 ID>
python scripts/p07_run.py --run-dir artifacts/us_equity/p6/runs/<새 ID>
python scripts/p06_run.py --run-dir artifacts/us_equity/p5/runs/<후속 ID> --change-run artifacts/us_equity/p6/runs/<새 ID>
python scripts/p06_verify_package.py --run-dir artifacts/us_equity/p5/runs/<후속 ID>
python scripts/p07_verify_package.py --run-dir artifacts/us_equity/p6/runs/<새 ID>
python web/p05/phase_snapshot.py --p06-run artifacts/us_equity/p5/runs/<후속 ID> --p07-run artifacts/us_equity/p6/runs/<새 ID>
python web/p05/verify_contracts.py
node web/p05/verify-phases.mjs
```

P07 기본 실행은 세 모드를 모두 검사합니다. `--cutoff-mode historical_public`, `observed_live`, `current_review`와 선택적 `--cutoff`를 지원합니다. 과거 모드 기본 cutoff는 각 새 발표 날짜입니다. 현재 재검토 기본 기준일은 이 개발 실행의 2026-10-06이며 다른 날짜 작업에는 cutoff를 명시합니다.

현재 후보 39개는 검토 묶음 33개, 발표 family 2개입니다. 현재 재검토의 변화 계산은 15/42건(전사 독립 발표 쌍 12 + 동일 발표 사업부 비교열 3), 공식 계산은 8/8건입니다. 당시 공개 모드의 3/42건은 같은 발표의 비교열이며 독립 prior 검색 성과가 아닙니다. 관측 모드 변화는 0/42건입니다. 사람 gold·qrels·중요성 모델·정식 성능은 미실행입니다.

`phase_snapshot.py`는 새 Phase용 allowlist adapter입니다. 원문 prose·private 경로·키·사람 메모를 내보내지 않습니다. `phases.json` 생성만으로 게시 화면이 갱신되지 않으며 같은 Sites 프로젝트의 새 버전 게시가 필요합니다. 실제 배포 상태는 각 활성 run의 `site_update_manifest.json`을 확인합니다. 기존 2인 접근을 변경하지 않습니다.
