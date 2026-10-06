# P04 조정 전 agent 비교

두 agent의 본 주석 78개를 39개 item으로 정렬했다. 동일 원자료·가이드·등록부 문맥에서 작성한 결정적 변환의 일관성 검사다. 인간 독립 일치도와 시스템 추출 정확도는 미측정(null)이다.

- 사실 전체 tuple 일치: 39/39. 숫자와 관계의 분모 및 필드별 exact/nonnull/null 수는 agreement_results.json과 agreement_by_field.csv에 있다.
- 숫자 span exact: 33/33. overlap은 원 DOM 셀 code point 문자 기준이며 토큰 F1과 구별한다.
- 질문 응답은 8질문×39개 pair이다. unknown/NA 등을 뺀 양쪽 실질 응답 pair는 78개다. 분모가 0인 질문은 substantive rate=null이다. 조정 후 값을 원본 일치도 계산에 사용하지 않았다.
- MQ01~MQ05/MQ07의 unknown은 근거 부족이며 낮은 중요성이 아니다. 같은 unknown끼리의 일치로 판단 능력을 입증하지 않는다.
- 공유 가이드/metadata에 의한 일치이므로 사람용 chance-corrected 계수를 만들지 않았다. guide1.1 연습의 vocabulary 오류와1.2 보완은 별도 이력으로 보존한다.

39개 agent 조정 기록은 원본 annotation/assessment와 근거에 연결된다. 사실이 일치해도 과거 scope·사업부 표시 정책·prior 부재·실제 관계 유효기간은 미해결로 유지했다. 최종 산출물은 reviewed_agent_*이며 gold_events/gold_relations는 실제 인간 독립 원본이 없어 0건이다.

## 자가검증 후 보완

별도 구현으로 원본 78건을 재계산하고 22개 반례를 검사했다. 전체 필드 비교는 1,329/1,329이며 null 127쌍과 unresolved 문자열 24쌍을 제외한 관측 필드 비교는 1,178/1,178이다. 기존 `nonnull` 열은 null만 제외하므로 미해결 문자열도 포함한다. 이를 관측 가능성과 혼동하지 않도록 `observed_state_agreement`와 독립 보고서의 필드별 분모를 추가했다.

숫자 관측 필드는 1,034/1,034, 관계는 144/144다. 모든 계약 필드가 관측된 완전 tuple은 0건이므로 해당 점수는 null이다. 39/39 전체 tuple 일치에는 같은 결측 상태끼리의 일치가 포함된다. MQ06과 MQ08을 제외한 6개 질문은 각각 39개 unknown으로 관측 분모 0, 점수 null이다. span 문자 비교는 230/230 code point이며 원문 진실 검증이나 end-to-end 추출 평가가 아니다.
