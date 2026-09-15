# 레퍼런스 등록부

기준일: 2026-09-15. 이 설계서에서 인용한 프로젝트 자료·기업 자료·논문·표준·구현 가이드를 모두 모았습니다. 관련 분야의 모든 문헌을 정독했다는 뜻은 아닙니다. **확인 수준과 미확인 사항을 별도 표시**하며, 논문 정독·추가 검색은 P02의 실행 작업입니다. 보관 중인 이전 상세기획서는 현재 단계 번호의 근거로 사용하지 않습니다.

## 자료별 용도와 확인 수준

| ID | 자료 | 적용 단계 | 읽을 내용과 사용 방법 | 확인 수준·주의점 |
| --- | --- | --- | --- | --- |
| N01 | [최신 Notion 프로젝트](https://app.notion.com/p/3d00589711408057948dc5666ae044e3) | 전체 | 개요 및 설명의 RQ1~5, 모듈7.1~7.11, Phase0~8, 기업 선정 | 2026-09-15 본문 확인; 보관 초안보다 우선 |
| N02 | [회의1 실행 계획](https://app.notion.com/p/3d505897114080558acfdcf184982330) | P0~P3 | 기업·기간·A/B/C 역할·초기 표본·후속 적용 순서 | 2026-09-15 작성·확인 |
| D01 | [OpenDART 공시정보 개발가이드](https://opendart.fss.or.kr/guide/main.do?apiGrpCd=DS001) | P0/P6 | 공시검색·기업개황·원본파일·고유번호 가이드에서 실제 필드와 오류 조건 확인 | 목록 확인; API 키 발급·수집 성공은 별도 작업 |
| D02 | [KIND](https://kind.krx.co.kr/) | P0/P6 | 정기·수시 공시 원문, IR 자료 탐색 | 출처 확인; 자동 수집 허용·접근 조건은 P0에서 확인 |
| D03 | [KRX 정보데이터시스템](https://data.krx.co.kr/) | P0/P5/P8 | 거래일·가격·거래량·수정주가 기준과 이용조건 확인 | 접속 확인, 동적 본문·실제 다운로드 미검증 |
| D04 | [한국은행 ECOS](https://ecos.bok.or.kr/) | P5/P6 | 환율·금리 시계열과 발표시점 확인 | 접속 확인, 통계별 시리즈·개정 이력은 미검증 |
| D05 | [GDELT](https://www.gdeltproject.org/) | P0/확장 | 글로벌 기사 후보·메타데이터 수집 가능성 검토 | 공식 소개 확인; 대상 기간 API 조회·기사 사용권은 미검증 |
| D06 | [SEC EDGAR API](https://www.sec.gov/search-filings/edgar-application-programming-interfaces) | 확장 | 해외 기업 submissions/XBRL, 기간·사업 범위 차이 검토 | 공식 가이드 확인; 현재 국내 표본의 필수 수집원 아님 |
| C01 | [삼성 2025Q4 IR](https://images.samsung.com/kdp/ir/events/2025/2025_4Q_conference_kor.pdf) | P0~P3/P6 | 메모리 전망·HBM4 양산 출하 계획, 메모리 매출/DS 이익 범위 구분 | PDF 본문 확인 |
| C02 | [삼성 2026Q1 IR](https://images.samsung.com/kdp/ir/events/2026/2026_1Q_conference_kor.pdf) | P0~P3/P6 | HBM4 양산 판매 개시, 이전 계획과 후속 실행 연결 | PDF 본문 확인 |
| C03 | [SK하이닉스 2026Q1 공식 실적 발표](https://news.skhynix.com/en/q1-2026-business-results/) | P0~P3 | 제품 공급·양산·투자·재무 항목 추출; 한국어 원문과 중복 구분 | 영문 본문 확인; 표기 날짜와 본문 발표일을 별도로 기록 |
| C04 | [ISC 공식 IR](https://isc21.irpage.co.kr/) | P2 전이/P3 | 실적자료·스크립트·공개 Q&A, FT/SLT·매출액 CAPA 정의 | 포털 공개본문 확인; 개별 자료 전체 확보 여부는 따로 기록 |
| C05 | [리노공업 2026Q1 분기보고서](https://kind.krx.co.kr/external/2026/05/14/000390/20260514000861/11013.htm) | P2 전이/P3 | 주요제품 가격, 생산능력, 제품별 매출, 신설 투자; 분기와 연간 열 구별 | 본문 확인; 제품별 가격·생산능력 산출 어려움 명시 |
| C06 | [주성 2026Q2 Fact Sheet](https://www.jusung.com/uploads/post/2026/08/c7aa1f2865acd32715035278b3268683.pdf) | 보류 후보 | 반도체/디스플레이/태양광 사업 구분 | PDF 본문 확인; 현재 학습 대상 아님 |
| C07 | [테스 2026Q1 IR 게시물](https://www.hites.co.kr/bbs/board.php?bo_table=d3&sca=IR%EC%9E%90%EB%A3%8C&wr_id=47) | 보류 후보 | 연속 분기 IR 게시·첨부 접근 재시험 | 게시물 확인; 첨부 본문 도구 접근 실패, 자료 부재 아님 |
| R01 | [IFRS Practice Statement 2: Making Materiality Judgements](https://www.ifrs.org/issued-standards/list-of-standards/materiality-practice-statement/) | P1/P5 | 회계 보고 맥락의 materiality와 리서치 검토 필요성의 차이 비교 | 공식 개요 확인; 문단별 해석은 P1 원문 정독 작업 |
| R02 | [Zheng et al. (2019), Doc2EDAG](https://aclanthology.org/D19-1032/) | P1/P3/P4 | 문서 단위 사건·분산된 인자·여러 사건의 표현 설계 | 서지·초록 확인; 중국어 자료 성능을 한국어 예상 성능으로 사용 금지 |
| R03 | [Artstein & Poesio (2008), Inter-Coder Agreement](https://aclanthology.org/J08-4004/) | P1/P3/P5 | 라벨 유형별 일치도·우연 일치·단위 분리 문제 검토 | 서지·초록 확인; 분석식 선택 전 본문 읽기 |
| R04 | [Park et al. (2021), KLUE](https://arxiv.org/abs/2105.09680) | P1/P4 | 한국어 NER·RE 평가 방식·모델 후보 조사 | 서지·초록 확인; 금융 사건 전용 gold와 별도 |
| R05 | [Yang et al. (2020), FinBERT](https://arxiv.org/abs/2006.08097) | P1/P4 | 금융 도메인 적응의 비교 후보와 한계 | 서지·초록 확인; 영어 금융 모델을 한국어 정답기로 쓰지 않음 |
| R06 | [Reimers & Gurevych (2019), Sentence-BERT](https://aclanthology.org/D19-1410/) | P4/P6 | 문장 임베딩 후보·유사도 검색의 역할 | 서지·초록 확인; 유사도는 같은 사건의 증거가 아님 |
| R07 | [Thakur et al. (2021), BEIR](https://arxiv.org/abs/2104.08663) | P6/P8 | 희소/밀집 검색 비교와 다른 도메인 평가 설계 | 서지·초록 확인; 우리 금융 prior-state 검색을 따로 평가 |
| R08 | [Chen et al. (2021), FinQA](https://aclanthology.org/2021.emnlp-main.300/) | P1/P6 | 표·문장 근거와 계산 프로그램 연결 방식 | 서지·초록 확인; 데이터셋 전체 재배포 권한은 별도 확인 |
| R09 | [MacKinlay (1997), Event Studies in Economics and Finance](https://www.jstor.org/stable/2729691) | P1/P5/P8 | 추정창·사건창·정상수익률·교란 사건을 읽고 연구 메모 작성 | 서지 확인; 이 조사에서 원문 본문 접근 미확인. 실험 전 원문 확보 필요 |
| O01 | [W3C SKOS Reference](https://www.w3.org/TR/skos-reference/) | P1/P2 | 대표명·별칭·상하위·정의·매핑 관계를 설계할 때 참고 | 공식 표준 개요 확인; RDF 도입 자체는 필수 아님 |
| O02 | [EDM Council FIBO](https://spec.edmcouncil.org/fibo/) | P1/P2 | 금융 개념의 재사용 가능한 정의·관계 조사 | 공식 소개 확인; 반도체 KPI가 모두 정의돼 있다고 가정 금지 |
| O03 | [W3C PROV-O](https://www.w3.org/TR/prov-o/) | 전체 | 원문→추출→수정→계산의 출처·행위·작성 주체 연결 | 공식 표준 확인; v1은 관계형 기록으로 구현 가능 |
| T01 | [scikit-learn model evaluation](https://scikit-learn.org/stable/modules/model_evaluation.html) | P3~P8 | 각 metric의 분모·평균 방식·undefined 조건 확인 | 공식 문서 확인; 설치 버전과 문서 버전 맞추기 |
| T02 | [scikit-learn cross validation](https://scikit-learn.org/stable/modules/cross_validation.html) | P3~P8 | 시간 분리·그룹 분리·누수 방지 평가 설계 | 공식 문서 확인; 일반 TimeSeriesSplit만으로 사건 묶음 분리가 보장되지 않음 |
| T03 | [scikit-learn calibration](https://scikit-learn.org/stable/modules/calibration.html) | P4/P5/P8 | 보정 곡선·확률 평가·별도 보정 데이터 운영 | 공식 문서 확인; 낮은 Brier만으로 보정 품질 단정 금지 |
| T04 | [Sentence Transformers STS](https://www.sbert.net/docs/sentence_transformer/usage/semantic_textual_similarity.html) | P4/P6 | 임베딩·유사도 구현 후보 | 공식 문서 확인; 한국어·금융 적합성은 자체 평가 |
| T05 | [SQLite FTS5](https://www.sqlite.org/fts5.html) | P6/P7 | 희소 검색·BM25·인덱스·토큰화 설계 | 공식 문서 확인; 한국어 토큰화 별도 검증 |
| T06 | [Python decimal](https://docs.python.org/3/library/decimal.html) | P2/P6 | 금액·비율 계산의 정밀도와 반올림 규칙 | 공식 문서 확인; 입력 문자열·정밀도·반올림 설정 보존 |
| T07 | [Pydantic Models](https://pydantic.dev/docs/validation/latest/concepts/models/) | P4/P6/P7 | 입출력 스키마·누락·타입 오류 검증 후보 | 공식 문서 확인; 강제 형변환과 엄격 검증을 구별 |
| T08 | [Streamlit caching and state](https://docs.streamlit.io/develop/api-reference/caching-and-state) | P7 | 세션 상태·캐시와 영속 피드백 저장 구별 | 공식 문서 확인; 화면 상태를 감사 로그로 대체하지 않음 |

## Notion 실행 작업 원본

문서 파일의 P01~P09는 설계서 번호이고, 아래 01~12는 회의1의 작업 번호입니다. Jira 이슈 생성·상태 변경은 이번 문서 작성에 포함하지 않았습니다.

- [회의1 작업 01](https://app.notion.com/p/3dc05897114081b5b964c4b5c727ac51)
- [회의1 작업 02](https://app.notion.com/p/3dc0589711408109ab01e55ae19a991c)
- [회의1 작업 03](https://app.notion.com/p/3dc05897114081c9893ecaf8383f6ef3)
- [회의1 작업 04](https://app.notion.com/p/3dc05897114081569374d1a3ac6e8bf8)
- [회의1 작업 05](https://app.notion.com/p/3dc05897114081eaa72bc9c5cfd72fc6)
- [회의1 작업 06](https://app.notion.com/p/3dc058971140814987ebd18a3248c7ef)
- [회의1 작업 07](https://app.notion.com/p/3dc0589711408168a30cd9ae549b651d)
- [회의1 작업 08](https://app.notion.com/p/3dc05897114081ccb494d65b58bbef1d)
- [회의1 작업 09](https://app.notion.com/p/3dc05897114081669eb5d46cb361ca62)
- [회의1 작업 10](https://app.notion.com/p/3dc058971140815c8281c389c53d9f57)
- [회의1 작업 11](https://app.notion.com/p/3dc05897114081d6bfcecbe44e9ce0cd)
- [회의1 작업 12](https://app.notion.com/p/3dc05897114081d29809c8c28638f88a)

## Jira 에픽 대응

- Phase 0: [KAN-4](https://qyurimoon.atlassian.net/browse/KAN-4)
- Phase 1: [KAN-5](https://qyurimoon.atlassian.net/browse/KAN-5)
- Phase 2: [KAN-6](https://qyurimoon.atlassian.net/browse/KAN-6)
- Phase 3: [KAN-7](https://qyurimoon.atlassian.net/browse/KAN-7)
- Phase 4: [KAN-8](https://qyurimoon.atlassian.net/browse/KAN-8)
- Phase 5: [KAN-9](https://qyurimoon.atlassian.net/browse/KAN-9)
- Phase 6: [KAN-10](https://qyurimoon.atlassian.net/browse/KAN-10)
- Phase 7: [KAN-11](https://qyurimoon.atlassian.net/browse/KAN-11)
- Phase 8: [KAN-12](https://qyurimoon.atlassian.net/browse/KAN-12)

## 문헌 조사 기록 양식

`ref_id / 정확한 제목 / 저자·기관 / 연도·버전 / DOI·URL / 확인일 / 읽은 절·페이지 / 연구 질문 / 데이터·언어 / 방법 / 평가·분할 / 주장 / 근거 / 우리 설계 적용 / 적용 한계 / 라이선스 / 읽기 상태`

원문을 읽지 않은 자료는 ‘초록 확인’ 상태를 유지합니다. 숫자 성능을 인용할 때는 데이터셋·분할·metric·모델 조건을 붙입니다. 접근 실패는 문헌 존재 여부와 분리하고, 대체 링크를 사용할 때도 동일 판본인지 확인합니다. API 한도·가격·모델 버전은 실행일에 재확인하고 결과 manifest에 남깁니다.

## 프로젝트 사전학습 첨부

- **N03 · 기업 리서치 반자동화 사전지식 HTML:** [최신 프로젝트의 사전학습 영역](https://app.notion.com/p/3d00589711408057948dc5666ae044e3#3d5058971140804989cde5852f8872e0). 용어·배경 입문용. 첨부 존재와 위치는 확인했으며 이번 설계 작성에서 HTML 전체 본문을 정독한 것은 아닙니다.
- **N04 · 기업 리서치 반자동화 사전지식 PDF:** [사전학습 PDF 위치](https://app.notion.com/p/3d00589711408057948dc5666ae044e3#3d5058971140803bae42c2b5e41c1938). HTML과 중복 내용인지 확인 후 문헌표에서는 같은 자료의 형식 변형으로 연결합니다. 전체 본문은 이번 작성에서 미검증입니다.

A/B/C 모두 용어가 낯설면 사전학습을 먼저 읽고 P02 문헌 조사로 들어갑니다. 이 입문 자료의 설명과 최신 기업 선정·Phase 정의가 충돌하면 최신 본문과 결정 기록을 우선합니다. 첨부 안에 추가 논문·웹 자료가 있으면 P02-T01~T04에서 원출처를 열고 이 등록부에 추가합니다.

