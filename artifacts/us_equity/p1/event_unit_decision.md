# ADR P02-001 · 분석 단위

2026-10-05 · 상태: 잠정 구현, 팀 검토·새 사례 독립 시험 대기.

기본 사실 단위는 **문서 revision에서 근거를 가진 원자 주장(atomic claim)**이다. claim마다 회사·scope·행위 또는 지표·modality·기간·화자와 근거 배열을 기록한다. event는 동일 발표 내 함께 발생한 주장들을 연결하고, event_family는 같은 발표의 재보도·번역·수집 revision을 연결한다. 같은 URL의 source 수정은 revision으로 보존하지만, **새로 발행된 정정 발표는 새 doc_id·새 family와 correction_of로 연결**한다. 독립적인 새 후속 발표도 새 family와 follow_up_of를 갖는다. 정정/후속의 새 family는 이전 family와 별도 leakage_group으로 연결해 split 누수를 검토한다. family 또는 leakage_group이 시간 경계를 걸치면 분할 이동 또는 embargo를 검토한다.

| 후보 | 장점 | 채택 판단 |
| --- | --- | --- |
| 문서 한 건 = 사건 한 건 | 입력 목록과 대응 쉬움 | 미채택: 연차보고서의 다기간·다지표·다관계를 한 사건으로 합침 |
| 문장 한 건 = 사건 한 건 | span 단위가 단순함 | 근거 블록으로만 사용: 숫자표·주석·앞 문장 화자가 필요할 수 있음 |
| 원자 주장 + evidence 배열 | scope·기간·계획/실적별 비교와 다문장 근거를 함께 표현 | 기본 단위로 잠정 채택 |
| 여러 문서 하나의 cluster | 재보도 중복과 누수 제어 | family 수준에서 사용: 원문 claim과 문서 revision은 유지 |

[Doc2EDAG §3–4, pp.339–340](https://aclanthology.org/D19-1032.pdf)은 문장 밖 인자와 문서 내 여러 record를 다룬다. 이를 근거로 문서 전체 문맥과 여러 근거 블록을 허용했다. 중국어 금융 공시·원격 감독 라벨링과 본 프로젝트의 영문 인간 주석은 다르다. trigger를 생략하는 모델 선택을 그대로 채택하지 않고 원문 action_raw를 보존한다.

[FinQA §3–4, pp.3699–3700](https://aclanthology.org/2021.emnlp-main.300.pdf)의 근거·계산 프로그램 분리는 derived 계산의 입력 ID·수식·반올림 기록에 적용한다. 단순화한 표 QA에서의 결과를 복잡한 공시표 추출 성공률로 사용하지 않는다.

설명용 합성 반례: 한 문서가 제품 X의 개발 계획과 제품 Y의 판매 실적을 기록하면 claim 두 건이다. 계획 발표 뒤 실행 발표가 나오면 문서·event·family를 새로 만들고 follow_up_of를 기록한다. 새 금액 없이 같은 계획을 다시 인용한 문서는 기존 발표 family에 연결하되 반복 claim을 삭제하지 않는다. 가상의 A→B 공급 계획은 relation claim으로 표현하며 매출 감소·증가 판단은 assessment에만 둔다.

분모는 문서 / revision / 고유 event / 발표 family / claim / relation tuple / 비교 가능 pair를 각각 센다. 실제 기업 표본으로 적용한 수와 인간 독립 확인 수는 handoff_p1.md에 기록하며 이 ADR 자체는 검증 결과가 아니다.
