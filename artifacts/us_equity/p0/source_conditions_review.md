# 미국 기업 P01 출처 조건 검토

검토 기준일은 사용자 시간대의 **2026-10-05**이며, 정책 열람 기록은 2026-10-05T11:55:02Z이다. Microsoft·NVIDIA는 이번 접근성 시험의 후보이며 팀 확정 기업으로 해석하지 않는다. 이 문서는 `source_registry.csv`의 판단 근거이며 확보 문서 수·본문 추출 성공률을 보고하는 문서가 아니다.

## 이번 실행에 적용할 범위

SEC Submissions·Company Facts JSON의 로컬 소표본 시험과 deterministic 구조 추출은 **이용조건상 조건부 후보**다. 다만 이번 환경에서 `data.sec.gov/robots.txt`와 `www.sec.gov/robots.txt`의 로컬 직접 요청이 각각 403을 반환하여 두 호스트의 추가 API·filing 요청은 진행하지 않는다. 사전에 선정한 API 후보 4건은 `blocked_unattempted`로 보존하며 다운로드/추출 성공으로 집계하지 않는다. 접근 가능한 후속 실행에서는 숫자·단위·실제 시작/종료일·CIK·accession·공시 형식·fact tag만 정규화하고 원자료의 prose·description·회사 본문은 agent prompt나 외부 LLM에 넣지 않는 경로를 적용한다. AI 원문 입력/학습은 `unresolved`이며 미실행이다. 정규화된 비표현적 사실을 P02 예제로 연결하는 처리는 이 제한과 구별하며 이번 API 확보 사실로 보고하지 않는다.

Microsoft IR 웹 본문은 프로젝트 코퍼스로 저장·AI 처리하는 권리 범위가 확인되지 않아 보류한다. NVIDIA의 일반 웹사이트 약관은 자동 수집을 제한하며, IR 하위 도메인에 적용되는 footer를 이번 도구로 확인하지 못했으므로 해당 하위 도메인도 채택하지 않는다. 같은 내용이 SEC 공개 filing에 포함되었다면 원출처·획득 경로·권리 판단을 별도 기록하며 기업 웹 약관을 SEC API 조건으로 합치지 않는다.

## 근거와 판단 코드

| 코드 | 공식 근거와 위치 | 이번 판단 |
| --- | --- | --- |
| SEC_REUSE | [SEC Webmaster FAQ](https://www.sec.gov/about/webmaster-frequently-asked-questions), General Questions 첫 두 항목 | 정부 작성물과 EDGAR 공개 filing의 접근·재사용을 허용한다. stock art 등 예외가 있다. |
| SEC_DISSEMINATION | [SEC Privacy Information](https://www.sec.gov/about/privacy-information), Website Dissemination | SEC 허락 없이 복사·추가 배포가 가능하나 출처 표시를 권고하며 SEC 로고/미술품·상표 사용에 제한을 둔다. 외부 링크는 외부 사이트의 조건이다. |
| SEC_FAIR_ACCESS | [SEC Developer Resources](https://www.sec.gov/about/developer-resources), Fair Access; [SEC Webmaster FAQ](https://www.sec.gov/about/webmaster-frequently-asked-questions), Developers/programmatic downloads | 식별 가능한 User-Agent, 사용자 전체 10 req/sec 이하, 필요한 것만 다운로드하는 접근을 요구한다. |
| SEC_API | [SEC EDGAR APIs](https://www.sec.gov/search-filings/edgar-application-programming-interfaces), data.sec.gov/submissions·XBRL APIs·Programmatic API Access | API key/인증 없이 JSON을 제공한다. submissions는 최근 최소 1년 또는 1,000건과 추가 history file 목록이며 전체 기간 검증은 별도다. companyfacts는 비custom taxonomy의 entity 전체 facts다. segment/prose의 완전한 대체물이 아니다. |
| SEC_LOCAL_FACTS | SEC_REUSE·SEC_DISSEMINATION·SEC_API에 대한 프로젝트 판단 | 공개 JSON을 로컬 저장하고 사실 필드를 비AI 코드로 분석하는 소표본은 허용되는 재사용의 범위로 판단한다. 원문 AI 권리를 확정한 판정은 아니다. |
| SEC_AI_UNRESOLVED | 위 정책과 API 가이드 검토 | 외부 LLM 원문 입력과 모델 학습의 개별 조건을 명시적으로 확인하지 못했다. 원문 prose/description AI 처리는 보류한다. |
| MSFT_DOCUMENTS | [Microsoft Terms of Use](https://www.microsoft.com/en-us/legal/terms-of-use), Documents·Personal and Non-Commercial Use Limitation·Content | 문서 예외는 고지 유지·정보용 비상업/개인 목적·수정 금지·network 복제/게시 제한을 포함한다. 일반 프로젝트 코퍼스에 포괄 허락을 주지 않는다. |
| NVDA_AUTOMATION | [NVIDIA Terms of Service](https://www.nvidia.com/en-us/about-nvidia/terms-of-service/), §3.1·§3.2(f)·§4 | 개인 비상업 내부용 단일 copy의 좁은 허락과 자동 scraper/crawler/data mining/extraction 제한이 있다. 자동 수집 채택을 보류한다. |

SEC FAQ의 짧은 원문 근거: “All Government-created content on sec.gov and EDGAR public filing content are free to access and reuse.”

이 문구는 **SEC가 작성한 정보만** 허용한다는 문구가 아니다. 정부 생성물과 제출자가 작성한 공개 filing의 출처를 구별하되, 공개 filing 자체에 SEC가 안내하는 재사용 범위를 기록한다. 이를 모든 filer 저작권의 소멸·public domain 판정으로 바꾸지 않는다. 로고, licensed illustration, 개별 첨부의 별도 고지, 외부 링크 자료는 제외하거나 개별 검토한다. companyfacts의 tag label/description과 filing prose를 숫자 fact와 섞지 않는다.

## 자동 접근과 실패 처리

SEC 공식 FAQ의 User-Agent 예시는 회사 식별과 담당자 이메일을 포함한다. 별도로 정확히 그 형식만 허용하거나 이메일 없는 repository URL을 승인한다는 문구는 확인하지 못했다. 이번 application name와 실제 repository URL 선언은 진실한 식별을 위한 소표본 운영 판단이며 **SEC의 이메일 대체 승인**으로 보고하지 않는다. 수집 실행 기록에는 사용 UA 유형을 남기되 개인 이메일을 만들거나 인증정보를 노출하지 않는다.

정책의 상한과 실제 운영 간격을 구별한다. 이번 소표본은 사용자 전체 합산으로 1 req/sec 이하, 동시 요청 1개를 적용하고 403이면 해당 시도를 중단한다. 429 및 Retry-After를 준수하며 차단 우회·UA 위장·IP 변경을 하지 않는다. 이 값은 프로젝트의 보수적 설정이며 SEC 공식 상한이 바뀌었다는 뜻이 아니다.

| URL | 실제 확인 | 결과와 처리 |
| --- | --- | --- |
| [www.sec.gov/robots.txt](https://www.sec.gov/robots.txt) | web tool, 2026-10-05 정책 조사 | `/Archives/edgar/data` allow와 특정 파일/경로 disallow를 확인했다. 정책 열람 성공이며 로컬 HTTP 접근 성공이 아니다. |
| `https://www.sec.gov/robots.txt` | root의 선언된 application+repo UA urllib 직접 1회, 확인일 2026-10-05; 정확 관측시각 미확인(`observation_precision=run_trace_only`) | HTTP 403. 재시도/우회 없음. 이 호스트의 로컬 자동 접근 중단. web tool 정책 열람과 실행환경의 직접 접근은 다른 기록이다. |
| `https://data.sec.gov/robots.txt` | web tool 접근 불가; application+repo UA로 직접 1회, 2026-10-05T11:56:03.748412Z | HTTP 403. 재시도/우회 없음. robots 상태 `unresolved_access_denied`; 공식 API 제공 안내와 실제 환경의 접근 실패를 구별한다. |

403 robots 실패는 API 권리가 없다는 증거도, robots를 허용했다는 증거도 아니다. 공식 API 문서가 안내하는 제출 이력·XBRL 소표본 경로는 이용조건상 후보로 남기고 이번 두 호스트의 접속은 중단한다. 로컬 robots 네트워크 시도 **2건/성공 0건/실패 2건**, submissions·companyfacts API endpoint **실제 시도 0건/선정 후보 4건**, filing body **실제 접근 0건**, 실제 원자료 확보 **0건**이다. 공식 정책 web 열람을 corpus 확보 분자에 넣지 않는다. API 후보의 미시도를 본문 확보 실패율 또는 기업 자료 부재로 바꾸지 않는다. 실제 사건/수치의 원문 검증은 미완료 상태로 P02에 인계한다. 본문·프록시·bulk mirror로 바꿔 성공 처리하지 않는다. 공식 API 가이드에 제시된 `www.sec.gov` bulk ZIP은 문서상 대체 제공 방식이며 이번 소표본에서는 다운로드하지 않았다.

## 기업 IR의 적용성 확인

- Microsoft [IR 시작 페이지](https://www.microsoft.com/en-us/investor/default)의 footer Terms of use 링크는 `https://go.microsoft.com/fwlink/?LinkID=206977`에서 위 TOU로 이동함을 확인했다. 열람 페이지의 표시된 TOU 갱신일은 2022-02-07이며 확인일과 다르다. TOU의 AI Services 제한을 일반 IR 문서에 기계적으로 적용하지 않는다. 일반 IR 문서의 AI 활용 허락은 별도로 미확인이다.
- NVIDIA [IR 시작 페이지](https://investor.nvidia.com/home/default.aspx)의 web 추출에는 약관 footer가 나타나지 않았다. 일반 NVIDIA 약관의 적용 범위는 그 약관이 연결된 NVIDIA 운영 사이트를 포함하므로 IR 적용 연결은 `unresolved`다. 불명확한 적용성을 자동 접근 허용으로 바꾸지 않는다. newsroom 및 `q4cdn.com` 첨부의 최종 도메인/별도 고지는 미확인이고 수집하지 않았다.

## registry 해석과 남은 항목

각 권리 열은 `allowed / prohibited / conditional / unresolved` 중 하나이며 세부 조건 열은 위 근거 코드와 해당 범위를 적는다. SEC의 일반 복사·배포 허용을 별도 AI 학습 허락으로 재명명하지 않는다. ordinary external transfer와 외부 LLM 입력은 다른 열이다. SEC JSON 원본을 공유 저장소에 그대로 공개하는 일은 이번 실행 범위에 포함하지 않는다.

아직 확인하지 않은 항목은 원문 LLM 입력/학습의 이용 범위, NVIDIA IR의 약관 연결, IR 첨부 최종 host 조건, 각 endpoint의 실행환경 접속 가능성, 실제 역사 기간 coverage이다. 정책 열람 5개 출처 행은 문서 확보 5건을 뜻하지 않는다. 새 미국 corpus 검증을 한국 공식 뉴스룸 4건/186블록의 기존 회귀 결과로 대체하지 않는다.
