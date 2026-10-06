# 검토 필요성 표현 후보

2026-10-05 · 후보 질문형 0.1.0 · 점수·가중치·임계값 미채택.

재무보고 materiality, 사건 연구의 시장 반응, 투자 리서치의 검토 행동, 문장 감성을 별도 개념으로 유지한다. [IFRS Practice Statement 2 공식 About](https://www.ifrs.org/issued-standards/list-of-standards/materiality-practice-statement/)은 IFRS 재무제표 작성의 비강제 가이드임을 확인했다. 전문 문단을 읽지 않았고 미국 기업의 법적 materiality 기준으로 채택하지 않는다. [MacKinlay 원논문 페이지](https://www.jstor.org/stable/2729691)는 서지만 확인 가능한 상태이며 본문 미독이다. event study 방법·공식·사건창을 구현하거나 인용한 실험은 없다.

| 표현 후보 | 저장 방법 | 이번 결정·후속 검증 |
| --- | --- | --- |
| 단일 중요성 점수 | ordinal label | 보류: 근거 부족과 작은 영향, 관계 변화와 규모를 섞을 위험 |
| 다차원 질문 | 질문 ID별 응답·근거·미상 이유 | 잠정 채택: 가정 영향·검토 행동·근거·비교·재무/사업을 분리 |
| 후속 검토 행동 | maintain/revise/investigate/defer/not_applicable | 후보 채택: 질문·as_of·평가자 이유를 함께 기록 |
| review_readiness | supported/needs_review/not_comparable | 근거/비교 운영 상태로만 사용; 중요성 및 외부 확인과 분리 |

각 응답에는 authored_by/author_kind/created_at/as_of와 evidence_refs를 붙이고 unknown 또는 unable_to_judge를 허용한다. 새 정보의 방향과 유리/불리 판단, 영향 규모는 자동 추론하지 않는다. 금액 미공개 관계 변화도 대상이다.

P04에서 독립 원본 주석의 nominal/ordinal 일치도와 질문 이해도를 확인하고 P06에서 dev 효용을 비교한 뒤 합산 필요성을 결정한다. 이번에 독립 인간 라벨·gold·효용 결과는 생성하지 않았다.
