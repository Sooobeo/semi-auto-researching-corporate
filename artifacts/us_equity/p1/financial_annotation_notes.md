# 재무 사실·계산 작성 메모

2026-10-05 · 실제 회사 회계정책·계산 선정은 대기.

자료 흐름은 분석 질문·as_of → 재무제표/주석/MD&A 검토 → 비교/대사 → 사업 해석 → 가정 유지/수정/보류 → 메모/검토 → 후속 갱신이다. [CFA FIN01 공개 Exhibit 1](https://www.cfainstitute.org/insights/professional-learning/refresher-readings/2026/integration-financial-statement-analysis-techniques)의 단계 구분을 적용하며 유료 전문·모든 팀원의 분석 수행을 확인한 것은 아니다.

| 개념 후보 | fact로 남길 것 | 계산·판단 제한 |
| --- | --- | --- |
| 이익과 현금흐름 | 순이익·CFO·개별 비현금/운전자본 조정, 기간과 주석 | 차이만으로 부정 판정 금지; 대사 입력 누락은 incomplete |
| 성장·수익성 | revenue·gross profit·operating income, GAAP/조정 정의 | 동일 scope·기간·정의·양의 매출 분모 확인 후 margin; %p와 % 변화 구별 |
| 운전자본 | 채권/재고/채무 잔액 시점·CFO 조정 | 잔액 차이를 환율·인수·분류 변경 확인 없이 현금흐름 항목으로 대체하지 않음 |
| 설비투자·감가상각 | PP&E 현금 지출·비현금 D&A, 원문 부호와 취득 범위 | 지출을 당기 비용으로 처리하지 않음; 투자현금흐름 전체를 capex로 바꾸지 않음 |
| GAAP/non-GAAP | 각 metric 정의·개별 조정·세금·대사표 위치 | 같은 이름만으로 두 회사 정의 동일 판정 금지 |
| 유동성·차입 | cash·현재/장기 부채·만기 주석·borrowings | 모든 liabilities를 차입금으로 매핑하거나 미공개 만기를 추정하지 않음 |

[SEC FIN03 가이드의 Balance Sheets, Cash Flow Statements, Read the Footnotes, Read the MD&A](https://www.sec.gov/investor/pubs/begfinstmtguide.htm)를 읽어 잔액 시점과 기간 흐름, 주석·경영진 설명을 구분했다. 입문 안내의 단순 예시를 회사별 GAAP 측정 정의로 사용하지 않는다. FIN02 [공개 소개·요약](https://www.cfainstitute.org/insights/professional-learning/refresher-readings/2026/evaluating-quality-financial-reports)을 확인해 보고 품질과 실적 품질을 분리하며 특정 기업을 좋다/나쁘다로 판정하지 않았다.

source의 괄호 음수와 scale을 raw로 보존한다. CFO는 source 부호를 유지한다. 프로젝트 FCF 후보가 CFO - positive_cash_capex라면 지출을 양의 금액으로 정규화한 별도 입력과 sign rule을 둔다. company FCF metric은 회사 정의로 별도 저장한다. [SEC Non-GAAP C&DI 100.02/100.05/102.07](https://www.sec.gov/rules-regulations/staff-guidance/corporation-finance-interpretations/non-gaap-financial-measures)은 기간/회사 정의 차이와 FCF의 비통일 정의·대사·해석 제한을 보여준다. 이를 법적 적합성 판정 모델로 쓰지 않는다.

재무상태는 balance_or_flow=balance와 as_of_date, 손익/현금흐름은 flow와 period_start/end·duration·quarter/YTD/annual을 보존한다. 52/53주 회계연도는 실제 날짜·길이를 확인한다. JSON numeric_value는 Decimal 문자열이다. denominator 또는 input이 null이면 미계산이며 부족한 입력의 사유를 남긴다.

financial_reconciliations·scenario는 derived 레코드, 사업 영향·가정·메모는 assessment 레코드다. 수작업 기준에는 계산한 사람·시점·모델 출력 사전 열람 여부·동료 검토를 기록한다. Codex 계산을 사람의 독립 수행 증거로 표시하지 않는다.
