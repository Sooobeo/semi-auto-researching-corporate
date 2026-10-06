# 중요성·검토 질문 후보

2026-10-05 · 0.1.0 · facts와 별도의 assessment.questions[]에 저장한다.

| ID | 질문 | 허용 응답 | 판단 불가/후속 행동 |
| --- | --- | --- | --- |
| MQ01 | 기존 사업·제품/고객/공급 관계 가정을 다시 검토할 필요가 있는가? | yes/no/unknown/not_applicable | prior·scope·관계 근거 부족은 unknown; 관련 가정 ID 요청 |
| MQ02 | 회사 가이던스 또는 분석자의 같은 미래 기간 가정이 바뀌었는가? | yes/no/unknown/not_applicable | company_guidance와 analyst_assumption 구별; 서로 다른 기간 비교 금지 |
| MQ03 | 수익성·성장의 비교 가능한 새 정보가 있는가? | yes/no/unknown/not_applicable | 금액 없으면 영향 규모 미공개; 관계 fact 삭제 금지 |
| MQ04 | 현금 창출·설비투자·운전자본의 설명을 다시 확인할 필요가 있는가? | yes/no/unknown/not_applicable | input/조정 주석 부족은 investigate/defer |
| MQ05 | 유동성·차입 부담의 검토가 필요한가? | yes/no/unknown/not_applicable | 공시 없는 만기·차입 분류는 추정 금지 |
| MQ06 | 필요한 fact를 원문 위치·기간·scope와 연결했는가? | sufficient/insufficient/unknown/not_applicable | missing 필드를 명시; 낮은 중요성으로 대체 금지 |
| MQ07 | prior와 동일 기준의 비교가 가능한가? | comparable/conditional/not_comparable/unknown | 정의/기간/회계/단위/통화·관계 조건을 각각 확인 |
| MQ08 | 다음 행동은 무엇이며 이유는 무엇인가? | maintain/revise/investigate/defer/not_applicable/unable_to_judge | 채택/수정은 사람의 판단이며 별도 evidence·rationale 필요 |

질문별 response 문자열은 후보이며 가이드와 함께 버전을 고정한다. assessment에는 response가 평가자의 의견이라는 author_kind를 남긴다. 모든 질문을 단일 점수로 합치지 않는다. 사용자/팀 담당이 답하지 않은 이번 agent 초안에는 실제 중요성 응답을 채우지 않았다.

readiness=supported는 카드 목적에 필요한 근거·비교 조건이 충분한 경우, needs_review는 시각 충돌/미공개/미검증 위치 등 추가 확인이 필요한 경우, not_comparable은 필수 비교 기준이 비호환인 경우다. facts 미해결 필드와 불확실성의 위치를 함께 남긴다. 비교가 필요한 카드에서 prior가 없으면 needs_review로 두고 별도 이유를 쓴다. 중요한 사건도 not_comparable일 수 있다.

화면/작업 패킷은 as_of에 이용 가능했던 문서와 prior만 제공한다. 사후 가격·후속 실적·정정·다른 평가자 답을 숨기고 사후 지식을 기억한 경우 exposure 한계를 기록한다. 합의 뒤 값으로 인간 일치도를 계산하지 않는다.
