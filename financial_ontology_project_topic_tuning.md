# 금융 리서치 온톨로지 프로젝트 주제 튜닝 정리

## 0. 한 줄 결론

초기 아이디어였던 **“종목·산업 리서치와 공개문건을 수집·정제하여 온톨로지를 구축하고, 이를 바탕으로 투자 의사결정에 필요한 정보를 제공하는 시스템”**은 그대로 두면 향후 금융 특화 GPT, 증권사 자체 AI, Bloomberg/FactSet/FnGuide 계열 서비스의 발전으로 빠르게 범용화될 가능성이 높다.

따라서 프로젝트의 중심을 **“금융 RAG/리서치 챗봇”**이나 **“기업 온톨로지 자체”**에 두기보다,

> **공개정보가 언제 등장했고, 어떤 기업·산업·변수와 연결되며, 어떤 투자 가설을 지지/반박했고, 이후 실제 결과가 어떻게 나타났는지를 시간축으로 축적·검증하는 투자 의사결정 지원 시스템**

으로 튜닝하는 편이 적절하다.

핵심은 **Ontology 자체가 제품이 아니라, 신뢰 가능한 구조화 지식을 만들기 위한 인프라**가 되는 것이다.

---

# 1. 초기 프로젝트 아이디어

초기 구조는 대략 다음과 같다.

```text
공시 / IR / 뉴스 / 리서치 / 산업자료
                ↓
          수집 및 정제
                ↓
      기업·산업 Ontology 구축
                ↓
          Knowledge Graph
                ↓
              LLM
                ↓
       종목/산업 리서치 제공
                ↓
         투자 의사결정 지원
```

예를 들어,

```text
NVIDIA
 └─ AI Cluster 증가
       ↓
800G / 1.6T Optical Demand
       ↓
AAOI / Fabrinet / Coherent
       ↓
Hyperscaler CAPEX와 연결
```

와 같이 기업·제품·고객·산업·기술 간 관계를 구조화하고, 사용자가 특정 종목이나 산업을 질문했을 때 관련 정보를 연결하여 보여주는 시스템이다.

---

# 2. 왜 이 구조만으로는 장기적인 차별성이 약한가

## 2.1 금융 특화 LLM이 가장 먼저 대체할 영역

향후 금융 특화 GPT나 증권사 자체 AI가 발전하면 다음 기능들은 빠르게 기본 기능이 될 가능성이 높다.

- 공시 수집
- 뉴스 수집
- IR/실적발표 자료 파싱
- PDF 및 표 데이터 추출
- 종목별 요약
- 기업 비교
- 산업 구조 설명
- 실적 변화 요약
- 주요 리스크 추출
- 유사기업 비교
- 일반적인 Knowledge Graph 생성
- 기업-제품-고객 관계 탐색

예를 들어 다음과 같은 질문은 향후 별도 시스템 없이도 모델이 상당히 잘 처리할 수 있다.

```text
AAOI의 주요 고객은 누구인가?
최근 실적에서 무엇이 달라졌는가?
CRDO와 AAOI의 차이는 무엇인가?
AI 데이터센터 Optical Value Chain을 기업별로 정리해줘.
최근 8-K 중 투자자가 봐야 할 내용을 뽑아줘.
```

따라서 다음과 같은 구조는 장기적으로 Commodity가 될 가능성이 높다.

```text
문서 수집
→ 파싱
→ Vector DB
→ Knowledge Graph
→ LLM 질의응답
```

즉 **“공개정보를 잘 모아서 AI가 설명해주는 금융 리서치 서비스”** 자체는 장기적인 핵심 차별점이 되기 어렵다.

---

# 3. 그렇다면 Ontology가 의미 없어지는가

아니다.

다만 **Ontology의 역할이 바뀐다.**

초기에는 Ontology가 프로젝트의 핵심 결과물처럼 보였지만, 향후에는 다음과 같이 시스템 내부 인프라로 내려가는 것이 적절하다.

```text
Sources
↓
Extraction
↓
Entity Resolution
↓
Temporal Knowledge Graph
↓
Evidence / Claims
↓
Events
↓
Investment Hypotheses
↓
Signals
↓
Portfolio Decisions
↓
Outcomes
↓
Evaluation
↓
Decision Rule Update
```

이때 Ontology는 주로 다음 영역을 담당한다.

```text
Entity Resolution
+
Temporal Knowledge Graph
+
Semantic Relationship Definition
```

즉,

> **Ontology 자체를 만드는 것이 목적이 아니라, 투자 판단을 위해 필요한 정보를 안정적으로 연결하고 추적하기 위한 구조적 기반으로 사용한다.**

---

# 4. 프로젝트의 핵심을 무엇으로 옮겨야 하는가

기존 방향:

> Financial Knowledge Graph + AI Research Assistant

튜닝 방향:

> **Point-in-Time Investment Intelligence System**

또는 보다 쉽게 표현하면,

> **“시장이 무엇을 언제 알게 되었고, 그 정보가 어떤 기업과 산업에 영향을 주었으며, 이후 실제로 어떤 결과가 발생했는지를 기억하고 검증하는 시스템”**

이다.

---

# 5. 핵심 구조

추천하는 전체 구조는 다음과 같다.

```text
             INFORMATION
                 │
       SEC / IR / News / Data
                 │
                 ▼
        Temporal Knowledge Graph
                 │
        ┌────────┴────────┐
        ▼                 ▼
     Events            Relations
        │                 │
        └────────┬────────┘
                 ▼
             Hypothesis
                 │
                 ▼
              Signal
                 │
                 ▼
             Decision
                 │
                 ▼
              Trade
                 │
                 ▼
             Outcome
                 │
                 ▼
          Historical Replay
                 │
                 ▼
        Decision Rule Update
```

핵심은 단순한 `Information → Answer`가 아니라,

```text
Information
→ Evidence
→ Hypothesis
→ Decision
→ Outcome
→ Evaluation
```

의 Loop를 만드는 것이다.

---

# 6. 단순 Ontology와 튜닝된 시스템의 차이

## 6.1 단순 Ontology

```text
Meta
 └─ CAPEX 증가
      ↓
1.6T Optical Demand 증가
      ↓
AAOI / FN / COHR 수혜
```

이 관계 자체는 금융 특화 LLM이 충분히 생성할 수 있다.

---

## 6.2 튜닝된 구조

```text
Entity
AAOI

Claim
"800G hyperscaler demand accelerating"

Evidence
- 2026-08 Earnings Call
- 2026-09 Customer CAPEX Guidance
- Supply Chain Data

Known At
2026-08-07 16:15 ET

Confidence
0.82

Affected Variables
- Revenue Growth +
- Gross Margin +
- Customer Concentration Risk -
- 2027 EPS Revision +

Historical Comparable Events
23 cases

Observed Market Reaction
1D
5D
20D

Current Valuation
EV/Sales percentile

Portfolio State
Current Optical Exposure

Decision State
WATCH → BUY candidate
```

이 경우 시스템은 단순한 “지식 저장소”가 아니라 **Investment State Machine** 또는 **Decision-support System**에 가까워진다.

---

# 7. 왜 시간축(Point-in-Time)이 중요한가

금융에서는 다음 질문이 중요하다.

> “지금 사실인가?”

보다

> **“그 당시 시장 참가자가 알 수 있었는가?”**

예를 들어 어떤 공시가

```text
2026-05-05 16:12 ET
```

공개되었다면 해당 정보를 5월 5일 장중 의사결정에 사용하면 미래정보가 섞인다.

따라서 다음 시간을 구분할 필요가 있다.

```text
effective_at
published_at
available_at
ingested_at
```

이 구조를 갖추면 다음 질문이 가능해진다.

```text
2026년 3월 14일 당시 공개되어 있던 정보만으로
이 투자 가설은 합리적이었는가?
```

이 부분은 단순한 최신 리서치 챗봇보다 훨씬 중요한 차별점이 될 수 있다.

---

# 8. Evidence와 Provenance가 필요한 이유

LLM이 어떤 관계를 생성했다고 해서 바로 사실로 저장하면 안 된다.

예:

```text
Claim
"Microsoft is a major customer of Company A"
```

위 Claim에는 반드시 다음 정보가 연결되어야 한다.

```text
Claim
↓
Source
↓
Document
↓
Page / Paragraph / Section
↓
Published Timestamp
↓
Confidence
```

또한 출처 간 내용이 충돌할 수 있다.

```text
Source A
→ Customer = Microsoft

Source B
→ Customer = Unnamed Hyperscaler
```

따라서 시스템은 단순히 Truth 하나를 저장하는 것이 아니라,

```text
Claim
Evidence
Confidence
Source Quality
Temporal Validity
```

를 함께 관리하는 것이 적절하다.

---

# 9. Consensus DB와 Ontology는 같은가

완전히 같지는 않다.

## 9.1 Consensus의 역할

FnGuide와 같은 컨센서스 서비스는 기본적으로 여러 증권사가 발표한 추정치를 정규화하여 집계한다.

예:

```text
Broker A
AAOI FY2027 EPS = X

Broker B
AAOI FY2027 EPS = Y

Broker C
AAOI FY2027 EPS = Z

        ↓

AAOI / FY2027 / EPS
        ↓
Consensus
```

핵심 Entity는 대략 다음과 같다.

```text
Company
Broker
Analyst
Estimate
FinancialMetric
FiscalPeriod
```

즉 **여러 전망치를 동일한 기준으로 정규화하고 집계하는 데이터 시스템**이다.

---

## 9.2 Ontology의 역할

Ontology/Knowledge Graph는 범위가 더 넓다.

예:

```text
Company
Product
Technology
Customer
Supplier
Industry
FinancialMetric
Estimate
Event
Claim
Document
Analyst
Broker
```

그리고 관계 역시 다음처럼 다양하다.

```text
SUPPLIES
CUSTOMER_OF
COMPETES_WITH
DEPENDS_ON
BENEFITS_FROM
GUIDED
ESTIMATED_BY
MENTIONED_IN
```

따라서 관계를 단순화하면,

> **Consensus DB는 금융 Ontology 위에서 관리할 수 있는 하나의 데이터 영역이다.**

라고 보는 것이 적절하다.

---

# 10. FnGuide 같은 회사도 Ontology를 자체 구축하는가

공개적으로 확인 가능한 범위에서는 FnGuide가 자신들의 내부 시스템을 “Formal Ontology”나 “Knowledge Graph”라고 명시한다고 단정하기는 어렵다.

다만 컨센서스와 금융 데이터를 운영하려면 최소한 다음 구조는 필요하다.

```text
Company
├─ Identifier
├─ Ticker
├─ Industry Classification
├─ Financial Statements
├─ Consensus
│   ├─ Broker
│   ├─ Analyst
│   ├─ Estimate
│   └─ Fiscal Period
├─ Ownership
└─ Corporate Events
```

즉 내부적으로는 반드시

- Entity Identification
- Taxonomy
- Normalization
- Relationship Mapping
- Validation
- Historical Data Management

과 같은 구조가 필요하다.

다만 그것이

- RDF/OWL 기반 Formal Ontology인지
- Property Graph인지
- Relational DB + Taxonomy인지

는 외부에서 단정하기 어렵다.

따라서 프로젝트에서 “FnGuide도 Ontology를 사용한다”고 단정하기보다는,

> **금융 데이터 제공업체 역시 기업·지표·기간·애널리스트·이벤트 등을 일관되게 관리하기 위한 독자적인 데이터 모델과 분류 체계를 필요로 한다.**

정도로 표현하는 것이 안전하다.

---

# 11. 이 프로젝트를 통해 대학생이 실제로 경험할 수 있는 것

이 프로젝트의 가치는 단순히 “금융 GPT를 만들어봤다”가 아니다.

제대로 구현하면 다음 경험을 한 프로젝트 안에서 모두 할 수 있다.

---

## 11.1 Data Modeling

처음에는 단순하게 다음 정도로 생각하기 쉽다.

```text
company
news
financials
```

하지만 실제로는 바로 문제가 발생한다.

예:

```text
Meta는 회사인가 브랜드인가?
Google과 Alphabet은 같은 Entity인가?
AWS는 Amazon과 분리해야 하는가?
2027 Revenue는 Calendar Year인가 Fiscal Year인가?
Ticker가 바뀌면 동일 기업으로 볼 것인가?
M&A 이후 기존 Entity는 어떻게 처리할 것인가?
```

결국 다음과 같은 구조를 설계하게 된다.

```text
entity
identifier
relationship
valid_from
valid_to
source
confidence
```

즉 실제 데이터 플랫폼의 핵심 문제인 **Data Modeling**을 경험할 수 있다.

---

## 11.2 Entity Resolution

실제 문서에서는 동일 기업이 여러 방식으로 표현된다.

```text
Advanced Micro Devices
AMD
AMD Inc.
Advanced Micro Devices, Inc.
NASDAQ: AMD
```

이들을 하나의 Entity로 연결해야 한다.

반면 다음은 상황에 따라 분리해야 한다.

```text
Google
Alphabet
Google Cloud
GCP
```

즉,

> **지저분한 현실 세계 데이터를 일관된 Entity System으로 변환하는 과정**

을 직접 경험하게 된다.

---

## 11.3 Information Extraction

실적 발표에서 다음 문장이 있다고 가정한다.

```text
"We expect 1.6T shipments to begin ramping in the second half."
```

단순 요약이 아니라 다음처럼 구조화한다.

```text
subject: Company
predicate: EXPECTS_RAMP
object: 1.6T Product
period: 2027 H2
source: Earnings Call
confidence: 0.91
```

여기에는 다음 기술이 사용될 수 있다.

- Named Entity Recognition
- Relation Extraction
- Classification
- Structured Output
- LLM Extraction
- Rule-based Parsing
- Validation

---

## 11.4 Temporal Data Engineering

금융에서는 정보의 시점이 매우 중요하다.

따라서 다음을 관리하게 된다.

```text
effective_at
published_at
available_at
ingested_at
valid_from
valid_to
```

이 경험은 일반적인 챗봇 프로젝트에서는 거의 다루지 않는 영역이다.

---

## 11.5 Provenance / Data Validation

어떤 Claim이 어디에서 왔는지 추적한다.

```text
Claim
→ Source
→ Document
→ Exact Location
→ Timestamp
→ Confidence
```

또한 여러 출처가 충돌할 때,

```text
Source Reliability
Recency
Directness
Confidence
```

등을 기준으로 처리해야 한다.

즉 금융 데이터 서비스에서 중요한 **Validation Pipeline**을 경험한다.

---

## 11.6 산업 구조 이해

Ontology를 만들기 위해서는 산업 자체를 구조적으로 이해해야 한다.

예:

```text
AI Datacenter
→ Accelerator
→ Networking
→ Optical
→ Power
→ Cooling
```

또는

```text
Semiconductor
→ Fabless
→ Foundry
→ Wafer
→ Packaging
→ HBM
```

기업을 단순 종목 단위로 보는 것이 아니라 **Value Chain과 Causal Relationship**을 중심으로 보게 된다.

---

## 11.7 금융 변수 이해

다음 변수의 차이를 정확히 이해해야 Schema를 만들 수 있다.

```text
Revenue
Bookings
Backlog
ARR
CapEx
Orders
Guidance
Consensus
Estimate Revision
Surprise
Margin
FCF
```

따라서 금융 데이터 자체에 대한 이해도 자연스럽게 깊어진다.

---

## 11.8 정보와 투자성과의 차이 이해

가장 중요한 학습 중 하나다.

예를 들어 시스템이 다음 관계를 정확히 발견했다고 가정한다.

```text
Meta CAPEX ↑
→ 1.6T Demand ↑
→ Optical Vendor 수혜
```

그래도 해당 기업 주가가 하락할 수 있다.

이유:

```text
이미 가격에 반영
Valuation 부담
시장 기대치가 더 높음
Margin 악화
Customer Concentration
Macro Shock
NASDAQ 급락
```

따라서 실제 프로젝트를 진행하면 다음 차이를 직접 경험하게 된다.

```text
Knowledge
≠
Prediction
≠
Trading Signal
≠
Portfolio Decision
```

이 부분이 단순 산업 리서치 프로젝트보다 중요한 학습 포인트다.

---

# 12. 프로젝트를 너무 크게 만들지 않는 방법

Bloomberg나 FnGuide 전체를 따라 만들려고 하면 범위가 너무 크다.

따라서 특정 산업을 좁게 잡는 것이 적절하다.

예:

> **AI Infrastructure Knowledge Graph / Investment Intelligence System**

기업 수:

```text
약 30~50개
```

예시:

```text
CRDO
AAOI
FN
CIEN
COHR
LITE
AVGO
MRVL
ANET
NVDA
AMD
...
```

---

# 13. 추천 Entity Scope

처음부터 모든 종류의 데이터를 다루지 않고 다음 정도로 제한한다.

```text
Company
Product
Technology
Customer
Supplier
Industry
FinancialMetric
Estimate
Event
Claim
Document
```

---

# 14. 추천 Relation Scope

```text
SUPPLIES
CUSTOMER_OF
COMPETES_WITH
BENEFITS_FROM
DEPENDS_ON
GUIDED
ESTIMATED_BY
MENTIONED_IN
```

필요하면 추후 확장한다.

---

# 15. 추천 Source Scope

초기 MVP에서는 공개성과 신뢰도가 높은 자료만 사용한다.

```text
SEC Filing
Earnings Call
Investor Presentation
Company Press Release
```

뉴스나 2차 자료는 이후 확장한다.

---

# 16. 사용자에게 보여줄 결과물 예시

질문:

```text
Meta의 CAPEX 증가에 노출된 Optical 기업은?
```

시스템 응답:

```text
Meta CAPEX
   │
   ├── 1.6T Deployment
   │       │
   │       ├── AAOI
   │       ├── FN
   │       └── COHR
   │
   └── Networking
           ├── CRDO
           └── ANET
```

그리고 Edge를 클릭하면,

```text
왜 이 관계가 존재하는가?
↓
Source
↓
Exact Filing / Earnings Call
↓
Published Timestamp
↓
Confidence
↓
Historical Changes
```

를 확인할 수 있도록 한다.

---

# 17. 최종적으로 지향해야 할 데이터 구조

## Entity

```text
Entity
- entity_id
- entity_type
- canonical_name
- identifiers
- valid_from
- valid_to
```

## Relationship

```text
Relationship
- subject_entity
- predicate
- object_entity
- valid_from
- valid_to
- confidence
- source_id
```

## Document

```text
Document
- document_id
- source_type
- publisher
- published_at
- available_at
- url
```

## Claim

```text
Claim
- claim_id
- subject
- predicate
- object
- source_id
- evidence_location
- confidence
- known_at
```

## Event

```text
Event
- event_id
- event_type
- affected_entities
- occurred_at
- known_at
- evidence
```

## Hypothesis

```text
Hypothesis
- hypothesis_id
- thesis
- supporting_claims
- contradicting_claims
- created_at
- status
```

## Signal

```text
Signal
- signal_id
- hypothesis_id
- variable
- direction
- strength
- generated_at
```

## Outcome

```text
Outcome
- outcome_id
- signal_id
- horizon
- realized_return
- realized_fundamental_change
- evaluation
```

---

# 18. 향후 확장 방향

MVP 이후에는 다음 방향으로 확장할 수 있다.

### 18.1 Consensus Integration

```text
Broker
Analyst
Estimate
Revision
Consensus
```

을 추가하여,

```text
산업 Event
→ 기업 Fundamental 변화
→ Analyst Estimate Revision
→ Consensus 변화
→ Price Reaction
```

까지 연결할 수 있다.

---

### 18.2 Historical Replay

특정 과거 날짜를 지정하고 당시 공개된 정보만 복원한다.

```text
"As of 2026-03-14"
```

이후 시스템이 당시 생성할 수 있었던 투자 가설과 실제 결과를 비교한다.

---

### 18.3 Decision Rule Learning

예:

```text
Hyperscaler CAPEX Upward Revision
+
Optical Demand Commentary
+
Supplier Guidance Revision
+
Valuation Below Threshold

→ BUY Signal
```

그리고 과거 사례를 통해 성능을 검증한다.

---

### 18.4 Portfolio-aware Decision

단순히 기업별 판단이 아니라 현재 포트폴리오까지 고려한다.

```text
AAOI Buy Signal
BUT
Current Optical Exposure = 18%

→ Position Size 제한
```

이 경우 시스템은 단순 리서치 도구에서 **Portfolio Decision Support System**으로 확장된다.

---

# 19. 이 프로젝트에서 피해야 할 방향

다음 중 하나로 끝나면 차별성이 약하다.

### 피해야 할 형태 1

```text
SEC + 뉴스
→ RAG
→ 챗봇
```

### 피해야 할 형태 2

```text
기업 관계를 LLM으로 추출
→ Neo4j
→ 그래프 시각화
```

### 피해야 할 형태 3

```text
기업 검색
→ 요약
→ 매수/매도 추천
```

### 피해야 할 형태 4

```text
Bloomberg / FnGuide를 축소 복제
```

---

# 20. 프로젝트의 기술적 핵심

LLM API를 호출하는 부분보다 다음이 더 중요하다.

```text
1. Entity Resolution
2. Financial Data Modeling
3. Temporal Knowledge Representation
4. Provenance Tracking
5. Claim Validation
6. Relation Extraction
7. Historical Replay
8. Future-information Leakage Prevention
9. Hypothesis Tracking
10. Outcome Evaluation
```

즉 프로젝트의 기술적 난점은 **LLM 자체가 아니라, 실제 데이터를 신뢰 가능한 구조로 만드는 과정**에 있다.

---

# 21. 프로젝트를 통해 얻는 핵심 경험

한 문장으로 정리하면,

> **Unstructured Real-world Information → Trustworthy Structured Knowledge → Decision-support System**

을 처음부터 끝까지 설계하는 경험이다.

구체적으로는 다음 경험을 얻는다.

```text
Finance
+
Industry Research
+
Data Engineering
+
Database Design
+
NLP / LLM
+
Knowledge Graph
+
Temporal Data
+
Backend
+
Quantitative Evaluation
```

따라서 단순히 “금융 GPT를 만들어본 경험”보다 범용성이 크다.

---

# 22. 최종 주제 표현 후보

## 후보 A — 가장 기술적인 표현

> **Point-in-Time Financial Knowledge Graph for Investment Decision Support**

---

## 후보 B — 금융/투자 중심

> **Temporal Investment Intelligence System Based on Public Financial Information**

---

## 후보 C — 연구 프로젝트 느낌

> **공개 금융정보의 시간축 기반 구조화와 투자 의사결정 지원 시스템**

---

## 후보 D — 시스템 구축 중심

> **기업·산업 관계 및 투자 가설 추적을 위한 Temporal Knowledge Graph 구축**

---

## 후보 E — 가장 현재 논의에 가까운 표현

> **공개문건 기반 Temporal Knowledge Graph와 Evidence-Hypothesis-Outcome Loop를 활용한 투자 의사결정 지원 시스템**

---

# 23. 현재 시점에서의 추천 방향

프로젝트를 계속 진행한다면 다음처럼 정의하는 것이 가장 적절하다.

> 공개 공시, 실적발표, IR 자료 등에서 기업·제품·고객·기술·재무변수 간 관계와 주요 Claim을 추출하고, 각 정보의 출처와 공개 시점을 보존하는 Temporal Knowledge Graph를 구축한다. 이후 개별 정보가 투자 가설을 어떻게 지지하거나 반박하는지 연결하고, 해당 가설 이후의 실제 Fundamental 및 시장 결과를 기록하여 반복적으로 검증 가능한 투자 의사결정 지원 시스템을 구현한다.

핵심은 다음 네 요소다.

```text
1. Structured Knowledge
2. Point-in-Time
3. Evidence / Provenance
4. Hypothesis → Outcome Evaluation
```

Ontology는 이 네 요소를 가능하게 하는 **기반 기술**로 위치시킨다.

---

# 24. 최종 판단

이 프로젝트는 다음과 같이 평가할 수 있다.

### 의미가 약해지는 버전

> 공개문건을 모아서 기업 Ontology를 만들고 GPT가 투자 정보를 답해주는 서비스

향후 금융 특화 AI가 빠르게 대체할 가능성이 높다.

### 의미가 남는 버전

> 공개정보의 시점·근거·기업 관계를 구조화하고, 투자 가설과 실제 결과까지 연결하여 과거 판단을 재현하고 평가할 수 있는 시스템

LLM이 발전하더라도 데이터 구조와 검증 시스템의 가치가 남는다.

따라서 **“Ontology 프로젝트”가 아니라 “Investment Intelligence Infrastructure 프로젝트”로 보는 것이 현재 논의의 최종 튜닝 방향**이다.
