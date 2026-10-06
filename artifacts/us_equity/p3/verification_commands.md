# P04 검증 재실행

저장소 루트에서 실행한다. 아래 검증은 네트워크를 사용하지 않고 기존 결과를 덮어쓰지 않는다. 예약 문서의 본문·숫자를 열지 않는다. 최종 패키지 확인과 agent 재계산은 Python 표준 라이브러리만 사용한다.

```powershell
python -X utf8 scripts/p04_verify_package.py
```

상세 재계산은 저장소 밖 새 임시 폴더에 보고서를 쓴다. 기존 데이터의 출력 폴더를 통째로 삭제하거나 builder를 같은 경로에 재실행하지 않는다.

```powershell
$p04VerifyDir = Join-Path $env:TEMP ('p04-verify-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $p04VerifyDir | Out-Null
python -X utf8 scripts/p04_independent_agreement.py --output (Join-Path $p04VerifyDir 'agreement.json')
python -X utf8 scripts/p04_independent_split_audit.py --output (Join-Path $p04VerifyDir 'split.json')
python -X utf8 scripts/p04_validate_handoff.py --report (Join-Path $p04VerifyDir 'handoff.json')
```

원문 계약 검증을 다시 수행할 때는 기존 private 원문 3개와 `lxml`, `jsonschema`가 필요하다. 현재 실행 환경의 기존 격리 의존성은 `$env:TEMP/p02-jsonschema-20261005`이며 별도 환경에서는 해당 의존성을 준비해야 한다. 이 검사는 선택 DOM 셀·머리글·hash·Unicode offset을 비교하고 신규 예약 본문에는 접근하지 않는다.

```powershell
python -X utf8 scripts/p04_contract_validation.py --report (Join-Path $p04VerifyDir 'source-contract.json') --cases (Join-Path $p04VerifyDir 'source-cases.json')
```

소스·최종 파일·코드 hash는 `package_manifest.json`, 공개 파일별 크기/행 수는 `artifact_inventory.csv`에 있다. `package_validation.json`은 manifest 고정 후 검사한 결과라 자기 자신을 hash 목록에 넣지 않았다. private 원문·약관·고지는 공개 목록에서 제외했으며 source manifest의 hash로 로컬 불변 여부만 확인한다.

생성 순서와 이전 실패는 `scripts/p04_stage1.py` → `p04_finish_stage1.py` → 계약 builder/validator 및 `p04_finish_stage2.py` → 연습/가이드 1.1·1.2/본 주석 및 `p04_finish_stage3.py` → `p04_stage4.py`/독립 계산/`p04_finish_stage4.py` → `p04_stage5_prepare.py`/인계·독립 분할 검사/`p04_stage5_docs.py`/`p04_finish_stage5.py`로 추적한다. 외부 출처 재수집은 이 검증 절차에 포함되지 않는다. 각 시점의 가이드와 코드는 revision 폴더에 보존했으므로 현재 스크립트를 초기 버전 재현용으로 혼용하지 않는다.
