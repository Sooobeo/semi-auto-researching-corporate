# 실제 실행 및 재검증 명령

저장소 루트의 PowerShell에서 실행한다. Python 3.13.3과 requirements.lock의 기존 로컬 설치를 사용했다. jsonschema가 기본 경로에 없으면 %TEMP%/p02-jsonschema-20261005를 읽는다. 네트워크 설치/호출은 없다.

```powershell
$env:PYTHONIOENCODING='utf-8'
python scripts/p04_verify_package.py
python scripts/p05_verify_package.py
```

기존 파일 덮어쓰기를 거부한다. 아래 출력 폴더/보고서가 없을 때만 새 이름으로 실행한다.

```powershell
python scripts/p05_test_baseline.py --stage inputs --report artifacts/us_equity/p4_checks/inputs.json
python scripts/p05_test_baseline.py --stage rules --report artifacts/us_equity/p4_checks/rules.json
python scripts/p05_rule_baseline.py --run-id recheck_001 --output-dir artifacts/us_equity/p4_checks/recheck_001
python scripts/p05_validate_predictions.py --run-dir artifacts/us_equity/p4_checks/recheck_001
python scripts/p05_compare_reference.py --run-dir artifacts/us_equity/p4_checks/recheck_001
python scripts/p05_test_evaluation.py --run-dir artifacts/us_equity/p4_checks/recheck_001 --report artifacts/us_equity/p4_checks/evaluation.json
```

실제 단계 순서는 prepare_inputs --stage protocol → --stage inputs → 합성 입력 검사/2단계 gate → 규칙 검사/추출/3단계 gate → validate_predictions → compare_reference → qualifier-fix 및 재실행 → 비교 반례/4단계 gate → 별도 폴더 재현 → finalize --stage 5 → verify_package다. 실행별 파일에 시각과 code/input/schema/rule/dependency hash가 있다. 현재 최종 실행은 m0_004, 재현은 m0_repro_005이다. 추출기 CLI는 명시적 stage_02_final을 요구하므로 검토 gate를 자동으로 가장하지 않는다.
