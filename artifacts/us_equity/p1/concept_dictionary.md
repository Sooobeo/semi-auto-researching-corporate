# 개념 사전 초안

2026-10-05 · 0.1.0 · 회사별 metric/관계 등록부를 아직 확정하지 않았다.

| 개념 | 운영 정의 | 구별·반례 |
| --- | --- | --- |
| document / revision | 동일 출처 문서의 안정 ID / 실제 관측한 파일·수정본 ID | 새로 발행된 정정은 새 doc_id; 같은 파일 재수집은 접근 로그만 추가 |
| atomic claim | 단일 비교 대상·동작 또는 지표·scope·기간·modality를 가진 출처의 주장 | 전체 연차보고서를 하나의 claim으로 쓰지 않음 |
| event / event_family | 발표 내 연관 주장 묶음 / 같은 발표 재보도·번역·수집 revision 묶음 | 새 정정·후속 발표는 새 family+correction_of/follow_up_of; leakage_group 별도 연결 |
| reported fact | 출처가 해당 내용을 발표했다는 근거 | actual_reported만으로 외부 사실 확인 완료가 되지 않음 |
| business relation | 두 개체 사이 방향·역할·scope·시점·조건을 가진 출처 주장 | 같은 문장에 두 회사 이름 등장 ≠ supplies_to |
| concept / metric / alias | 해석 정의 / 측정 정의 / 정의에 매핑되는 원문 표현 | CFO라는 alias만으로 회사 FCF와 동일 metric이 되지 않음 |
| prior state | cutoff 이전 이용 가능하고 비교 조건을 충족하는 이전 주장/관계 | 현재 정정 수치를 과거 시점 상태에 소급 사용하지 않음 |
| review readiness | 카드 목적에 필요한 근거·필드·비교 조건의 운영 상태 | supported ≠ 사실의 외부 검증 ≠ 높은 중요성 |
| accounting materiality | 재무보고 작성 맥락의 중요성 개념 | 리서치 담당자의 조사 행동과 하나의 점수로 합치지 않음 |
| research review need | 기존 가정·해석을 다시 검토할 필요에 대한 평가 | 긍정 감성·주가 상승을 정답으로 쓰지 않음 |

대표명/별칭·정의·상하위·mapping은 [W3C SKOS §5, §7, §10](https://www.w3.org/TR/skos-reference/)에 구분 근거가 있다. 비슷한 라벨을 exactMatch로 승격하지 않는다. CSV 등록부로 먼저 구현하며 RDF 도입은 필수 범위가 아니다.

출처·추출 run·수정자·계산 계보는 [PROV-O §3.1–3.2](https://www.w3.org/TR/prov-o/)의 entity/activity/agent와 derivation·revision 구별을 참조한다. 현재는 ID 연결로 표현하며 OWL 추론이나 검증된 그래프를 구축했다는 뜻이 아니다.

[FIBO 공식 소개](https://spec.edmcouncil.org/fibo/)는 금융 개념·관계 정의의 조사 후보다. 이번에는 개별 term·release를 검증하지 않아 특정 KPI나 고객 관계를 FIBO에서 채택하지 않았다.
