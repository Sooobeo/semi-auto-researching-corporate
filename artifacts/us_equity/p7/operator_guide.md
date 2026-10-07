# 실제 운영 명령 · P08/P09

저장소 루트에서 실행한다. P05의 기존 Python 환경과 로컬 jsonschema 캐시를 사용한다. 검증한 최신 결과는 P08 `integration_012`, P09 `evaluation_005`이다. 원문 위치 검증에는 기존 허용 private HTML의 로컬 접근이 필요하며 이를 배포하지 않는다.

```powershell
$env:PYTHONIOENCODING='utf-8'
python web/p05/server.py
```

표시 주소에서 ‘통합 실행·기록 → 내 PC 통합 실행’은 추출→비교→검토→카드→파일 이력 검증을 실제 실행한다. 기존 P05 재실행 버튼도 유지한다. Sites 공유 화면은 원격 실행·자동 공동 저장을 하지 않는다.

새 batch와 복구:

```powershell
python scripts/p08_run.py --run-dir artifacts/us_equity/p7/runs/<새 ID>
python scripts/p08_verify_package.py --run-dir artifacts/us_equity/p7/runs/<새 ID>
python scripts/p08_run.py --run-dir artifacts/us_equity/p7/runs/<실패 ID> --resume
```

기존 경로는 `--resume` 없이 사용하지 않는다. 실패/취소/timeout의 `pipeline_state.json`과 `stage_attempts.jsonl`을 확인한다. 입력/코드/설정이 바뀌면 새 ID를 사용하고 실패 run을 보존한다. 살아 있는 writer가 없는지 확인한 뒤에만 남은 `.writer.lock`을 수동 정리한다.

카드의 검토 초안은 이 기기 localStorage에만 저장되고 파일로 내보낸다. 이름/이메일/개인 메모 대신 별칭·허용된 구조화 값과 근거 ID만 사용한다. 파일은 카드별 원래 값과 run/version을 포함한다. 로컬 화면의 파일 가져오기 또는 CLI로 검증한다:

```powershell
python scripts/p08_import_feedback.py --run-dir artifacts/us_equity/p7/runs/integration_012 --file <내보낸 JSON> --report <검증 결과 JSON>
python scripts/p08_import_feedback.py --run-dir artifacts/us_equity/p7/runs/integration_012 --resolve <conflict_id> --decision adopt --selected <feedback_id> --owner <로컬 운영자 별칭>
```

다른 값을 단순 merge하지 않는다. 채택은 한 feedback를 선택하고, 동일 값의 중복 제안만 merge할 수 있다. 다른 값의 통합안은 새 제안으로 기록한다. defer도 이력으로 남긴다. 같은 logical card version의 이전/다른 run 기록도 보존하고 충돌을 검사한다. 카드 내용/version이 바뀌면 이전 검토를 자동 상속하지 않는다. 피드백은 gold·학습 자료로 자동 승격되지 않는다. 자체 신고 actor/시간은 인증된 저자/시각이 아니다.

반영하려는 source run의 피드백을 새 snapshot에 포함하려면 `integration_012/run_config.json`을 별도 설정 파일로 복사하고 `feedback_source_run`을 `integration_012`으로 바꾼다. 새 run을 `--config <설정 JSON>`으로 실행한다. 로컬 화면의 통합 재실행은 현재 화면 source run을 자동으로 참조한다. 원래 후보·카드는 덮어쓰지 않는다.

P09 측정 전에 protocol을 별도 run에 고정한다:

```powershell
python scripts/p09_run_evaluation.py --init-protocol --run-dir artifacts/us_equity/p8/runs/<새 평가 ID>
python scripts/p09_run_evaluation.py --run-dir artifacts/us_equity/p8/runs/<새 평가 ID> --p08-run artifacts/us_equity/p7/runs/<검증 ID> --reproduction-run artifacts/us_equity/p7/runs/<별도 재현 ID>
python scripts/p09_build_report.py --run-dir artifacts/us_equity/p8/runs/<평가 ID>
python scripts/p09_verify_package.py --run-dir artifacts/us_equity/p8/runs/<평가 ID>
```

현재 evaluator는 development 전용이다. 사람 gold·독립 qrels·사람 세션이 없으면 null을 출력한다. 새로운 독립 평가 목적/권리/노출/정답 protocol이 필요하며 예약 본문을 자동 개봉하지 않는다.

공유 화면 반영 전:

```powershell
python web/p05/integration_snapshot.py --p08-run artifacts/us_equity/p7/runs/<검증 ID> --p09-run artifacts/us_equity/p8/runs/<평가 ID>
node web/p05/verify-integration.mjs
python web/p05/verify_contracts.py
```

이후 Sites skill의 기존 프로젝트 source/version 게시 workflow를 사용한다. 위 명령은 로컬 snapshot만 갱신한다. 같은 사이트 배포 성공을 확인하고 `site_update_manifest.json`에 기록해야 공유 반영 완료다. 접근은 소유자+지정 팀원 2인 유지, raw/private/credential 업로드 금지.
