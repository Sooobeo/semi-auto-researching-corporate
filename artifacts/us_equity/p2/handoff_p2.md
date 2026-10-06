# P03 실행 인계

2026-10-05 · 등록부 `us-p2-0.1.0` · 확보 가능한 Microsoft 공식 표로 실행한 제한 범위 인계.

사용자 지시로 인간 검증의 다음 단계 진행 조건을 `user_waived_requirement`로 해제했다. 인간 독립 주석·일치도·gold는 측정하지 않았다. P03에서는 실제 표 수치에 연결한 등록부·별칭·단위/비교 규칙과 동일 기업의 새 실적 문서 적용을 만들었다. NVIDIA와 추가 섹터는 이 실행의 선정 기업·확보 성공 분모에 포함하지 않는다.

| 단위 | 실제 결과와 분모 |
| --- | --- |
| 선정 기업 | Microsoft 1개. NVIDIA는 미확보 후보 1개로 별도 보존. |
| 숫자 표본 문서·발표 family | FY2024 Q4 / FY2025 Q4 release 2문서·2 family. 회계범위 확인용 FY2025 연차보고서는 추가 참조이며 숫자 표본 분모에 더하지 않음. |
| source numeric occurrence | 33개: 전사 24, 사업부 9. FY2024 release 15, FY2025 release 18. 전년도 비교열 3개는 후속 문서 공개시점을 따름. |
| 등록 metric | 14개: 실제 관측 7, 프로젝트 계산 정의 2, selected cell 미관측 후보 5. 선정 기업 분모 1; 문서/family/기업/기간 수는 개별 catalog 행에서 재계산. |
| 재무 개념·entity | 개념 7개. entity 5개: 선정 회사 1 + 보고 사업부 3 + 미채택 회사 후보 1. 회사별 회계정책의 전체 감사 완료를 뜻하지 않음. |
| 관계·별칭 | `reports_segment` 주장 6개, 고유 회사→사업부 endpoint 3개. 관계 정의 6개 중 source-selected 1, candidate 5. 전사 재무 label의 source-scoped alias 14개. 고객·공급·경쟁을 실제 확보했다고 세지 않음. |
| 단위·driver | 단위 정책 9개. direct scale만 자동 변환하며 FX/%↔%p/누적차분/부호는 별도 guard를 요구. driver 4개 중 등록 계산 2, 관측 입력 없는 물리 driver 후보 2. |
| 적용 점검 | 동일 기업의 새 release 18개 source claim. 전사 12개는 기존 정의를 사용하고 사업부 6개는 다른 presentation version을 보존. 필드별 assessment 72행. 정확도 분모가 아님. |
| 감사 | source agent의 selected numeric cell 값·scale·Unicode span 왕복 33/33, 원 기간/year header 셀 대조 33/33, private 원본 hash 3/3. 전체 본문 완전성 감사 0, 인간 독립 감사 0. 비교 엔진·독립 구현 QA 결과는 각 report 참조. |

실제 예외는 Intelligent Cloud의 FY2024 연매출이 FY2024 release에서 **105,362 USD million**, FY2025 release의 FY2024 비교열에서 **87,464 USD million**으로 표시된 점이다. `msft-segment-presentation-fy2024`와 `msft-segment-presentation-fy2025`를 분리하고 두 수치와 위치를 보존했다. 같은 사업부 이름·같은 과거 기간이라는 이유로 자동 delta를 만들지 않는다. source 표시는 확인했지만 변화 원인·회계정책 본문은 이 표본에서 해석하지 않았다. Productivity and Business Processes / More Personal Computing도 이전 release와 새 비교열 표시값을 각각 보존한다.

기본 전사 metric 정의는 source sidecar와 같은 `us-financial-0.1`, 일반·후보 정의는 `0.1.0`이다. revenue catalog의 accepted definition 목록은 **scope마다 원 claim version을 반드시 확인해야 하는 목록**이며 서로 교환할 수 있는 정의가 아니다. 전사 연결 범위는 `scope_corroboration.json`의 공식 연차보고서 위치·로컬 feature 확인으로 보완했고, 정확 발행시각은 계속 미상이다. 이 추가 정책 근거는 2026년 관측이며 과거 발행일·가용시점을 확인하지 않았으므로 2024/2025 당시 사용 가능했다고 소급하지 않는다. FY2024 366일 / FY2025 365일은 실제 연간 날짜를 보존하며 윤년 조건은 comparison rule에서 명시한다.

`baseline_registry_0.1.0/manifest.json`은 FY2024-only 재구성 등록부 8개 파일의 hash를 고정했다. 수집 과정에서 FY2025 사실도 보았으므로 이 적용은 **사후 동일 기업 adaptation**이다. 독립 회사 holdout·다른 섹터 일반화·블라인드 적용으로 보고하지 않는다. 현재 독립 평가용으로 예약·확보한 미사용 문서/사건은 0개다.

source의 `numeric_value`는 원 scale의 Decimal 문자열이고 `numeric_value_base_units`는 단위 정규화 값이다. occurrence에는 두 값과 scale, capex 원 괄호 음수·양의 cash outlay 부호 규칙이 모두 있다. 엔진 계산 입력은 `normalized_claims.jsonl`의 base USD 값·scale 1을 사용한다. 계산값은 derived이며 company FCF claim이나 새 원문 occurrence에 포함하지 않는다. 선정 표에 나온 cash PP&E line만 capex 경계로 삼으며 전체 투자현금흐름·비현금 finance lease를 더하지 않는다.

P03-T01~T08은 이 소표본과 구현 범위에서 실행했다. T03의 추가 회사 작업은 확보 가능 범위의 예외로 보류했고 T09의 인간 부분은 면제, 등록부 hash 고정은 수행했다. T10~T11은 동일 기업 새 release의 노출된 adaptation으로 실행했다. T12는 이 패키지 인계다. source 조건·동일 이름 KPI·사업부 표시 원인·추가 회사·미사용 평가 세트는 제한으로 남는다.

P04에는 지표 ID·source alias의 scope/정의 조건, segment entity/`reports_segment` sidecar 확장, exact date/윤년·GAAP/non-GAAP·balance/flow 조건을 전달한다. 사람 검증 면제를 source 오류나 미공개 값 해결로 쓰지 않는다. agent draft를 gold로 승격하지 않고 새 독립 평가자료는 별도 확보한다. 기존 한국기업 자료·등록부·4건/186블록은 입력하지 않았다.

새 파일은 `metric_sampling.md`, `metric_catalog.csv`, `metric_occurrences.csv`, `occurrences_company_a.csv`, `occurrences_company_b.csv`, `accounting_concept_catalog.csv`, `entity_catalog.csv`, `relation_catalog.csv`, `business_relations.jsonl`, `alias_registry.csv`, `unit_rules.csv`, `definition_history.csv`, `driver_edges.csv`, `ontology_decisions.md`, `transfer_manifest.csv`, `transfer_cases.jsonl`, `transfer_assessment.csv`, `task_status.csv`, 이 인계 문서와 baseline registry 디렉터리다. root가 작성하는 `comparability_rules.md`, `normalized_claims.jsonl`, 비교/QA 보고서와 최종 등록부 manifest는 별도 파일이다.

재현 입력은 `../p0/available_20261005/facts_v0_3.jsonl`, `business_relations.jsonl`, source registry/conditions, private DOM reference hash·XPath다. 앞선 `facts.jsonl`과 baseline snapshot을 보존해 변경 전 결과를 추적한다. 원문 private HTML을 공유 산출물이나 Git에 넣지 않는다.
