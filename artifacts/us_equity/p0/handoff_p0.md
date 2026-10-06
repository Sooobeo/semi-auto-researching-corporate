# P01 → P02/P03 인계 · 실행 초안 0.1

기준일 2026-10-05. 현행 구조 v1.2의 미국 신규 프로젝트다. [범위](scope.md), [가능성 결과](data_feasibility.md), [출처 조건](source_registry.csv)을 먼저 읽는다. 활성 입력에 한국기업 artifact가 없다.

인계 가능한 것은 5개 출처의 조건/실패 기록, 임시 기업 후보와 coverage 빈칸의 이유, 수집기와 입력 manifest 기반 QA, P02 문헌·스키마 초안이다. 실제 미국 문서·주장·사업 관계·gold는 확보하지 못했다. 모든 P01 작업을 완료했다고 보고하지 않는다.

```powershell
python scripts/p01_us_verify.py --manifest artifacts/us_equity/p0/pilot_20261005_002/api_payload_manifest.csv --report artifacts/us_equity/p0/validation_report.json
```

수집기는 output이 새 디렉터리여야 하며 현재 차단된 두 호스트를 전달하면 네트워크 재시도가 없다. 아래는 실패 보존 재현 명령이며 자료 확보 명령이 아니다.

```powershell
python scripts/p01_us_sec_pilot.py --output artifacts/us_equity/p0/pilot_20261005_replay --run-id us-sec-pilot-20261005-replay --blocked-host data.sec.gov --blocked-host www.sec.gov
```

정상 접근 여부와 권리를 새로 확인하기 전 차단 인자를 해제하지 않는다. 제3자 인간의 manifest만을 이용한 원문·표 확인, 새 문서 등록 시험은 미실행이다. 실제 원문이 생기면 hash·JSON pointer 또는 XPath·표 머리글·숫자/기간/scope·날짜를 대조하고 가이드 개발 자료는 adaptation으로 기록한다. 기업별 GAAP/non-GAAP 정의와 재무 개념 적용도 원문으로 다시 확인해야 한다.
