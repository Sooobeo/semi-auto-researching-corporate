# P08·P09 산출물과 후속 운영 인계

2026-10-07 최종 개발 run: P08 `integration_012`, 재현/복구 `integration_resume_013`, P09 `evaluation_005`. 기존 run·실패 시도·동결 P04/P05 입력/결과를 보존했다. 개발·게시 완료, 사람/독립 연구 평가 미완료다.

## 사용할 진입점

- [같은 사이트](https://corporate-research-p05.sooobeo.chatgpt.site): 통합 카드·원문 위치·시점/기간/scope 비교·검토 질문·실행 현황·파일 초안/내보내기·P09 개발 평가와 전체124 보류/미계산 결과.
- [P08 실행 결과](../p7/execution_briefing.md), [운영 안내](../p7/operator_guide.md), [pipeline 계약](../p7/pipeline_spec.md).
- [P09 실행 결과](execution_briefing.md), [최종 보고](runs/evaluation_005/final_report.md), [system 비교](runs/evaluation_005/system_comparison.csv), [전체 사례](runs/evaluation_005/failure_cases.jsonl), [재현](runs/evaluation_005/reproducibility.md).
- [P08 게시 기록](../p7/runs/integration_012/site_update_manifest.json), [P09 게시 기록](runs/evaluation_005/site_update_manifest.json), 각 active_run.json. 원래 계산/평가 manifest를 수정하지 않고 별도 게시 기록을 작성했다.

## 최종 게시

프로젝트 `appgprj_6ac4af31b39c8191b7d3d8876d313876`, version4 `appgver_e7e514177a3c8191bb6e84582a350084`, deployment `appgdep_6ac5d176ea3c81919b9028e51420f2eb`, 상태 `succeeded`, 게시시각 `2026-10-07T04:58:44.940896+00:00`.

게시 source commit `6adf5fe6de9ecb5fd90499378f155d0110eaf4d5`, snapshot SHA256 `babda23899e29f97ab931ae68aa4ccaa8fed9c4cbd05b6f3bfd41c52b3d1d716`. custom 접근 대상2·revision2를 유지했다. 실제 팀원 접속은 미확인이다. production 페이지를 배포 확인용으로 열지 않았으며 로컬 브라우저 QA와 최종 native 배포 상태를 구분했다.

공유 화면은 snapshot이다. 로컬 Python 실행/소유자 가져오기는 로컬 API 또는 CLI에서 수행한다. 브라우저 초안/파일 내보내기 → 소유자 검증/가져오기·충돌 해결 → 새 run/snapshot·같은 사이트 재게시 절차를 따른다. 자유입력 actor는 self_declared이며 gold가 아니다.

## 새 코드·화면·문서

| 경로 | 이번 변경 |
| --- | --- |
| `scripts/p08_common.py`, `p08_run.py` | 설정/schema/hash·고정 배치·stage 재개/실패 기록 |
| `scripts/p08_cards.py` | 33카드·39후보 연결·원문/비교/계산/질문 adapter |
| `scripts/p08_feedback.py`, `p08_import_feedback.py` | 검증·원자 journal·중복·같은 version의 run 간 충돌·채택/병합/보류 |
| `scripts/p08_verify_package.py`, `p08_test_integration.py` | manifest 계약 및30개 장애/합성 검사 |
| `scripts/p09_common.py`, `p09_run_evaluation.py`, `p09_build_report.py` | 사전 protocol·S0/S1/S3·12개 공학 검사·전체 사례·비용/미평가 보고 |
| `scripts/p09_verify_package.py`, `p09_test_evaluation.py` | 평가 파일/분모/재현 계약 및7개 조건 검사 |
| `web/p05/integration_snapshot.py`, `dist/integration.json`, `dist/integration-schema.json`, `dist/integration.js` | 검증된 allowlist snapshot/schema·카드/평가/파일 UI |
| `web/p05/dist/index.html`, `app.js`, `phases.js`, `styles.css` | 기존 P05~P07 유지·P08/P09 탐색과 desktop/mobile 화면 |
| `web/p05/server.py`, `test_integration_api.py`, `verify-integration.mjs`, `README.md` | loopback 실행/가져오기·Host/Origin/CSRF/파일 검사·로컬 API12개 검사·운영 안내 |
| `artifacts/us_equity/p7/`, `p8/` | 별도 run·cards·journal·검사·평가/사람 protocol·재현·보고·active/게시 기록 |
| `structure/P06_P09_execution_roadmap.md`, `P08_phase7_execution_plan.md`, `P09_phase8_execution_plan.md` | 10/07 실제 실행 상태 추가, 10/06 설계·기존 사용자 변경 보존 |

실패/이전 run은 보존한다. 코드 개정 뒤 이전 run의 code hash가 최신 코드와 다른 것은 최종 run 통과 근거로 쓰지 않는다. 신규 source 수집/학습/LLM·예약 평가 본문 개봉·공개 접근·DB 도입·root Git commit/push는 수행하지 않았다. Sites 게시 source는 기존 프로젝트의 배포 workflow로 저장했다.

## 미완료 연구와 다음 실제 작업

문서2/family2의 개발 결과다. 정확한 발표시각·날짜 충돌·사업부 정의/사후 문맥·보고 관계 유효기간·전체 본문 완전성·순이익→CFO 대사 입력은 미확인이다. 사람 gold·독립 test·qrels·사람 세션/학습 사례0, 동료 재실행 미실행, 비용/메모리 미측정이다.

현재 카드 일괄 검토는 feedback 이력으로 시작할 수 있다. 이를 untouched test로 승격하지 않는다. 정식 평가에는 새 자료를 보기 전 권리/노출/목적과 정답·qrels protocol 고정, 사람 독립 주석, 실제 두 사람의 교차 과업 세션 및 동료 재실행이 필요하다. [미완료 연구 인계](runs/evaluation_005/project_closeout.md)를 따른다.

## Git에 남기는 범위 — 2026-10-07 정리

`.gitignore`는 P08/P09 run을 기본 제외하고 최종 `integration_012`, 재현 `integration_resume_013` 및 그 deadline 증거, 최종 평가 `evaluation_005`만 예외로 남긴다. 최종 package의 단계 출력도 hash 검증과 재현 입력이므로 포함한다. 이전 버전3의 두 site_update_manifest도 게시 이력으로 남긴다. 코드·문서·active 포인터·안전한 웹 snapshot은 커밋 대상이다.

디버그/중간/브라우저 실행, 운영 feedback journal, 브라우저 합성 다운로드, 의존성 환경은 커밋에서 제외한다. 제외된 파일은 삭제하지 않아 이 PC의 실패 기록·run_catalog 이력을 보존한다. 새 checkout에 중간 run이 모두 있다는 뜻은 아니다. 다음 run을 정식 결과로 승격할 때는 `.gitignore`의 예외와 active/게시 기록을 함께 갱신한다. raw/private/본문/자격증명 제외 규칙은 유지한다.
