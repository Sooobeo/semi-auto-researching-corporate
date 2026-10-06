# P03 실행 브리핑 — 확보 가능한 공식 자료 적용

실행 기준 2026-10-05 · 최종 확인 2026-10-06 · P03 = Phase 2 · 등록부 `us-p2-0.1.0`.

사용자의 “인간 검증은 했다고 치고 다음꺼 해봐 확보할 수 있는 자료들 선에서 해결해” 지시에 따라 P03의 인간 검토 진입 조건을 면제하고, 실제 확보한 Microsoft 자료로 지표·보고 사업부 등록부와 단위·비교 규칙을 실행했다. 확보 범위의 P03 패키지를 작성했으며 다음 P04에 인계할 수 있다. 사람의 독립 주석·일치도·gold는 관측하거나 생성하지 않았다. [진행 근거](progression_authorization.json), [작업별 상태](task_status.csv), [인계](handoff_p2.md).

## 확보·권리·검증 분모

| 단위 | 시도·실제 결과 |
| --- | --- |
| 선정 기업 | Microsoft 1개 / 선정 분모 1개. NVIDIA는 미확보 후보로 남김. |
| 새 직접 접근 | 정책 3요청 + 자료 3요청 = 6요청 / 6 HTTP 200. 기존 SEC 차단 경로는 재시도하지 않음. |
| 숫자 자료 | FY2024 Q4·FY2025 Q4 공식 release 2문서 / 2 발표 family. 현재 연도·Q4·기말 잔액과 사업부 비교열을 분리. |
| scope 보완 자료 | FY2025 annual report 1문서. 숫자 문서·실적 발표 family 분모에 추가하지 않음. manifest의 참조 family 1개는 별도 범주. |
| 숫자 occurrence | 33건 = 전사 24 + 사업부 연매출 9. FY2024 release 15 + FY2025 release 18. 고유 기사 확보·문체 비교는 이번 작업의 대상이 아님. |
| 원문 셀 감사 | 값·배율·Unicode span 33/33, 특정 기간/연도 header 33/33, 보관 원본 hash 3/3. |
| 보고 관계 | 회사→사업부 `reports_segment` 6 발표 주장 / 고유 endpoint 관계 3개. 고객·공급·경쟁 관계로 세지 않음. |
| 실제 비교 | 21쌍 / 계산 가능 15쌍, 정의 차이로 차단 6쌍. 시스템 정확도·독립 평가 지표가 아님. |
| 본문·사람·AI | 전체 본문 완전성 감사 미실행, 독립 인간 주석/gold 0건, 기업 원문 prose AI 입력·학습 0건. 인간 게이트는 사용자 면제. |

권리 근거는 공식 [Microsoft Terms of Use](https://www.microsoft.com/en-us/legal/terms-of-use)의 Documents 조건과 2026-10-05 확인 기록이다. 개인/비상업 정보 참조 범위의 소량 로컬 읽기로 제한했다. 고지 포함 원본은 Git 제외 `private/`에 보존하며 공개 산출물은 숫자·기간·표 위치·표준 label·관계 등 비표현적 사실 참조다. 이 운영 판단을 상업적 운영·원문 공유·AI 이용권으로 확대하지 않는다. robots/HTTP 성공과 이용권은 별도다. 출처별 권리 축·요청 기록·실패 이력은 [source_conditions.md](../p0/available_20261005/source_conditions.md), [source_registry.csv](../p0/available_20261005/source_registry.csv), [source_run_manifest.json](../p0/available_20261005/source_run_manifest.json)에 있다.

## 만든 등록부와 실제 적용

- metric 14개: 실제 관측 7개, 프로젝트 수식 2개, selected cell 미관측 후보 5개.
- 회계 개념 7개, entity 5개(선정 회사 1 + 사업부 3 + 미선정 회사 후보 1), relation 정의 6개(관측 1 + 후보 5).
- 별칭 14개, 단위 정책 9개, driver 4개, 정의 변경 이력 4개.
- FY2024 기반 registry 8파일 hash를 보존하고 FY2025 source claim 18건에 적용했다. 전사 12건은 기존 정의를 사용하고 사업부 6건은 표시 정의 예외로 기록했다. 필드 assessment 72행은 정확도 분모가 아니다.
- 원 값과 scale을 보존하면서 33/33건을 base USD로 명시적 변환했다. 최종 결과는 [applied_002](applied_002/run_manifest.json)이며 이전 `applied_001`과 source v0.1/v0.2는 보존했다.

같은 회사의 두 자료는 확보 때 이미 노출됐으므로 이 적용은 **사후 동일 기업 adaptation**이다. 다른 기업·섹터 holdout, 블라인드 전이, 산업 일반화 또는 untouched 평가로 보고하지 않는다. 후속 평가용 미노출 예약 사례는 0건이다.

## 실제 비교로 얻은 결과

아래 단위는 USD million이다. 각 값은 회사 보고 unaudited 표이며 변화율은 이 프로젝트의 계산값이다. FY2024 366일/FY2025 365일은 실제 calendar anniversary 조건으로 비교했다. [FY2024 공식 release](https://www.microsoft.com/en-us/Investor/earnings/FY-2024-Q4/press-release-webcast), [FY2025 공식 release](https://www.microsoft.com/en-us/Investor/earnings/FY-2025-Q4/press-release-webcast).

| 전사 연간 지표 | FY2024 | FY2025 | 차이 | 계산 변화율 |
| --- | ---: | ---: | ---: | ---: |
| 매출 | 245,122 | 281,724 | +36,602 | +14.93% |
| 영업현금흐름(CFO) | 118,548 | 136,162 | +17,614 | +14.86% |
| 현금 PP&E 지출(capex, 양의 지출) | 44,477 | 64,551 | +20,074 | +45.13% |

각 숫자의 원문 셀·header·raw sign·배율은 [facts_v0_3.jsonl](../p0/available_20261005/facts_v0_3.jsonl), 정규화·계산 계보는 [normalized_claims.jsonl](applied_002/normalized_claims.jsonl), [comparability_results.jsonl](applied_002/comparability_results.jsonl)에 있다. capex는 선택한 현금 PP&E line으로 한정하며 비현금 투자/finance lease를 합치지 않았다. 프로젝트 FCF·margin 수식은 등록했지만 수식 실행·대사는 P07 작업으로 남겼다.

중요한 예외는 **Intelligent Cloud FY2024 매출**이다. FY2024 release는 105,362, FY2025 release의 FY2024 비교열은 87,464를 표시한다. 이름·기간이 같아도 두 발표의 표시 정의를 분리해야 한다. 세 사업부의 이전 표시→새 표시 비교 6쌍은 차이를 계산하지 않았고, FY2025 발표 내 같은 표시 기준의 전년 비교 3쌍은 허용했다. 정확한 재분류 원인·정책 범위는 표만으로 확정하지 않았다. [definition_history.csv](definition_history.csv), [비교 규칙](comparability_rules.md).

연결 회계범위 보완 자료의 정확 발행일은 미확인이고 관측일은 2026-10-05다. 이 근거는 availability dependency로 연결했다. 이번 계산은 현재 시점의 비교이며 과거 cutoff에서 이 보완 근거를 이용한 계산을 차단한다. [scope_corroboration.json](../p0/available_20261005/scope_corroboration.json).

## 검증과 재현

독립 구현 검사는 통화·scope·정의·GAAP/non-GAAP·balance/flow·기간·윤일/53주·scale·비율 분모·%/%p·YTD·시점 누수를 확인했다. 반례 59/59, 원문 source/변환 33/33, 실제 비교 재계산 21/21이 통과했다. 검사 그룹 23개 통과, P04 미노출 평가 검사는 범위 밖으로 미실행 1개다. 최종 등록부 35파일·출처 입력 9파일·코드 4파일 hash가 일치했다. 검사별 결과는 [independent_validation.json](independent_validation.json)에 있다. 이는 구현·표 셀 검증이며 독립 인간 gold나 추출 정확도 측정은 아니다. 최종 파일 hash·코드 hash·active revision은 [registry_v0.1_manifest.json](registry_v0.1_manifest.json)에 고정한다.

```powershell
python scripts/p03_apply_registry.py --facts artifacts/us_equity/p0/available_20261005/facts_v0_3.jsonl --audit artifacts/us_equity/p0/available_20261005/extraction_audit_v0_3.csv --output-dir artifacts/us_equity/p2/applied_003 --as-of 2026-10-05
python scripts/p03_verify_registry.py --report artifacts/us_equity/p2/independent_validation_rerun.json
```

출력 경로는 아직 존재하지 않는 경로를 사용한다. 재현은 로컬 감사 파일을 읽으며 네트워크 재수집을 하지 않는다. private 원본이 없는 환경은 원문 재조회 검사를 동일하게 수행할 수 없다.

## 새·변경 파일과 후속 인계

새 source package는 `p0/available_20261005/`, 등록부·정의·적용·QA는 `p2/`이다. 새 코드는 `scripts/p03_source_facts.py`, `p03_comparability.py`, `p03_apply_registry.py`, `p03_verify_registry.py`이며 repo README·structure README·P01~P03 설계서·공통 규약·DECISIONS에 현재 결과 링크를 추가했다. 개별 파일 크기·hash는 [artifact_inventory.csv](artifact_inventory.csv)에 있다. 이전 P01/P02 실행 브리핑·실패 자료·한국기업 결과는 보존했고 한국기업 자료를 이번 입력으로 사용하지 않았다.

P04는 이 ID·scope·발표 family·노출 이력·원문 좌표를 받아 주석 양식과 분할 기준을 연결할 수 있다. 다만 새로운 인간 gold를 꾸미거나 노출 자료를 untouched test로 바꾸지 않는다. 미확보 항목은 NVIDIA/다른 기업·섹터, 고객/공급/제품 관계, 원문 prose NLP 이용권, 전체 본문 추출, 정확한 사업부 표시 변경 정책과 미노출 평가 자료다. 확보 범위에서 가능한 비교·등록부 작업은 완료했으며 이 항목들은 후속 범위로 남긴다.
