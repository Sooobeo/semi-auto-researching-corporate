# 레퍼런스 등록부

기준일: 2026-10-05 / 방향성 개정 v1.2. 현행 방향성의 근거는 DIR01~DIR03입니다. 기존 논문·표준·구현 문서의 확인 수준은 이전 등록 기록을 유지합니다. v1.2 개정에서는 아래 FIN01~FIN04의 공식 공개 페이지를 2026-10-05에 열람했습니다. 기업별 미국 원자료·API는 호출하거나 수집하지 않았습니다. **과거 확인·현행 적용 후보·미확인 사항을 구분**하고 실제 사용 시 P01/P02에서 다시 확인합니다.

## 현행 방향성 근거

| ID | 자료 | 용도·확인 수준 |
| --- | --- | --- |
| DIR01 | [미국 기업 온톨로지·NLP 개인 방향성 제안](../docs/project_direction/us_equity_research_proposal.md) | 2026-10-04 문서, 2026-10-05 로컬 본문 확인. 대상·개념 확장, 변화 질문·검토 카드·배치/로컬 운영 유지. 개인 제안이며 팀 합의가 아님 |
| DIR02 | 사용자 2026-10-05 대화 지시 | `docs`를 근거로 `structure` 업데이트, 기존 한국기업 자료·결과 폐기. 새 미국 입력·gold·평가로 다시 시작하는 기준; 데이터 파일 삭제 완료를 의미하지 않음 |
| DIR03 | 사용자 2026-10-05 추가 대화 지시 | 재무회계 개념 이해와 투자 리서치·기업 분석 프로세스 수행 경험을 목표로 추가. 팀원의 온톨로지/NLP/사업 분석 목표도 함께 유지하도록 structure 개정 요청 |

미국 기업의 개별 공시·IR·공식 발표는 기업 선정 후 새 출처·문서 등록부에 추가합니다. 이전 한국기업 원문 C01~C07 및 국내 공시/가격 출처 D01~D04는 현행 자료 선정에서 제외했습니다. 기존 성과를 미국 표본의 접근성·정확도 근거로 사용하지 않습니다.

## 재무회계·투자 리서치 적용 근거

| ID | 원출처 | 설계에서의 용도 | 확인 범위·한계 |
| --- | --- | --- | --- |
| FIN01 | [CFA Institute · Integration of Financial Statement Analysis Techniques](https://www.cfainstitute.org/insights/professional-learning/refresher-readings/2026/integration-financial-statement-analysis-techniques) | 목적·자료·처리·해석·보고·후속 갱신의 분석 흐름 | 2026-10-05 공개 개요·프레임워크·학습 목표 확인. 유료 전체 reading/사례를 읽었다는 기록 아님; 프로젝트 수행 범위로 적용 |
| FIN02 | [CFA Institute · Evaluating Quality of Financial Reports](https://www.cfainstitute.org/insights/professional-learning/refresher-readings/2026/evaluating-quality-financial-reports) | 사업·회계정책·기간 비교·이익/현금흐름·위험의 연결과 분석 품질 검토 | 2026-10-05 공개 요약·학습 목표 확인. 특정 회사의 보고 품질·부정 여부 판정 근거가 아니며 회사별 원문 검토 필요 |
| FIN03 | [SEC · Beginners’ Guide to Financial Statement](https://www.sec.gov/investor/pubs/begfinstmtguide.htm) | 재무상태·손익·현금흐름·자본 변동, 주석·경영진 설명의 입문 개념 | 2026-10-05 공개 가이드 본문 확인. 개별 회계처리·기업별 정의는 실제 공시·정책·적용 기준 추가 확인 |
| FIN04 | [SEC · Non-GAAP Financial Measures](https://www.sec.gov/rules-regulations/staff-guidance/corporation-finance-interpretations/non-gaap-financial-measures) | GAAP/non-GAAP 조정과 FCF 회사 정의·프로젝트 수식 분리 | 2026-10-05 공개 문답, 특히 102.07의 FCF 정의·대사·해석 제한 확인. 기업별 이용권이나 실제 조정표 확보를 확인한 것은 아님 |

## 자료별 용도와 확인 수준

| ID | 자료 | 적용 단계 | 읽을 내용과 사용 방법 | 확인 수준·주의점 |
| --- | --- | --- | --- | --- |
| N01 | [이전 Notion 프로젝트](https://app.notion.com/p/3d00589711408057948dc5666ae044e3) | 단계 흐름 참고 | 변화 질문·Phase0~8의 이전 기획 출처 | 이전 2026-09-15 확인 기록; 기업·기간·현재 방향은 DIR01/DIR02로 대체 |
| N02 | [이전 회의1 실행 계획](https://app.notion.com/p/3d505897114080558acfdcf184982330) | 과거 계획 출처 | 이전 작업 번호·분담 방식 참고 | 기업·기간·표본·역할 배정은 현행 기준 아님 |
| D05 | [GDELT](https://www.gdeltproject.org/) | P0/확장 | 글로벌 기사 후보·메타데이터 수집 가능성 검토 | 공식 소개 확인; 대상 기간 API 조회·기사 사용권은 미검증 |
| D06 | [SEC EDGAR API](https://www.sec.gov/search-filings/edgar-application-programming-interfaces) | P01/P07 조사 후보 | 미국 기업 식별·공시·기간·사업 범위·API/추출 조건 검토 | 이전 공식 가이드 확인 기록; 새 대상·기간의 호출·권리·자동 접근/저장·AI/전송 조건은 미검증 |
| R01 | [IFRS Practice Statement 2: Making Materiality Judgements](https://www.ifrs.org/issued-standards/list-of-standards/materiality-practice-statement/) | P1/P5 | 회계 보고 맥락의 materiality와 리서치 검토 필요성의 차이 비교 | 공식 개요 확인; 문단별 해석은 P1 원문 정독 작업 |
| R02 | [Zheng et al. (2019), Doc2EDAG](https://aclanthology.org/D19-1032/) | P1/P3/P4 | 문서 단위 사건·분산된 인자·여러 사건의 표현 설계 | 서지·초록 확인; 중국어 자료 성능을 미국 영문 과업의 예상 성능으로 사용 금지 |
| R03 | [Artstein & Poesio (2008), Inter-Coder Agreement](https://aclanthology.org/J08-4004/) | P1/P3/P5 | 라벨 유형별 일치도·우연 일치·단위 분리 문제 검토 | 서지·초록 확인; 분석식 선택 전 본문 읽기 |
| R04 | [Park et al. (2021), KLUE](https://arxiv.org/abs/2105.09680) | 방법 참고 | 한국어 NER·RE의 평가 설계 참고 | 이전 서지·초록 확인 기록; 현행 영문 baseline 선택 근거·미국 gold 아님 |
| R05 | [Yang et al. (2020), FinBERT](https://arxiv.org/abs/2006.08097) | P02/P05 후보 조사 | 영어 금융 도메인 적응의 비교 후보·과업 한계 | 이전 서지·초록 확인 기록; 사건/관계 추출 적합성·라이선스·비용·성능 새 검증 필요 |
| R06 | [Reimers & Gurevych (2019), Sentence-BERT](https://aclanthology.org/D19-1410/) | P4/P6 | 문장 임베딩 후보·유사도 검색의 역할 | 서지·초록 확인; 유사도는 같은 사건의 증거가 아님 |
| R07 | [Thakur et al. (2021), BEIR](https://arxiv.org/abs/2104.08663) | P6/P8 | 희소/밀집 검색 비교와 다른 도메인 평가 설계 | 서지·초록 확인; 우리 금융 prior-state 검색을 따로 평가 |
| R08 | [Chen et al. (2021), FinQA](https://aclanthology.org/2021.emnlp-main.300/) | P1/P6 | 표·문장 근거와 계산 프로그램 연결 방식 | 서지·초록 확인; 데이터셋 전체 재배포 권한은 별도 확인 |
| R09 | [MacKinlay (1997), Event Studies in Economics and Finance](https://www.jstor.org/stable/2729691) | P1/P5/P8 | 추정창·사건창·정상수익률·교란 사건을 읽고 연구 메모 작성 | 서지 확인; 이 조사에서 원문 본문 접근 미확인. 실험 전 원문 확보 필요 |
| O01 | [W3C SKOS Reference](https://www.w3.org/TR/skos-reference/) | P1/P2 | 대표명·별칭·상하위·정의·매핑 관계를 설계할 때 참고 | 공식 표준 개요 확인; RDF 도입 자체는 필수 아님 |
| O02 | [EDM Council FIBO](https://spec.edmcouncil.org/fibo/) | P1/P2 | 금융 개념의 재사용 가능한 정의·관계 조사 | 공식 소개 확인; 모든 산업 KPI·고객·경쟁 관계가 정의돼 있다고 가정 금지 |
| O03 | [W3C PROV-O](https://www.w3.org/TR/prov-o/) | 전체 | 원문→추출→수정→계산의 출처·행위·작성 주체 연결 | 공식 표준 확인; v1은 관계형 기록으로 구현 가능 |
| T01 | [scikit-learn model evaluation](https://scikit-learn.org/stable/modules/model_evaluation.html) | P3~P8 | 각 metric의 분모·평균 방식·undefined 조건 확인 | 공식 문서 확인; 설치 버전과 문서 버전 맞추기 |
| T02 | [scikit-learn cross validation](https://scikit-learn.org/stable/modules/cross_validation.html) | P3~P8 | 시간 분리·그룹 분리·누수 방지 평가 설계 | 공식 문서 확인; 일반 TimeSeriesSplit만으로 사건 묶음 분리가 보장되지 않음 |
| T03 | [scikit-learn calibration](https://scikit-learn.org/stable/modules/calibration.html) | P4/P5/P8 | 보정 곡선·확률 평가·별도 보정 데이터 운영 | 공식 문서 확인; 낮은 Brier만으로 보정 품질 단정 금지 |
| T04 | [Sentence Transformers STS](https://www.sbert.net/docs/sentence_transformer/usage/semantic_textual_similarity.html) | P05/P07 | 임베딩·유사도 구현 후보 | 이전 공식 문서 확인 기록; 영문 금융·관계 문맥 적합성은 새 자체 평가 |
| T05 | [SQLite FTS5](https://www.sqlite.org/fts5.html) | P07/P08 | 희소 검색·BM25·인덱스·토큰화 후보 | 이전 공식 문서 확인 기록; 실제 영문 약어·숫자·토큰화 검증 필요 |
| T06 | [Python decimal](https://docs.python.org/3/library/decimal.html) | P2/P6 | 금액·비율 계산의 정밀도와 반올림 규칙 | 공식 문서 확인; 입력 문자열·정밀도·반올림 설정 보존 |
| T07 | [Pydantic Models](https://pydantic.dev/docs/validation/latest/concepts/models/) | P4/P6/P7 | 입출력 스키마·누락·타입 오류 검증 후보 | 공식 문서 확인; 강제 형변환과 엄격 검증을 구별 |
| T08 | [Streamlit caching and state](https://docs.streamlit.io/develop/api-reference/caching-and-state) | P7 | 세션 상태·캐시와 영속 피드백 저장 구별 | 공식 문서 확인; 화면 상태를 감사 로그로 대체하지 않음 |

## 이전 Notion 실행 작업 원본

문서 P01~P09와 아래 과거 회의 작업 01~12는 다른 번호입니다. 아래 기업·기간·진행 상태를 미국 작업에 승계하지 않습니다. 외부 Notion/Jira는 이번 작업에서 변경하지 않았습니다.

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

## 이전 Jira 에픽 연결

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

## 이전 프로젝트 사전학습 첨부

- **N03 · 기업 리서치 반자동화 사전지식 HTML:** [최신 프로젝트의 사전학습 영역](https://app.notion.com/p/3d00589711408057948dc5666ae044e3#3d5058971140804989cde5852f8872e0). 용어·배경 입문용. 첨부 존재와 위치는 확인했으며 이번 설계 작성에서 HTML 전체 본문을 정독한 것은 아닙니다.
- **N04 · 기업 리서치 반자동화 사전지식 PDF:** [사전학습 PDF 위치](https://app.notion.com/p/3d00589711408057948dc5666ae044e3#3d5058971140803bae42c2b5e41c1938). HTML과 중복 내용인지 확인 후 문헌표에서는 같은 자료의 형식 변형으로 연결합니다. 전체 본문은 이번 작성에서 미검증입니다.

사전학습 첨부는 선택적 입문 자료입니다. 한국기업 예시·범위는 현행 입력이나 평가 자료로 사용하지 않습니다. 미국 방향성은 DIR01/DIR02와 [DECISIONS](DECISIONS.md)를 따릅니다. 필요한 문헌은 P02에서 원출처·읽은 구간·언어/과업·적용 한계를 새로 기록합니다.

## 폐기된 국내 뉴스 설계의 참고문헌 (2026-09-21 기록)

아래는 [폐기된 국내 기사 분류 설계](P01_news_article_classification_design.md)의 이전 문헌 기록입니다. 현행 수집·구매·문체 분석 계획이 아니며 미국 과업의 성능·표본·권리를 보장하지 않습니다. 재사용할 방법이 있으면 미국 질문·언어·자료로 별도 검증합니다.

| ID | 자료 | 설계에 사용한 내용 | 한계 |
| --- | --- | --- | --- |
| NWS01 | [Fan et al. (2019), BASIL](https://aclanthology.org/D19-1664/) | 동일 사건의 매체별 기사 묶음; 어휘 표현과 정보·인용 선택 분리 | 미국 정치뉴스의 편향 라벨과 분포를 국내 기업뉴스에 일반화하지 않음 |
| NWS02 | [Choubey et al. (2020), Discourse as a Function of Event](https://aclanthology.org/2020.acl-main.478/) | 기사 주사건에 대한 본문 문장 기능 8종과 화자 구분 | 제목 라벨이나 한국어 성능으로 직접 확대하지 않음 |
| NWS03 | [Lee et al. (2025), K-News-Stance](https://aclanthology.org/2025.emnlp-main.778/) | 한국 뉴스 장르, 제목·리드·인용·결론 구분 | 사회 이슈 자료; 입장 주석은 분석·의견 기사에 적용 |
| NWS04 | [Card et al. (2015), Media Frames Corpus](https://aclanthology.org/P15-2072/) | 프레임의 구간 주석 | 미국 정책 프레임을 반도체 기사에 그대로 적용하지 않음 |
| NWS05 | [Kim et al. (1999), Retrieving Collocations From Korean Text](https://aclanthology.org/W99-0610/) | 한국어 형태소·비인접 결합 청크 | 현재 형태소 분석기 성능 근거는 아님 |
| NWS06 | [Bugert & Gurevych (2021), Event Coreference Data](https://aclanthology.org/2021.emnlp-main.38/) | 기사 간 동일 사건 연결 후보 | 자동·약지도 링크는 수동 검증 필요 |
| NWS07 | [Song et al. (2023), 뉴스 제목의 인용 맥락 변화 연구](https://aclanthology.org/2023.findings-eacl.52/) | 제목 인용과 화자/기자 서술 구분 | 기업기사 성능 근거는 아님 |
| NWS08 | [IPTC Genre NewsCodes](https://cv.iptc.org/newscodes/genre/) | 분석·배경·인터뷰·의견·전재 등 장르 용어 | 개별 기사 API 응답값을 보증하지 않음 |
| NWS09 | [NewsStore 검색 API](https://www.newstore.or.kr/store/prodct/license-news-search/license-api-list.do), [상세 API](https://www.newstore.or.kr/store/prodct/license-news-detail/license-api-list.do) | 원시 기사 메타데이터와 본문 접근 필드 | 계약 상품별 본문·AI 이용권 및 장르 결측 확인 필요 |
| NWS10 | [BIGKinds 검색](https://www.bigkinds.or.kr/v2/news/index.do), [FAQ](https://www.bigkinds.or.kr/news/faqList.do?page=2) | 기사 발견·중복/사설 후보, 무료 본문 제한 | 검색 기능을 라이선스된 본문 확보로 간주하지 않음 |
| NWS11 | [네이버 뉴스 검색 API](https://developers.naver.com/docs/serviceapi/search/news/news.md) | 제목·링크·요약 패시지 기반 후보 발견 | 공식 응답에 본문 필드 없음 |
| NWS12 | [Wegmann & Nguyen (2021), STEL](https://aclanthology.org/2021.emnlp-main.569/) | 문체 비교에서 내용 통제의 필요성 | 영어 패러프레이즈 자료; 동일 사건 기사 비교의 직접 근거는 아님 |
