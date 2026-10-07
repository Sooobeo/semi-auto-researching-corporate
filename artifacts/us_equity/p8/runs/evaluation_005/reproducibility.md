# 재현

같은 agent 실행 `integration_012`와 `integration_resume_013`의 카드 의미 hash 일치. 팀원 실제 재실행 미실행.

```powershell
python scripts/p08_run.py --run-dir artifacts/us_equity/p7/runs/<새 ID>
python scripts/p08_verify_package.py --run-dir artifacts/us_equity/p7/runs/<새 ID>
python scripts/p09_build_report.py --run-dir artifacts/us_equity/p8/runs/evaluation_005
python scripts/p09_verify_package.py --run-dir artifacts/us_equity/p8/runs/evaluation_005
```

코드/설정/정책/입출력 hash는 frozen_run_manifest.json 및 upstream run_manifest.json 참조. 제한 원문·키·private·개인 메모는 공개 묶음 제외. 원문 위치 validator는 기존 허용 private Microsoft HTML의 로컬 접근에 의존하므로 이 자료가 없는 환경에서 원문 대조는 미실행입니다. 이미 생성된 최소 사실·카드·보고서 hash 검사는 원문 재배포 없이 가능합니다.
