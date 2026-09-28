# P01 국내 뉴스 파일럿: 출처·권리 검토

- 확인일: 2026-09-21 (날짜 정밀도; 정확한 시각을 만들지 않음)
- 대상 기준 기간: 2024Q1~2026Q2. 기사 발행일·API 수집일·사건 기준분기는 별개다.
- 범위: 공개 상품설명·기술문서·이용조건 확인. 온톨로지 설계는 포함하지 않았다.
- 이 파일은 공개 문서에서 확인한 조건과 본 프로젝트에 적용 가능한 권한을 분리한 실행 기록이다.

## 실제 확인 결과와 다음 실행 가능 범위

NewsStore AI 상품은 **1차 8개 매체가 모두 판매 목록에 있음**을 확인했다. 그러나 본 프로젝트 계약서·승인서·구매기간·제공 매체 범위·실제 API 응답을 확인한 것은 아니다. 계약이 없다고 단정하지 않으며 **계약 확인 상태는 not_inspected**다. 원문 수집 및 AI 처리 권한을 자동으로 allowed로 만들지 않았다.

- 공개 문서 조사: **고유 URL 19개**, 조사 기록 **24건 = 성공 17 + 실패 6 + 부분 확인 1**. 같은 문서의 재시도/색인 확인을 별도 기록했으므로 성공 17은 고유 출처 17개라는 뜻이 아니다.
- API 실제 호출: **0건**. 기사 본문 fetch·저장·분석: **0건**. 표본 API 성공률·본문 완전성·매체별 기간 커버리지는 **미측정**이다.
- source_registry: **18행** = 공급/API/공식출처 9 + 직접 매체 8 + 제외 경로 NAVER 1.
- 제외 경로를 뺀 **17행 중 프로젝트 raw_storage와 ai_input이 모두 allowed인 행은 0행**이다. 공개 문서 접근 성공을 권한 확인 성공으로 세지 않았다.
- 직접 매체 8개는 **NewsStore 상품 목록만 확인**했다. 각 언론사 사이트의 자동수집·원문 저장·AI 조건은 이번 조사에서 별도로 검토하지 않았으므로 모두 unresolved다.
- 국내 기사·발표 family·동일 주장 비교쌍의 수는 이 권리 조사 작업에서 측정하지 않았다. 부모 파일럿 manifest의 집계와 합쳐 별도 보고해야 한다.

현재 진행 가능한 작업은 URL·검색식 후보 정리, 보유 계약 확인, 공급사 질의 검토 및 수집기 오프라인 검증이다. 권리 확인 전 국내 본문 대량저장·외부 LLM 입력은 진행하지 않는다.

## 1. NewsStore: 상품 설명과 계약을 분리

[AI 뉴스데이터 상품](https://www.newstore.or.kr/store/prodct/ainewsdata/list.do)은 JSON/API, LLM 학습·파인튜닝·RAG 상품을 안내한다. 공개 이용범위에 저장·분석·AI 학습과 분석결과 전송이 있으나 **기사 본문 대외전송은 제외**한다. RAG 구매 과정은 준비중이라고 안내하므로 실제 제공 방식·조건은 견적 단계에서 재확인해야 한다.

따라서 외부 클라우드 LLM·임베딩 API에 원문을 보내는 행위는 AI 상품명만으로 허용되지 않는다. 로컬 embedding/vector와 원문을 포함하는 파생 chunk의 저장·공유·보유기간도 명시 계약 확인 전 unresolved다. 공개 설명의 본문 전송 제한은 registry의 external_transfer/redistribution에 denied로 기록했다. 이는 별도 서면계약상 예외가 확인되면 해당 계약 범위로 다시 판정할 수 있다.

[분석용 Full Text/200자 상품](https://www.newstore.or.kr/store/prodct/newsdata/list.do)은 통계·동향 분석용이며 **AI 활용 목적이 허용되지 않는다**. 분석용 구매를 AI 입력·학습 권한으로 전환할 수 없다. 이 경로의 ai_input/ai_training은 denied, AI embedding 목적도 금지 범위에 따른 보수적 실행 판정으로 denied다.

[이용약관](https://www.newstore.or.kr/store/footer/selectTerms.do?ver=20250224)은 시행일을 2025-02-24로 표시한다. 제9~10조의 구매신청과 승인 통지, 제17조의 신청 목적·매체 제한 및 DB화 미허락 상품의 종료 후 보관 제한, 제21조의 이용제한을 확인했다. 공개 상품 소개와 실제 구매 승인·계약의 존재는 다르다. [저작권정책](https://www.newstore.or.kr/store/footer/selectCopyRight.do)도 사전허가 없는 복제·저장·배포를 허용하지 않는다.

### 매체 목록에서 확인한 범위

| source_id | 매체 | NewsStore 매체ID | AI 상품목록 | 2024Q1~2026Q2 관련 발행기사 제공 |
| --- | --- | --- | --- | --- |
| MK | 매일경제 | 02100101 | 명시됨 | 미확인 |
| HANKYUNG | 한국경제 | 02100601 | 명시됨 | 미확인 |
| ETNEWS | 전자신문 | 07100501 | 명시됨 | 미확인 |
| DT | 디지털타임스 | 07101201 | 명시됨 | 미확인 |
| EDAILY | 이데일리 | 04101008 | 명시됨 | 미확인 |
| NEWSPIM | 뉴스핌 | 04100078 | 명시됨 | 미확인 |
| EBN | EBN | 04100958 | 명시됨 | 미확인 |
| ZDNET_KR | 지디넷코리아 | 07100101 | 명시됨 | 미확인 |

AI 판매 여부는 위 AI 상품 페이지에서 직접 확인했다. ID는 [뉴스 제공 언론사 목록](https://www.newstore.or.kr/store/introduce/selectNewsMarketPartner.do)에서 확인했으며 목록의 UPDATE는 2025.01.02다. 매체 목록에는 한국경제는 AI/라이선스, 디지털타임스는 분석/AI 등 상품 차이가 표시된다. 이 목록은 개별 기간·기사·직접 웹수집의 권리 근거가 아니다.

### 검색·상세 API 기술문서

[검색 API](https://www.newstore.or.kr/store/prodct/license-news-search/license-api-list.do)와 [상세 API](https://www.newstore.or.kr/store/prodct/license-news-detail/license-api-list.do)에서 apiKey 인증과 content, news_id, title, byline, provider 및 원문링크 등 필드를 확인했다. 검색은 from/until, provider와 반환 fields를 받으며 상세는 news_id로 조회한다. 기술문서에는 검색 반환 크기/시작위치 제한이 있으나 계약별 권한·호출 속도·전체기간 제공성은 미검증이다.

published_at, enveloped_at, dateline을 같은 시각으로 합치지 않는다. 가이드는 published_at을 세계표준시간이라고 설명하지만 예시에는 +09:00도 보이므로 실제 문자열의 offset을 보존하고 공급사에 의미를 확인한다. 문서의 content 필드가 실제 완전본문을 제공했다는 증거는 아직 없다.

## 2. BIGKinds: 발견·분포 확인에 한정

[공식 FAQ](https://www.bigkinds.or.kr/news/faqList.do?page=2)는 다운로드 본문이 첫 200자이며 전체본문은 NewsStore 유료상품을 이용하도록 안내한다. 일반 범위는 1990년 이후이나 매체별 제공기간은 다르다. 뉴스 ID의 수집시각은 언론사 전송시각으로, 원 매체 게시시각과 다를 수 있다.

[회원정책](https://www.bigkinds.or.kr/v2/intro/policy.do)에서 비회원 검색은 가능하고 데이터 다운로드는 회원만 가능함을 확인했다. 이번에는 로그인·내보내기를 하지 않았다. [검색 도움말](https://www.bigkinds.or.kr/v2/news/index.do)은 공식 검색 색인에서 최대 20,000건/첫 200자를 확인했지만 직접 열기는 400 오류 페이지로 이동했다. [search.do](https://www.bigkinds.or.kr/v2/news/search.do)의 색인에는 검색어가 있으면 최대 5년, 없으면 1년이라는 검색창 제한이 있었으며 실제 표본 검색 결과는 확인하지 않았다.

[서비스 안내](https://www.bigkinds.or.kr/v2/intro/service.do)의 기사 전재·복제·배포 제한을 함께 기록했다. 무료 export를 완전본문이나 AI 입력 권한으로 해석하지 않는다. 본문이 제외된 최소 발견 메타데이터의 구체적 보유·공유 범위 역시 별도 확인 대상이다.

[수집기사 정보](https://www.bigkinds.or.kr/v2/intro/news.do)는 페이지 존재만 확인했고 매체별 기간 추출은 실패했다. 기존 전략의 OpenAPI 기관협약·최대 12개월 설명은 [기존 매뉴얼 URL](https://www.bigkinds.or.kr/manual/%EB%B9%85%EC%B9%B4%EC%9D%B8%EC%A6%88_%EC%82%AC%EC%9A%A9%EC%9E%90%EB%A7%A4%EB%89%B4%EC%96%BC.pdf) 접근 실패로 이번에 재검증하지 못했다. 현행 확정 제약으로 재인용하지 않는다.

## 3. 공식 뉴스룸도 언어·도메인별 조건을 구분

- [Samsung Global 약관](https://news.samsung.com/global/terms): 개인·정보·비상업 목적의 복사/다운로드 조건을 확인했다. 조직적 코퍼스, AI 처리, 다른 서버 미러링 및 재배포가 본 프로젝트에서 허용되는지는 미확인이다.
- [Samsung Korea 콘텐츠 안내](https://news.samsung.com/kr/%EC%82%BC%EC%84%B1%EC%A0%84%EC%9E%90-%EB%89%B4%EC%8A%A4%EB%A3%B8-%EC%BD%98%ED%85%90%EC%B8%A0-%EC%9D%B4%EC%9A%A9%EC%97%90-%EB%8C%80%ED%95%9C-%EC%95%88%EB%82%B4): 자체 제작 콘텐츠 이용을 안내하지만 별도 작성자·워터마크 이미지·영상 예외 및 변형/가공 후 배포 제한이 있다. 자동수집·AI 권한을 일괄 허용으로 처리하지 않았다.
- [SK hynix English 약관](https://news.skhynix.com/en/terms-of-use/): 수정일 2025-03-07. **로봇·스파이더 등 자동 접근을 명시적으로 금지**한다. 사전 서면동의와 개인 비상업적 사본 예외는 별도로 다룬다. 새 영문 뉴스룸 본문 자동 수집을 차단한다.
- [SK hynix Korea 운영안내](https://news.skhynix.co.kr/guideline/): 자체 제작·출처 표시의 공유/인용 조건을 안내하나 외부 작성자 예외, 상업적 사용 및 변형/가공 금지가 있다. 영문 도메인의 조건을 한국어 도메인으로 자동 전파하지 않았다. AI·chunk·자동접근은 unresolved다.

기존 공식 영문 4건·186블록의 확보/추출 결과는 보존해야 한다. 그것이 현행 이용권한이나 국내 언론사 코퍼스 검증을 뜻하지 않는다. 기존 파일의 공개·재사용 범위는 별도 권리 재검토 대상으로 남긴다.

## 기록 사용법과 미해결 항목

source_registry의 permissions는 이 프로젝트의 **기사 데이터 파이프라인**에 적용하는 allowed/denied/unresolved 값이다. 공개 웹사이트를 일반적으로 읽을 수 있는지와 같은 뜻이 아니다. 조건부 일반 허락은 rights_scope_notes에 기록하고, 개별 문서/프로젝트 적용 조건을 확인하지 못하면 unresolved를 유지했다. rights_status=verified는 해당 파이프라인에 충분한 근거를 갖춘 경우에만 사용한다.

모든 출처에서 automated_access, metadata_storage, raw_storage, internal_analysis, ai_input, ai_training, external_transfer, embedding_storage, derived_chunk_storage, sharing, redistribution을 분리했다. 인증·기간·약관확인·계약확인도 별도다. robots나 HTTP 200을 저장/AI 허락의 근거로 쓰지 않았다.

남은 실행 조건은 (1) 기존 계약·승인서가 있다면 해당 범위 확인, (2) 8개 매체의 실제 발행일 범위 및 누락/정정 제공방식, (3) 외부 LLM과 embedding/chunk·보유기간·공유 범위 서면 확인, (4) 그 뒤 허용된 표본 응답 및 원문 감사다. [공급사 문의 초안](supplier_questions.md)은 준비했으나 발송하지 않았다.

NAVER 뉴스 API는 AGENTS.md의 현행 제외 결정을 유지했다. 재조사·호출하지 않았다. 실패한 문서를 0건 또는 허용으로 숨기지 않았다.
