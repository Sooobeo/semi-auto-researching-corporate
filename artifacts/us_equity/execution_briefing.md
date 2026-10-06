# structure 파악 및 P01·P02 실행 브리핑

기준일: 2026-10-05 · 방향 structure v1.2 · 실행 초안 0.1 · 인간 검토 대기

**미국 기업 신규 프로젝트의 P01 출처·접근 조사를 수행하고 P02 문헌·스키마·가이드 초안을 작성했다. 실제 미국 원문 확보와 두 사람 이상의 독립 양식 시험이 남아 있어 두 단계 전체 완료로 보고하지 않는다.**

## 구조에서 확인한 흐름

P01 파일은 Phase 0(자료 가능성), P02는 Phase 1(선행연구와 개념/사건/관계 단위)이다. 이어서 P03 등록부·비교 규칙, P04 독립 주석·gold·분할, P05 추출 baseline, P06 검토 우선순위, P07 시점 제한 검색/변화/계산, P08 검토 카드, P09 비교 평가 순서다. 작업 ID 103개는 계획 식별자이며 완료 수가 아니다.

핵심 결과는 ‘새 정보가 기존 상태를 어떻게 바꾸는가’를 영문 원문 근거·불확실성·추가 확인 사항과 연결한 검토 카드다. 초기 배치·로컬 MVP를 유지한다. 온톨로지/NLP·사업 분석은 공통 목표이고 재무회계·투자 리서치 적용은 선정 사례의 개인 목표다. 모델 성능과 개인의 실제 이해·계산·수정 증거는 별도로 평가한다.

현재 미국 방향과 충돌하는 루트 README의 한국기업 설명에 현행 방향 링크를 추가했다. 기존 한국기업 자료·완료 결과·4건/186블록 검증은 신규 입력이나 미국 성과에 포함하지 않았다. 이전 파일의 물리적 삭제나 외부 Notion/Jira 변경은 하지 않았다.

## P01 결과

[범위](p0/scope.md), [출처 registry](p0/source_registry.csv), [조건 검토](p0/source_conditions_review.md), [접근 가능성 보고](p0/data_feasibility.md), [작업별 상태](p0/task_status.csv)를 작성했다.

| 항목 | 이번 실행 결과 |
| --- | --- |
| 기업 후보 | Microsoft·NVIDIA 2개; 팀 채택·기간 미확정 |
| 조건 조사 출처 | SEC 3경로 + 발행사 IR 2경로 = 5개 |
| 직접 robots 접근 | 성공 0 / 시도 2; 각각 HTTP 403 |
| API endpoint | 실제 시도 0 / 후보 4; 호스트 중단 후 보류 |
| 실제 API payload·공시 문서·완전 본문 | 0 / 0 / 0 |
| 자동 추출률·본문 접근률 | NA; 해당 분모 0 |
| 고유 기사·기사–사건 링크·발표 family | 0 / 0 / 0 |
| 독립 표현·동일 주장 매체 간 비교 쌍 | 0 / 0 |
| 수동 원문·표 감사 | 미실행 |
| 원문 LLM 입력·학습 | 0회 / 0회 |

SEC의 [재사용 FAQ](https://www.sec.gov/about/webmaster-frequently-asked-questions)와 [자동 접근 안내](https://www.sec.gov/search-filings/edgar-application-programming-interfaces)를 확인했다. 안내상 이용 가능성과 현재 환경의 실제 접근 성공은 다르다. AI 원문 입력/학습 조건은 unresolved로 남겼다. Microsoft IR의 코퍼스 사용과 NVIDIA IR 자동 접근 조건도 보류하여 크롤링을 확대하지 않았다.

수집기 [p01_us_sec_pilot.py](../../scripts/p01_us_sec_pilot.py)는 권리 registry gate, 1초 요청 간격, 403/429 후 호스트 중단, 자동 redirect 중단, 별도 run 출력·원본 보존, 안전한 경로·run ID, companyfacts 숫자/기간/JSON pointer 계보를 구현했다. 공시 HTML/PDF 본문·표 파서는 미구현이며 실제 추출도 미시험이다. `.gitignore`에 미국 raw/private/body/blocks 제외를 추가했다. 활성 결과는 [pilot_20261005_002](p0/pilot_20261005_002/run_manifest.json)이고, 첫 실패 기록 001도 보존했다. 같은 API 후보를 두 run의 고유 8개 후보로 합산하지 않았다.

## P02 결과

P02는 문헌 검색→읽은 절/페이지·도메인 한계→규칙→반례→검증 계획을 연결했다. [research map](p1/research_map.md), [문헌 matrix](p1/literature_matrix.csv), [사건 양식](p1/event_schema.md), [관계 양식](p1/relation_schema.md), [가이드](p1/annotation_guide_draft.md), [중요성 질문](p1/materiality_questions.md), [인계](p1/handoff_p1.md)를 작성했다. Primary 자료 14개를 등록했고 본문 일부·초록·공식 개요·본문 미접근을 구분했다. 전체 14개를 정독했다고 보고하지 않는다.

기본 사실 단위는 atomic claim이며 문서·revision·사건·발표 family·사업 관계 tuple을 구별한다. 원시값/정규화값/assessment/derived, 발표/실적 대상/적용/관측 시점, 전사/사업/제품, 회계분기/달력분기, 계획/전망/발표실적을 분리한다. 관계가 있다는 주장으로 매출·이익 영향을 계산하지 않는다.

실제 미국 사건·주장·관계 예시는 0건이다. 양식 예시는 명시적 합성 사례이며 gold나 정확도 benchmark가 아니다. 실제 새 사례로 두 사람 이상이 설명 없이 독립 작성하는 P02-T10은 미완료이고 일치도를 보고하지 않는다. 독립 agent QA와 JSON Schema 검사는 인간 검증을 대체하지 않는다.

## 검증과 변경 파일

- P01 정책·경로 회귀 테스트: 14개 통과, 실제 네트워크 요청 0건.
- P01 입력 manifest 기반 QA: 메타데이터 검사 11개 통과, 원자료가 필요한 검사 9개 미실행, 실패 0개. [보고서](p0/validation_report.json)는 분모 0인 접근/추출률을 null로 기록한다.
- P02 합성 계약 검사: 정상 예시 6개 유효, 오류 입력 22개를 예상대로 거부하여 총 28/28 통과. [보고서](p1/schema_validation_report.json)는 실제 사례·인간 주석·gold 모두 0으로 명시한다. 합성 검사는 실제 추출 정확도가 아니다.
- Python 컴파일·Markdown 내부 링크·Git whitespace 확인을 실행했다. legacy 산출물 변경은 없다.

새 파일은 `artifacts/us_equity/p0/` 조건·실패·coverage·인계·검증과 별도 run 2개, `p1/` 문헌·스키마·합성 사례·가이드·인계, `scripts/p01_us_sec_pilot.py`, `scripts/p01_us_verify.py`, `scripts/p02_build_schema.py`, `scripts/p02_validate_schema.py`, `scripts/p02_requirements.txt`, `tests/test_p01_us_sec_pilot.py`다. 변경한 기존 파일은 `.gitignore`, 루트 README, structure의 README·P01·P02·DATA_CONTRACTS다. [전체 파일·hash 목록](artifact_inventory.csv)과 [통합 검증 요약](verification_summary.json)을 함께 보관한다.

## 미해결 사항과 다음 순서

1. 최초 기업·사업 scope·회계기간·인간 담당·검토자·가용시간·개인 재무 과제를 정한다.
2. 정상 이용조건을 충족하는 경로에서 작은 원본 표본을 확보한다. 이번에 차단된 SEC 호스트 재시도나 대체 우회는 하지 않았다.
3. 문서·문단·표 원문을 대조해 본문 완전성, 숫자·scale·USD·기간 길이·scope·GAAP 정의·날짜 충돌을 감사한다. 지금 이 항목은 검증 미실행이다.
4. P02의 합성 예시를 실제 근거·span 사례로 보완한 후 미노출 실제 사례의 인간 독립 시험을 수행한다.
5. P03 등록부를 실제 표본으로 고정하고 P04 gold·분할 계획으로 넘긴다. 개발에 사용한 새 표본은 adaptation으로 관리한다.

P01의 자료 확보 및 인간 인계, P02의 실제 예시·인간 사용성 검증을 완료로 승격하지 않는다.
