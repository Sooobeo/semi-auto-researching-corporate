# 작성 가이드 0.1.0

2026-10-05 · Codex 초안 · 인간 독립 pilot·gold 0건.

영문 원자료로 사실을 작성한다. 출처 조건과 실제 확인 범위를 provenance에 연결하고 기록 대상이 source_supported / synthetic인지 먼저 선언한다. Microsoft·NVIDIA는 후보이며 실제 선정·미노출 test 보장은 하지 않는다.

## 작성 순서

1. manifest의 doc_id/revision_id와 source_registry의 rights_basis_ref를 확인한다. 저장·AI 입력·외부 전송이 unresolved이면 허용되지 않은 본문을 이 양식에 복사하지 않는다. URL/서지·미확인 이유를 기록하고 해당 본문 기반 주장은 대기한다.
2. 제목·발행/접수 시각·본문 dateline·observed를 각각 확인한다. 날짜만 있으면 published_at=null이고 time_precision=date다. 충돌을 arbitrarily 해소하지 않는다.
3. claim마다 회사/scope·제품·동작/metric·기간·modality·화자를 지정한다. 독립 claim으로 분리되는 기준은 event_relation_rules.md다.
4. raw 원표현을 기록한 뒤 normalized를 작성한다. 값·범위 endpoint·비율 종류·통화·배율·분모를 원문 머리글과 대조한다. 0과 null을 구별하고 null에는 필드 경로별 누락 이유를 둔다.
5. evidence의 block/셀/XPath·필요 머리글·주석 위치를 확인한다. verified span은 원문 Unicode code point [start,end)로 지정하고 raw_text[start:end]가 선택 표면과 일치함을 검사한다. normalized offset이 원문 offset과 다른 경우 mapping을 검증하기 전 gold로 사용하지 않는다.
6. 회사 발표의 actual_reported와 externally_verified를 구별한다. 계획·forecast·부인·조건·possibility는 현재 확정 상태로 바꾸지 않는다. normalized의 영향·인과 추정을 제거하고 assessment에 기록한다.
7. prior는 prior_state_policy.md에 따라 cutoff와 비교 조건을 확인한다. 못 찾으면 prior_state_status=prior_not_found, prior_claim_id=null이다.
8. 중요성 질문에 답할 때 as_of 자료만 제시하고 후속 실적·가격 반응을 숨긴다. 답할 수 없으면 unable_to_judge이며 낮은 중요성으로 대체하지 않는다. assessment 미작성은 null로 두어 fact 기록을 유지한다.
9. 계산은 derived에 입력 ID·수식/버전·단위·반올림·누락 입력을 기록한다. prior 또는 input이 null이면 insufficient_inputs, output=null이다. 계산한 값을 발표 실적 숫자로 재분류하지 않는다.
10. 수정은 새 revision과 supersedes_record_id로 추가한다. 독립 원본 주석과 조정 후 record는 따로 보존한다.

## 독립 시험·평가

P02-T10은 두 명 이상의 **인간**이 처음 보는 새 영문 사례를 설명 없이 독립 작성해야 완료다. 이번 Codex 양식 작성·합성 fixture 검사는 그 시험을 대신하지 않는다. 도구가 작성한 사실은 agent_draft로 표시하며 independent_human/gold 라벨을 사용하지 않는다.

일치도는 조정 전 원본에서 회사·숫자·단위·기간 exact match, code-point span exact/overlap, 관계 tuple/필드, nominal/ordinal 질문을 분리한다. [Artstein & Poesio §2.1, §2.6 pp.555–556,563–565](https://aclanthology.org/J08-4004.pdf)을 참조하며 최종 척도·분모·unknown 제외 정책은 실제 pilot 전에 고정한다. 일치도는 정확도나 원문 진실의 증거가 아니다.

가이드·alias·registry를 만드는 데 쓴 문서는 adaptation/practice에 둔다. 정정·번역·전재 계보가 split 양쪽에 갈라지지 않도록 family를 함께 관리한다. 후속 발표가 새 family여도 동일 사업 에피소드 누수 위험은 별도 그룹으로 검토한다.

## 미해결 기록

근거 미접근, 원문 누락/혼입, 시각 충돌, fiscal/calendar 혼동, 제품/전사 scope, 숫자 정의, 공개하지 않은 고객, 미검증 offset은 모두 field_missing_reasons와 uncertainty_reason에 남긴다. 판단 불가를 빈칸·0으로 바꾸지 않는다. 실제 source 사례·독립 작성자·팀 합의가 없으면 가이드의 완성이나 gold 확보로 보고하지 않는다.
