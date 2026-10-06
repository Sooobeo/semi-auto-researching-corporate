# P01 데이터 가능성 실행 결과 · 2026-10-05

**미국 소표본의 출처 조사와 재현 가능한 수집 준비를 수행했지만, 실제 원문/API 자료 확보는 미완료다.** SEC의 공개 재사용·programmatic access 안내를 확인했다. 정상 application 식별 User-Agent로 서로 다른 SEC 호스트의 robots를 각 1회 조회했으나 둘 다 403이었다. 호스트를 중단하고 API·문서 요청이나 우회를 하지 않았다.

## 출처와 권리

[source_registry.csv](source_registry.csv)는 SEC submissions API·companyfacts API·Archives·Microsoft IR·NVIDIA IR의 5개 출처를 기록한다. [조건 검토](source_conditions_review.md)에는 원문 근거와 실제 적용 판단을 구분했다.

- SEC: [공식 FAQ](https://www.sec.gov/about/webmaster-frequently-asked-questions)의 EDGAR public filing 재사용 안내와 [API 문서](https://www.sec.gov/search-filings/edgar-application-programming-interfaces)의 자동 접근 조건을 확인했다. 로컬 비AI 사실 추출은 조건부 후보다. AI 입력/학습은 별도 명시를 찾지 못해 unresolved로 보존했다.
- Microsoft IR: Documents의 제한적 이용조건을 코퍼스·AI 처리 허용으로 확장하지 않았다.
- NVIDIA IR: 일반 약관의 자동 도구 제한과 IR 적용성 미확인을 별도로 기록하여 자동 수집을 보류했다.

공개/robots 허용/HTTP 성공을 이용권의 대체 근거로 사용하지 않았다. 원문 외부 LLM 전송·학습은 0회다.

## 실제 분모·분자

| 단계·단위 | 결과 | 해석 |
| --- | --- | --- |
| 조건 조사 출처 | 5개 | 조사 기록이며 본문 확보 수가 아님 |
| 후보 기업 | 2개 | 팀 채택 미확정 |
| 직접 robots HTTP 조회 | 성공 0 / 시도 2 | data.sec.gov 403, www.sec.gov 403 |
| API 자원 후보 | 4개 | 2기업 × submissions/companyfacts |
| 실제 API endpoint 접근 | 0 / 후보 4 | robots 실패 후 미시도·보류 |
| 유효 API payload | 0 / 실제 endpoint 시도 0 | 접근률 undefined; 0%로 계산하지 않음 |
| 고유 공시 문서 발견·접근·다운로드 | 0 / 0 / 0 | submissions 미확보로 발견 단계 미실행 |
| 공시 본문 접근률·자동 추출률 | NA / NA | 각각 분모 0 |
| 완전 본문·원문 대조·숫자표 감사 | 0 / 0 / 0 | 검증 미실행 |
| 구조화 숫자 관찰·실제 주장·사업 관계 | 0 / 0 / 0 | 자료 부재가 아니라 접근 시험 미완료 |
| 독립 발표 family | 0 | 식별 가능한 실제 발표 미확보 |
| 언론사 기사 URL·고유 기사·기사–사건 링크 | 0 / 0 / 0 | 언론사 후보 선정 미실행 |
| 독립 표현·비교 가능한 매체 간 기사 쌍 | 0 / 0 | 문체 분석 미실행 |
| 다운로드 중복률 | NA | 전체 다운로드 0 |

정책 페이지의 web 열람은 조건 조사이며 공시 본문 접근 성공으로 집계하지 않았다. [network_probe_trials.csv](network_probe_trials.csv)와 [활성 run summary](pilot_20261005_002/summary.json)로 집계를 재계산할 수 있다. `pilot_20261005_001`은 권리 gate 개선 전의 실패 보존 기록으로 유지하며, 같은 API 후보를 run 간 합쳐 고유 후보 8건으로 세지 않는다. 기존 한국 공식 뉴스룸 4건/186블록은 이 표에 포함하지 않는다.

## 수행한 검증과 남은 감사

새 원문·private·blocks 경로의 Git 제외를 추가했다. 신규 수집기는 별도 출력 디렉터리, 안정 문서/수집본 ID, byte hash, JSON pointer, Unicode code-point offset, 회계기간·기간 길이·USD, 실패 원인과 노출 이력을 기록하도록 구현했다. 기존 manifest/report/raw를 덮어쓰지 않는다. 준비한 추출은 companyfacts JSON 사실 필드에 한정하며 공시 HTML/PDF 본문·문단·표/XPath 파서는 아직 구현하지 않았다. 실제 신규 자료가 없어 원문 표 의미·본문 누락/혼입·날짜 충돌·사업 scope·정정/후속·offset 검증은 **미실행**이다. 코드/빈 manifest 재현 검증은 원자료 감사와 별도로 보고한다.

## 채택과 다음 실행

SEC는 이용조건상 조사 후보를 유지하되 현재 실행환경의 자동 접근은 보류한다. 발행사 IR을 403 우회 경로로 쓰지 않는다. 정상 조건에서 별도 실행환경/승인된 기관 경로 또는 사용자가 적법하게 확보한 원본으로 재개할 수 있으나, 이번 실행에서 그 경로를 시험하거나 확보했다고 주장하지 않는다.

다음은 기업·범위 합의 → 정상 접근 소표본 → 재무표와 사업 관계 원문 감사 → 실제 P02 사례 → 인간 독립 양식 시험 순서다. 문헌·스키마 초안은 병행했으며 실제 자료·인간 검증을 대신하지 않는다.
