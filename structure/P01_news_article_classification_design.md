# P01 국내 기업뉴스 선정·분류·표현 비교 설계

> 상태: P01 접근성·분류 가능성 검증용 설계안 v0.1 (2026-09-21). 실제 기사 수집·라벨링·성능 검증 결과가 아니다. P02에서 사건·주장 스키마를 확정하고 P04에서 주석 지침과 gold를 검증한다.
>
> 연결: [P01](P01_phase0_data_feasibility.md) · [P02](P02_phase1_research_and_schema.md) · [P04](P04_phase3_annotation_pilot.md) · [공통 데이터 규약](DATA_CONTRACTS.md) · [기존 수집 전략](../artifacts/p0/domestic_news_style_corpus_strategy.md)

## 1. 목적과 기본 단위

목표는 **기업의 특정 변화가 보도될 때 국내 언론사가 어떤 사실·인용을 선택하고, 공통 사실을 어떤 어휘·문장 구조·확실성 표현으로 서술하는지** 배우는 것이다. 기사 수집량이나 URL 수를 최대화하지 않는다. 먼저 공시·IR·기업 공식 발표에서 기준 사건(anchor)을 만들고, 그 사건을 보도한 서로 다른 언론사의 한국어 기사 원문을 **사건 → 공통 사실/주장 → 기사 구간 → 표현 청크** 순서로 맞춘다. 같은 사건이라는 이유만으로 서로 다른 사실을 서술한 두 문장을 어휘 선택의 차이로 해석하지 않는다.

이는 동일 사건에 관한 매체별 기사를 묶고 어휘적 표현과 정보 선택을 구분한 [BASIL 연구](https://aclanthology.org/D19-1664/)에서 직접 영감을 받는다. 다만 BASIL은 미국 정치 기사 연구이므로 그 연구의 `bias` 판단이나 비율을 국내 기업뉴스에 이식하지 않는다. 여기서는 가치판단을 앞세우지 않고 `표현 차이`와 `포함 사실·인용 차이`를 기술한다. 기사 한 건에 복수 사건이 있을 수 있다는 설계는 문서 내 여러 사건 기록을 다룬 [Doc2EDAG](https://aclanthology.org/D19-1032/)와 맞는다.

분석 객체는 다음 순서로 분리한다.

1. **기준 자료/사건 family**: 같은 발표·주장을 재보도한 기사들이 공유하는 근거 블록과 기업·사업 범위·제품·행위·단계·기준 기간. 계획→실행 등 새 발표는 새 family로 만들고 `follow_up_of`로 연결한다. 공식 발표가 참조점이지 모든 보도 문장을 자동으로 참으로 만드는 장치는 아니다.
2. **기사**: 발행사·URL·바이라인·발행/출고/수집 시각·원문 버전·권리 조건을 가진 문서. 한 기사는 여러 사건 family와 연결될 수 있다.
3. **기사–사건 연결**: 기사에서 각 사건이 주제인지 배경인지, 어느 주장에 대응하는지 기록한다. 기사 주사건과 연구 대상 기업 사건은 다를 수 있다.
4. **문장/인용 구간**: 기사 안에서 사건 보도·결과·배경·평가·전망, 화자와 서술 주체를 가른다.
5. **표현 청크**: 공통 사실을 표현한 원문 어절, 형태소/POS, 숫자·단위·기간, 동사·명사 결합, 인과·추측·인용 표지를 원문 위치와 함께 남긴다.

P01의 산출물은 분류 **가능성·결측·오분류 원인** 보고다. 기사 어조에서 사건 중요도(materiality), 주가 방향, 실제 기업 행동을 추론해 확정하지 않는다.

## 2. 정확히 어떤 기사를 모을 것인가

**대상**은 2024Q1~2026Q2의 삼성전자 **메모리 사업**과 SK하이닉스에 관한 공식 기준 사건이다. 삼성 DS 전체 실적과 메모리 실적은 서로 다른 scope로 둔다. 분기 기간은 사건의 기준 기간이고, 기사의 발행일·공식 발표일·관측일과 별도로 보관한다. 분기 종료 뒤 발행된 관련 IR/기사도 기준 사건과 연결할 수 있으므로 기사 날짜만으로 기계적으로 자르지 않는다.

| 우선순위 | 기사/자료 유형 | 운영 결정 | 쓰임 |
| --- | --- | --- | --- |
| A | 공식 공시·IR·기업 뉴스룸 발표와 Q&A | 기준 사건으로 등록; `source_role=official_company` | 사실·수치·계획/실행 단계의 근거. 언론사 문체 표본에는 넣지 않음 |
| A | 국내 언론사 기자가 작성한 한국어 **스트레이트 사건 보도** | 목표 사건을 제목·리드 또는 본문 중심부에서 다루고 완전한 본문을 확보한 경우 핵심 표본 | 동일 사실의 제목/리드/본문 표현 비교 |
| B | 같은 사건에 관한 **분석·해설·배경 기사** | 스트레이트와 분리해 층화 | 원인·전망·경쟁 구도 등 해석적 표현 비교 |
| B | 원 발표 뒤 **실행·수치 변경·정정·부인 후속 기사** | 최초 기사와 분리하고 사건 family의 시계열 관계를 기록 | 계획→실행, 정정, 확실성 변화의 표현 비교 |
| C | 인터뷰·문답, 칼럼·사설, 피처 | 충분한 표본과 권리가 있을 때 별도 층으로 수집 | 인용 화자/작성자 견해와 일반 보도 문체의 차이 |
| 보조 | 통신사 원문·전재 기사, 보도자료 전재/재작성 | 출처 계보와 재배포 관계를 기록; 독립 언론사 문체 표본 수에서는 중복 계산 금지 | 유통·인용·보도자료 반영 정도 분석 |
| 대조 | 해당 기업을 언급하지만 변화가 없는 산업 일반·시장 반응 기사, 같은 시기의 무관 기사 | `context_only` 또는 `negative_control` | 잘못된 사건 매칭·문체 일반화 확인 |
| 제외 | 사진/영상만 있는 항목, 목록·시세·광고·협찬, 완전한 본문이 없거나 권리/출처 확인 불가 | 사유와 접근 실패를 남기고 본문 분석에서 제외 | 탐색 건수와 사용 가능 기사 수를 분리 |

사건 유형은 기사 장르가 아니다. P01의 **핵심 네 범주**는 `실적·전망`, `기술/제품 개발·검증`, `양산·출하·판매`, `설비/투자·계약·공급`이다. `정정·부인/리스크`는 별도 후속·예외 범주로 채집한다. **개발, 고객 검증, 양산 시작, 출하, 판매는 별개의 행위/단계**다. 한 기사에 실적과 투자 발표가 함께 있으면 사건 연결을 두 건 만든다. 해당 사건 유형이 특정 시기에 실제로 없으면 억지로 채우지 않고 coverage 결측을 기록한다.

기준 사건 발표일 전후 **7일을 초기 탐색창**, 후속·정정은 **30일을 우선 탐색창**으로 제안한다. 이 숫자는 논문이 정한 최적 창이 아닌 P01 실무 가설이다. 장기 후속이나 늦은 정정은 창 밖이라도 연결한다. `published_at`, `dateline`, `observed_at`, `reference_period`, 공식 발표 시점을 별도로 저장하고 시각이 날짜뿐이면 시각을 임의로 00:00으로 채우지 않는다.

## 3. 기사 한 건의 분류 축: 서로 섞지 않는다

아래 값은 **프로젝트에서 사람이 확인해 붙이는 운영 라벨**이다. [NewsStore 검색/상세 API](https://www.newstore.or.kr/store/prodct/license-news-search/license-api-list.do)는 ID·제목·본문·발행/출고/수집 시각·매체·기자·주제 분류 등을 제공하지만, 아래의 장르·전재·정정 관계를 일관된 필드로 제공한다고 가정하지 않는다. `category=경제>반도체`는 주제 후보이지 `straight` 장르가 아니다. 기사 본문을 볼 수 없으면 `unknown/unverified`를 허용한다. [IPTC Genre NewsCodes](https://cv.iptc.org/newscodes/genre/)의 장르 구분은 용어 참고용이지 NewsStore 필드 매핑이 아니다.

| 축/필드 | 값과 판정 규칙 |
| --- | --- |
| `eligibility` | `in_scope_main`: 대상 기업·사업 변화가 기사 중심이고 본문 사용 가능 / `in_scope_context`: 목표 사건이 배경·인용으로만 등장 / `negative_control`: 유사 키워드지만 목표 변화 없음 / `out_of_scope`: 기업·사업·기간 불일치 / `access_unusable`: 원문·권리·추출 품질 미충족. `reason_code` 필수. `out_of_scope`와 접근 실패는 구별 |
| `editorial_genre` | `straight`: 누가 언제 무엇을 발표·실행했는지가 중심이고 기자 해석은 제한적 / `analysis`: 원인·의미·비교·시나리오를 기자가 설명 / `opinion`: 칼럼·사설 등 필자의 규범적 주장 중심 / `interview`: 문답/인터뷰 자체가 기사 구성 / `feature`: 인물·현장 서사 중심 / `other`, `unknown`. 기사 전체의 지배적 기능으로 한 값; 애매하면 근거 구간과 검토 필요 표시. 한국 뉴스 연구의 straight/analysis/opinion/other 구분과 [IPTC 장르](https://cv.iptc.org/newscodes/genre/)를 국내 기업기사에 맞춰 확장한 운영안 |
| `urgency_format` | `breaking`, `regular`, `unknown`. `[속보]` 등은 후보 신호이며 최초 보도 증거가 아님. 속보도 분석/전재 여부와 독립 |
| `production_origin` | `reporter_original`, `wire_original`, `wire_reprint`, `press_release_reprint`, `press_release_rewrite`, `sponsored`, `unclear`. 매체 수와 독립적인 원문 독립성 판단; 바이라인·본문 출처 표기·문장 중복·발행사 원문 확인 필요 |
| `coverage_stage` | **기사–사건 연결별로** `anticipation`, `initial_report`, `followup`, `correction`, `denial`, `retrospective`, `unknown`. 기사 게시 순서가 아니라 해당 사건에 대한 기능. 한 기사는 사건 A의 최초 보도이면서 사건 B의 후속 보도일 수 있음 |
| `article_event_role` | 기사–사건 링크마다 `main_event`, `co_main_event`, `context`, `consequence_only`, `market_reaction`, `uncertain`. 기사의 주사건이 주가 급등이고 기업 발표는 배경이면 기업 사건은 `context`이며 주가 반응을 기업 행동으로 쓰지 않음 |
| `content_relation` | 비교 기사 사이 `exact_duplicate`, `near_duplicate_or_syndication`, `same_event_independent`, `same_event_followup`, `translation`, `correction_of`, `unrelated`, `uncertain`. 문서 중복과 동일 사건을 혼동하지 않음 |
| `claim_relation` | **기준 주장–기사 주장 쌍별로** `same_proposition`, `additional_fact`, `omitted`, `different_period_or_scope`, `different_modality`, `contradiction_candidate`, `uncertain`. 한 사건에서 여러 주장 관계가 공존한다. 어휘 스타일 비교는 원칙적으로 `same_proposition`에 한정 |

장르의 첫 후보는 섹션명, 제목 표식(`[해설]`, `[사설]`, `[인터뷰]` 등), 바이라인, Q&A 구조, 본문 내 분석·논증의 비중으로 만든다. 제목 길이나 인용문 존재만으로 장르를 확정하지 않는다. 직접 인용이 있는 스트레이트 기사는 여전히 스트레이트일 수 있다. 분석 기사에 단순 사실 전달 문장이 섞여 있어도 문장별 기능은 별도로 표시한다. [한국 뉴스 입장 분석 연구](https://aclanthology.org/2025.emnlp-main.778/)의 기사 장르 구분을 참고하되, 그 연구의 입장(stance) 주석은 **분석·의견 기사에만** 적용됐으므로 이 설계에서도 스트레이트 기사 전체에 찬성/반대 라벨을 강제하지 않는다.

## 4. 사건 매칭과 사실 정렬 판정

1. 공식 자료에서 `company_id + scope_id + product + action + stage + reference/effective time + 핵심 수치·단위`를 가진 기준 사건 카드를 만든다. 부족한 필드는 `unknown`으로 남긴다.
2. 기사 후보를 제목/본문 키워드·기업·기간으로 검색한다. API 후보는 인용·권리·출처가 확인된 본문으로 재확인한다. [네이버 뉴스 검색 API](https://developers.naver.com/docs/serviceapi/search/news/news.md)의 응답은 제목·링크·설명 패시지·날짜 중심이며 본문 필드가 없다. **이 프로젝트의 뉴스 문체 코퍼스 수집 경로에서는 네이버 API를 제외한다**([기존 수집 전략](../artifacts/p0/domestic_news_style_corpus_strategy.md)); 여기서의 언급은 본문 API로 오인하지 않기 위한 구분이다.
3. 문장 단위로 기업·사업 범위·제품·행위·단계·수치·기간·부정·확실성·화자를 읽고 각 `article_event_role`을 판정한다. 동일 기사에 둘 이상의 변화가 있으면 링크를 추가한다.
4. **같은 `event_family_id`**는 같은 발표·주장의 재보도 묶음이다. 키워드·날짜만으로 합치지 않는다. 계획→양산, 양산→출하, 숫자·적용 시점의 새 발표, 공식 정정 등은 별도 event mention/발표 family로 만들고 `follow_up_of`, `correction_of`, `contradicts` 등의 **family 간 관계**를 붙인다. 연구상 하나의 제품 이력을 넓게 묶어야 하면 별도 `case_id`(P02 확정 전 후보)를 사용한다. 기사 간 사건 동일성은 교차 문서 사건 공지시(coreference) 연구를 참고하되 자동 링크는 검토용 후보로 사용한다([Bugert & Gurevych 2021](https://aclanthology.org/2021.emnlp-main.38/)).
5. 기사 간 비교에서는 사건 family가 같아도 **주장/사실 카드**를 먼저 정렬한다. 공통 사실에 대응하는 문장만 `same_proposition`으로 연결해 어휘·청크를 비교한다. 추가 사실, 생략, 선택한 인용, 배경 배치 자체는 별도 `information_selection` 결과로 보존한다. 이는 [BASIL](https://aclanthology.org/D19-1664/)의 어휘적/정보적 차이 구분을 기업뉴스용 중립 라벨로 옮긴 것이다.
6. 전재·번역·기업 보도자료 문구 재사용은 문서/표현 독립성을 따로 판단한다. 같은 문장이 여러 매체에 실려도 매체별 독립 표현 3건으로 집계하지 않는다. **동일 기사의 수집·수정본**은 같은 `doc_id`의 다른 `revision_id`로, **새로 발행된 정정 기사**는 새 `doc_id`와 `correction_of` 문서 관계로 연결한다. 어느 쪽이든 이전 내용을 삭제하지 않는다.

**경계 예시(가상 사례, 실제 기사 판정 아님)**

| 표현 상황 | 라벨 결정 |
| --- | --- |
| 공식 자료는 “HBM4 양산 계획”, 기사는 “양산 돌입” | `plan`과 `actual_reported`를 분리하고 `different_modality` 또는 `contradiction_candidate` 검토; 같은 확정 사실 표현으로 정렬하지 않음 |
| 기사가 “삼성 DS 영업이익 증가”를 다룸 | `scope_id=DS`; 별도 근거가 없으면 메모리 영업이익 증가로 전환하지 않음 |
| “실적 발표에 주가 급등” 기사의 중심이 주가 | 기사 주사건은 시장 반응, 실적은 `context` 또는 `consequence_only`; 시장 반응을 기업 행위로 기록하지 않음 |
| A사 원문을 B·C사가 거의 그대로 전재 | 문서 ID는 각자 유지, `production_origin=wire_reprint`와 중복 링크; 독립 언론사 문체 표본 1건 취급 |
| 기사 한 건에서 신규 제품 발표와 설비투자 발표 | 기사 1건에 사건 링크 2건; 문장·주장마다 어느 사건에 관한 것인지 연결 |

## 5. 본문에서 무엇을 라벨링할 것인가

**위치와 기능을 분리한다.** `segment_position`은 `headline`, `subheadline`, `lead`, `body`, `conclusion`, `caption`이다. 제목/리드/인용/결론의 분리 필요성은 [한국 뉴스 연구](https://aclanthology.org/2025.emnlp-main.778/)를 참고한다. 본문 문장의 `discourse_role`은 [Choubey et al. (2020)](https://aclanthology.org/2020.acl-main.478/)의 주사건 상대 역할을 채택한다. 논문의 문장 라벨을 기사 제목에 그대로 확대하지 않고 제목은 위치·별도 기능으로 다룬다.

| 본문 문장 역할 | 프로젝트 판정 |
| --- | --- |
| `M1 main_event` | 기사 **자체의** 주사건을 직접 서술 |
| `M2 consequence` | 그 사건으로 나타난 결과·반응 |
| `C1 previous_event` | 주사건과 관련된 비교적 최근 선행 사건 |
| `C2 current_context` | 현재 상태·배경·당사자 정보 |
| `D1 historical_event` | 더 오래된 역사적 비교 사건 |
| `D2 anecdotal_event` | 예시·일화로 든 사건 |
| `D3 evaluation` | 사건의 의미·평가·판단 |
| `D4 expectation` | 향후 계획·예상·전망 |
| `NA` | 캡션/광고/메타 또는 판정 불가 텍스트 |

`speech_flag`와 `speaker_type`(`reporter`, `company`, `analyst`, `government`, `customer`, `other`, `unknown`)은 기능 라벨과 **독립**이다. 직접 인용과 간접 전언을 구분하고, 기자의 문장·기업 발표의 재서술·외부 전문가의 말이 누구에게 귀속되는지 표시한다. 인용 화자의 긍정·부정은 언론사 견해로 자동 귀속하지 않는다. 제목이 인용을 따왔을 때도 제목 선택과 화자의 발언을 나누어 기록한다([뉴스 제목 인용의 맥락 변화 연구](https://aclanthology.org/2023.findings-eacl.52/)).

표현 분석의 필드는 다음처럼 구분한다.

- `style_form`: 사실이 같을 때의 어휘·문장 구조·능동/피동·명사화·축약·강조·완곡/확실성 표지. 원문 구간과 매칭 주장 ID 필수.
- `information_selection`: 기준 사건 대비 포함/생략한 사실·숫자·배경·인용, 제목/리드 배치. 생략을 곧 의도적 편향으로 해석하지 않음.
- `source_echo`: 보도자료·IR 문장을 그대로 인용/의역/독립 취재로 확장했는지. 기자의 서술과 기업이 제공한 문구를 구분하고, 본문 접근·원 발표 대조가 불가능하면 `unknown`.
- `frame`: 무엇을 전면에 놓는가. P01 임시 후보는 `실적/성장`, `기술/실행`, `경쟁/시장`, `공급망/고객`, `위험/불확실성`, `책임/규제`. 문장/기사 수준 다중 라벨과 근거 span을 허용하며, 실제 분포를 본 뒤 P02/P04에서 통폐합. 프레임을 구간별로 표시한 [Media Frames Corpus](https://aclanthology.org/P15-2072/)는 방법 참고이고 미국 정책 프레임 목록을 그대로 복사하지 않음.
- `stance_to_target`: 명시적 대상(사건/주장)에 대한 입장; 주로 분석·의견 기사에서 근거가 있는 구간에만. `sentiment_or_tone`(평가적 극성) 및 `materiality`와 별개. 중립/불명/적용 불가를 구분.
- `claim_modality`: 계약의 `actual_reported`, `plan`, `forecast`, `possibility`, `denial`, `unknown`; 기자가 단정/귀속/추정한 방식(`author_certainty`)은 추가 축. `plan`을 완료 사실로 바꾸지 않음.
- `chunk`: 원문 어절 표면형, 형태소·품사 분석, 연속/비연속 결합, `event_trigger`, `company/product`, `number+unit+period`, `attribution`, `hedge`, `causal_link` 범위와 Unicode code-point offset. 한국어의 교착성과 자유로운 어순·떨어진 연어 때문에 공백 n-gram만으로 청크를 정의하지 않는다([Kim et al. 1999](https://aclanthology.org/W99-0610/)). 형태소 분석 결과는 도구 버전을 기록하고 원문 위치로 역추적한다.

## 6. P01 파일·판정 흐름과 감사

P01은 기존 `news_source_trials.csv`와 `news_manifest.csv`를 확장하거나 별도 정규화 테이블을 만들어도 된다. 그러나 **API 원시값, 사람이 검증한 값, 추론 라벨을 별도 열/테이블**로 유지해야 한다. 최소 레코드는 아래와 같다.

| 레코드 | 필수 필드 |
| --- | --- |
| `source_trial` | `source_id`, `source_role`(`official_company`/`publisher_news`/`wire_syndication`/`licensed_corpus`), API/매체, 조회 가능 기간, 원문 제공 여부, 재사용/AI 분석 권리, 본문 저장 범위, 실패 사유, 확인 URL·일시 |
| `official_anchor` | `event_family_id`, `doc_id`, `evidence_block_id`, `company_id`, `scope_id`, `product`, `action`, `stage`, `reference_period`, `effective_at`, 공식 발표 시각의 정밀도 |
| `event_family_relation` | 선행·후속 `event_family_id`, `relation_type`(`follow_up_of`/`correction_of`/`contradicts`/`related_case`), 근거, 검토 상태. 선택적 `case_id`는 P02에서 확정 |
| `news_article` | `article_id/doc_id`, `revision_id`, `source_id`, `provider_news_id`, 원 URL, `title`, `byline`, `provider`, `published_at`, `dateline`, `observed_at`, `language`, `body_status`, 추출기 버전, 해시, 권리 조건 |
| `article_classification` | `eligibility`, `reason_code`, `editorial_genre`, `urgency_format`, `production_origin`, 각 라벨 근거 구간/신뢰도/검토자/지침 버전 |
| `article_event_link` | `article_id`, `event_family_id`, `article_event_role`, `coverage_stage`, 기사 원문 기준 `company_id`·`scope_id`·`product`·`action_raw`·`claim_modality`·`reference_period`, `link_evidence_span`, `uncertainty_reason`. 다대다 관계; 기준 사건 값으로 기사 표현을 덮어쓰지 않음 |
| `claim_alignment` | `anchor_claim_id`(추가 사실이면 null 가능), `article_claim_id`(생략이면 null), `article_id`, `event_family_id`, `claim_relation`, 존재하는 쪽의 근거 span, 검토 상태. 한 사건에 여러 행 |
| `sentence_span` / `claim_span` / `chunk_span` | `article_id`, `segment_position`, 본문 offset, `discourse_role`, `speech_flag`, `speaker_type`, 주장 ID, 표현/프레임/확실성/청크 라벨과 근거 |
| `document_relation` | 좌·우 article/revision ID, `content_relation`(새 정정 기사는 `correction_of`), 원출처 근거, 수동 확인 여부 |

**수집 파이프라인:** 공식 anchor 선정 → 기간·기업·제품 검색 → 권리/본문 접근 감사 → 제목/리드/본문 일치·사업 범위 검사 → 기사 장르·기원 후보 부여 → 수동 확인 → 사건 및 주장 정렬 → 문장/청크 파일럿 → 오류 기록. [BIGKinds](https://www.bigkinds.or.kr/v2/news/index.do)는 검색·사설/중복 후보 파악에 쓸 수 있으나, [FAQ](https://www.bigkinds.or.kr/news/faqList.do?page=2)의 무료 다운로드 본문 제한을 넘는 사용 가능 원문을 자동 보장하지 않는다. [NewsStore](https://www.newstore.or.kr/store/prodct/license-news-detail/license-api-list.do)의 본문 제공 및 AI 분석 권리는 **구체적 상품/계약과 실제 응답**으로 확인한다. 수집된 원문은 계약 범위에 따라 보관하며 저장소에 재배포하지 않는다.

**P01 접근·분류 표본(연구 결과가 아닌 비용/품질 점검용 가설):** 2개 기업 × 핵심 사건 범주 4개 × 시기 2개(2024Q1~2025Q1 / 2025Q2~2026Q2)의 **16칸 목표 격자**를 만든다. 서로 다른 12~20개 발표 family를 선정하되, 실제 발표가 없는 칸은 결측으로 두고 20개를 선정할 때는 일부 칸에 복수 family가 들어간다. 각 family에 서로 다른 국내 매체의 기사 후보 **3개를 표집**한다. 한 `doc_id`는 주표집 family 한 곳의 quota만 채우고 다른 사건 링크는 별도로 유지한다. 따라서 `12~20 × 3 = 36~60`은 **고유 기사 후보/주표집 링크의 목표 수**이지, 확보된 완전 본문이나 독립 기자 표현 36~60건의 보증이 아니다. 접근 실패·전재·중복을 빼고 남은 수와 사건별 비교 가능 매체 수를 별도로 보고한다. 더 발견된 후보는 모집단/대체 후보로 기록하되 처음 선정한 실패 후보를 조용히 교체해 접근률을 높이지 않는다. 이 표본은 P01의 접근·분류 검증용이며 언론사별 문체 차이의 통계적 결론을 위한 표본이 아니다.

**권리 확인 뒤 후속 표현 파일럿:** P01에서 본문과 원저작을 검증한 기사를 **포함하여**, 관련 한국어 고유 기사 **총 약 100개**와 목표 변화가 없는 `negative_control` 기사 **약 20개**로 확장한다. 관련 기사는 서로 다른 **20~30개 발표 family**, **5~6개 매체**를 목표로 하며 매체당 관련 기사 15~20개, 최소 10개 서로 다른 family를 층화 점검 기준으로 삼는다. 이는 `약 100개`와 양립하는 운영 범위이지 모든 셀의 충족이나 대표성을 보증하지 않는다. `in_scope_context`(목표 사건이 배경인 기사)는 별도 집계하며 20개 음성 대조 quota에 넣지 않는다. 기사 100개 중 실제로 공통 주장을 맞출 수 있는 **동일 장르·동일 사실의 매체 간 비교 쌍** 수를 따로 보고한다. 이 후속 표본은 P01 완료 필수 산출물이 아니며, [P04](P04_phase3_annotation_pilot.md)의 **100~300개 독립 사건 gold**와 분모가 다르다. 기업·사건 유형·시기·보도 단계가 쏠리거나 목표에 못 미치면 결측을 공개한다.

**검증 항목:** `발견 후보 → 접근 가능 → 완전 본문 → 대상 범위 → 독립 원저작 → 사건/주장 매칭 가능`을 매 단계 건수와 탈락 사유로 보고한다. 첫 20건은 사람 두 명이 본문 완전성·기원·장르·사건 연결을 확인하고, 이견의 원인을 규칙에 반영한다. 문장/청크 주석은 P04에서 이중 주석과 합의 절차를 거쳐 고정한다. 기사 수와 독립 사건 수, 동일 사건 내 매체 수를 별도로 집계한다. 모델 평가가 필요해지면 같은 사건 family의 원문·전재·번역·정정을 동일 split에 두고, 연결된 후속 family의 분리 여부도 평가 목적에 따라 명시한다. 역사 시점 비교에는 그때 관측하지 못한 미래 정정·실행 기사를 쓰지 않는다.

**표현 비교 산출물:** 사건 family별로 `공식 기준 주장 → 매체별 포함/생략·인용 선택 → 동일 주장 표현 구간 → 어절/형태소 청크`를 한 행렬로 만든다. 장르가 같은 기사를 먼저 비교하고, 해설·칼럼은 별도 대비한다. 매체별 “즐겨 쓰는 단어”를 세려면 같은 사건뿐 아니라 같은 주장·화자·위치(예: 리드 대 리드)를 맞춘 쌍을 우선한다. [STEL](https://aclanthology.org/2021.emnlp-main.569/)은 영어 문체 평가에서 내용 통제의 중요성을 보여주지만, 동일 사건만 묶으면 내용이 완전히 통제된다는 근거는 아니다. P01에서는 이 행렬의 작성 가능성을 시험하고, 후속 단계에서 라이선스 허용 범위 안의 **표현 패턴 카드**(상황·주장 유형·구간·표현 특징·출처 링크)로 축약한다. 기사 본문을 통째로 복제한 모음이나 매체 문구 자동 생성의 성능 주장은 만들지 않는다.

## 7. 근거와 적용 한계

| 근거 | 이 설계에 직접 사용하는 부분 | 적용 한계 |
| --- | --- | --- |
| [Fan et al. 2019, BASIL](https://aclanthology.org/D19-1664/) | 동일 사건의 매체별 묶음, 어휘 차이와 선택한 사실/인용 차이 분리 | 영어·미국 정치 기사; 편향 라벨/빈도를 한국 기업 기사에 일반화하지 않음 |
| [Choubey et al. 2020](https://aclanthology.org/2020.acl-main.478/) | 기사 주사건을 기준으로 한 본문 문장 기능 8종과 speech 구분 | 원 논문 라벨이 제목까지 포함하는 것은 아님; 한국어 적용 검증 필요 |
| [Lee et al. 2025, K-News-Stance](https://aclanthology.org/2025.emnlp-main.778/) | 한국 뉴스 장르의 큰 범주, 제목·리드·인용·결론 분리 | 사회 이슈 데이터; 입장 라벨은 분석/의견에 적용, 스트레이트에 강제하지 않음 |
| [Card et al. 2015, Media Frames Corpus](https://aclanthology.org/P15-2072/) | 프레임을 근거 구간에 붙이는 방식 | 미국 정책 프레임을 국내 반도체 기사 분류표로 직접 사용하지 않음 |
| [Kim et al. 1999](https://aclanthology.org/W99-0610/) | 한국어 연어를 형태소 및 비인접 결합으로 보는 이유 | 오래된 연구; 현재 형태소 분석기 성능 보증 아님 |
| [Zheng et al. 2019, Doc2EDAG](https://aclanthology.org/D19-1032/), [Bugert & Gurevych 2021](https://aclanthology.org/2021.emnlp-main.38/) | 한 기사 다중 사건과 교차 문서 사건 연결을 분리 | 각각 중국어 금융 문서/온라인 뉴스 기반; 자동 매칭은 한국어 파일럿 검증 필요 |
| [Wegmann & Nguyen 2021, STEL](https://aclanthology.org/2021.emnlp-main.569/) | 표현 비교에서 내용 통제가 중요하다는 평가 원칙 | 영어 패러프레이즈 과제; 동일 사건 기사 비교의 직접 검증은 아님 |
| [IPTC Genre NewsCodes](https://cv.iptc.org/newscodes/genre/), [NewsStore API](https://www.newstore.or.kr/store/prodct/license-news-search/license-api-list.do) | 장르 용어와 실제 제공 메타데이터의 구분 | 표준의 장르 코드가 NewsStore 개별 기사에 포함된다는 뜻이 아님 |

P01 종료 시 결정할 것은 `본문 접근·사용 권리`, `사건별 매칭 가능한 독립 기사 수`, `장르/전재 자동 후보의 수동 검증 정확도`, `문장·청크 추출 품질`이다. 이 조건이 미달이면 대량 크롤링을 확대하지 않고 사건·매체 범위나 라이선스 경로를 조정한다.
