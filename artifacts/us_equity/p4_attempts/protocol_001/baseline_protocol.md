# P05 개발 실행 규약 — 2026-10-06

Microsoft FY2024 Q4/FY2025 Q4 공식 발표 2문서·2 family의 선택 숫자 33개와 보고 사업부 관계 문맥 6개를 처리한다. 전체 HTML에서 셀을 발견하는 작업은 제외한다. 신규 수집·모델 다운로드·외부 호출 예산은 0이다. FY2026 Q1 예약 원문과 폐기된 한국기업 자료는 입력에 넣지 않는다.

P04 공유 agent 참조와의 adaptation 회귀 비교이며 인간 gold·독립 train/dev/test는 각각 0이다. 숫자 전체 묶음은 33개, 관계 tuple은 6개, terminal 결과는 39개가 분모다. 관측/제공 문맥/미상 상태 일치를 분리하고 분모 0은 null이다. 추가 후보는 incomplete reference 때문에 정오 미판정이며 독립 precision/recall/F1은 계산하지 않는다.

adapter는 source_packets/evidence_index의 허용 필드만 읽는다. 원 item/source claim/relation ID는 reference_links에만 둔다. 추출기는 extractor_inputs, input_schema, prediction_schema, rules 파일만 읽도록 별도 실행하며 런타임 파일 접근을 제한한다. doc_id는 provenance와 고정된 발표별 정의 정책 조회에만 사용한다. 숫자 기간은 오직 표 기간/연도 머리글에서 파싱한다. scope label, 회사, 통화/GAAP, 표 용도와 발표별 정의는 사전 제공 문맥이다.

원 숫자·부호·배율은 보존한다. Decimal로 USD 기본 단위 및 scale=1을 출력한다. 괄호 음수 PP&E 지출만 명시적 positive_cash_capex 부호 정책을 적용한다. FCF·margin·중요성·투자 영향은 생성하지 않는다. 기간 시작일은 달력 계산의 파생 결과다. 기간흐름/시점잔액, 발표일/보고기간/관계 실제 유효기간을 분리한다.

매칭 키는 (doc_id, revision_id, record_kind, 정렬한 근거 location/kind/start/end)이며 input ID나 예측 지표/값을 답 매칭에 사용하지 않는다. 같은 키의 여러 후보는 동률 충돌로 남기고 동일 참조의 성공을 중복 계산하지 않는다. 추출 결과를 동결한 후에만 비교기가 agent 참조를 읽는다.

predicted는 구조화 후보 생성 상태다. 모든 후보의 review_readiness는 needs_review, 확률은 null이다. 근거/타입 오류는 quarantined, 지원하지 않는 의미는 abstained, 예상하지 못한 실행 오류는 failed로 기록한다. 입력마다 terminal 결과 한 행을 남긴다. 실패 입력도 비교 분모에 남긴다. 저장소 인계는 validation을 통과한 후보만 가능하며 중요성 판정 완료를 뜻하지 않는다.

출처 조건은 P0 source_conditions.md의 기존 개인·비상업 최소 사실 참조 판단을 계승한다. 원문 prose의 AI 입력/학습·외부 공유 권리는 unresolved다. 로컬 검증기는 허용된 84개 위치만 재조회하며 본문을 출력하지 않는다. 전체 본문·날짜 충돌 수동 감사는 미실행이다. 후향 scope 의존성 24개와 발표별 사업부 정의 한계를 유지한다.
