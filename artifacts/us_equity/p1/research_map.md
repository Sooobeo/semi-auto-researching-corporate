# RQ → 문헌 → 구현 규칙 → 검증

2026-10-05 · 연구/양식 초안 0.1.0 · 실제 미국 source-backed 사례 0건.

서지는 [literature_matrix.csv](literature_matrix.csv)가 기준본이다. literature_map.csv는 같은 표의 호환 이름이며 축별 literature_events/materiality/metrics는 생성한 부분집합이다. 읽은 상태·절/페이지·과업·전이 한계를 행마다 보존했고 전문 전체를 읽었다고 표시하지 않았다. 14개 자료를 등록했고 R09 본문은 미접근, R05는 초록, IFRS/FIBO는 공식 개요만 확인했다.

| RQ | 실제 읽은 근거 | 선택한 구현 규칙 | 이번 검사 / 남은 검증 |
| --- | --- | --- | --- |
| RQ1 단위·다중 주장 | [Doc2EDAG §3–4 pp.339–340](https://aclanthology.org/D19-1032.pdf) | P02-001 atomic claim + evidence[] + event/family | 합성 한 문서 두 제품·계획/실적 분리; 실제 문서·인간 시험 미실시 |
| RQ2 숫자·근거·계산 | [FinQA §3–4 pp.3699–3700](https://aclanthology.org/2021.emnlp-main.300.pdf) | raw/normalized/derived; formula/input refs | null prior+20%의 절대값 미계산·숫자 0 유지; 실제 표 QA 미실시 |
| RQ3 개념·관계·계보 | [SKOS §5/7/10](https://www.w3.org/TR/skos-reference/), [PROV-O §3.1–3.2](https://www.w3.org/TR/prov-o/) | concept/alias/mapping·doc/revision/run/author 분리 | 공급자→고객 역할/방향 fixture 검사; 실제 entity/term mapping 미실시 |
| RQ4 검토 필요성 | [IFRS About](https://www.ifrs.org/issued-standards/list-of-standards/materiality-practice-statement/), R09 본문 미독 | MQ 다차원·readiness 별도·사후 outcome 분리 | assessment=null 허용; 독립 중요성 라벨·효용 미측정 |
| RQ5 독립 주석 | [Artstein & Poesio §2.1/2.6](https://aclanthology.org/J08-4004.pdf) | 조정 전·척도/분모별 일치도·human/gold 구별 | synthetic→gold/test 오표시 거부; 인간 일치도 0표본/계수 미계산 |
| RQ6 재무·분석 흐름 | [SEC 가이드](https://www.sec.gov/investor/pubs/begfinstmtguide.htm), [Non-GAAP Q102.07](https://www.sec.gov/rules-regulations/staff-guidance/corporation-finance-interpretations/non-gaap-financial-measures), [CFA Exhibit 1](https://www.cfainstitute.org/insights/professional-learning/refresher-readings/2026/integration-financial-statement-analysis-techniques) | 잔액/기간·회사/프로젝트 FCF·사실/해석/가정 구별 | 역전 기간 거부; 실제 정책·대사·개인 수작업 수행 미실시 |

형식·의미 regression은 schema_validation_report.json에서 재계산한다. 합성 검사를 영어 추출 정확도·원문 감사·인간 일치도·gold 결과로 보고하지 않는다. 미해결 질문은 guideline_questions.md, 인계 상태는 handoff_p1.md다.
