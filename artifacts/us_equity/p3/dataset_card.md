# P04 dataset card — agent 개발 표본 1.0

기준일 2026-10-06. P04는 Phase 3이다. Microsoft의 기존 개발 자료로 주석·검토·분할 절차를 실행한 패키지다. **인간 gold 0건, 독립 평가 test 0건**이며 정식 P04 인간 주석 완료 조건은 충족하지 않았다. 사용자 요청의 실행 1~5번과 설계서 P04-T01~T12의 전체 완료를 구별한다.

## 범위와 분모

| 단위 | 실제 수 | 포함 범위 |
| --- | ---: | --- |
| 기업 | 1 | Microsoft; 다른 기업·섹터 일반화 미측정 |
| 개발 숫자 문서 / 발표 family | 2 / 2 | FY2024 Q4, FY2025 Q4 공식 release |
| scope 참고 문서 | 1 | FY2025 annual report; 발행일 미상, 2026-10-05 관측 |
| 원자 숫자 주장 | 33 | 전사 24, 사업부 9; FY2025의 FY2024 비교열 3개 포함 |
| 보고 사업부 관계 | 6 | `reports_segment`, 고유 endpoint tuple 3; 기존 숫자 주장 6개를 근거로 참조 |
| 고유 주석 항목 / agent 사건 그룹 | 39 / 2 | 33 숫자+6 관계; 39개의 독립 사건이 아님 |
| 연습 / 본 주석 | 16 / 78 | 최종 가이드 기준 8×2, 39×2; 연습은 본 표본의 부분집합 |
| 본 평가 응답 레코드 | 78 | 각 8질문; A/B 질문 비교 분모 39×8=312 |
| 근거 위치 / 주석 packet | 84 / 39 | 선택 숫자 셀·표 머리글·행 라벨; 본문 전체 아님 |
| 신규 후보 / 접근 시도 / 원본 예약 | 1 / 1 / 1 | FY2026 Q1, 2025-10-29 발표, 메타데이터만 검사 |
| 신규 후보 본문 수동 감사 / 라벨 / test 인증 | 0 / 0 / 0 | 예약은 본문 완전성·평가 적합성의 증거가 아님 |
| 인간 주석 / 인간 조정 / gold | 0 / 0 / 0 | 사람 간 일치도·주석 소요시간 미측정 |

기존 P03 비교 21쌍은 이번 A/B 항목 39쌍과 다른 분모다. 이번에 기록한 표현 중복 edge 3개도 비교 가능성이 확인된 정답쌍이 아니다. 두 개발 family는 같은 누수 그룹에 고정했다. 한국기업 자료는 입력·검증·평가에서 제외했다.

## 활성 파일과 읽기 계약

| 파일 | 계약·용도 | 숫자·시점의 의미 |
| --- | --- | --- |
| `contract_records.jsonl` | `event_schema_v1.json` 1.0.0-agent-pilot; 원자료 계약·원문 위치 검증용 39건 | `normalized.numeric_value`는 USD 기본 단위, `normalized.scale=1`; 원 배율은 `source_scale=1000000` |
| `reviewed_agent_claims.jsonl` | `annotation_output_contract_v1_2.json`의 numeric fact 필드; 검토된 agent 초안 33건 | `facts.numeric_value`는 원 배율 값, `facts.scale=1000000`; `facts.numeric_value_base_units`가 USD 기본 단위 |
| `reviewed_agent_relations.jsonl` | 같은 계약의 relation fact 필드; 검토된 관계 초안 6건 | `reference_period_*`는 보고 표 기간. 실제 `effective_period_*`, `valid_*`는 null |
| `reviewed_agent_events.jsonl` | 2개 발표 anchor의 claim/relation ID 묶음 | 사건 의미·원자성을 인간이 확정한 gold가 아님 |
| `annotations_raw.jsonl`, `assessments_raw.jsonl` | 가이드 `us-p3-guide-1.2`, 등록부 `us-p2-0.1.0` | 수정 전 A/B 본 기록 78건씩; 평가 응답은 facts와 분리 |
| `adjudications.jsonl`, `assessment_reviews.jsonl` | root agent 검토의 원본 연결 39건씩 | 사람 조정 이력으로 사용 불가 |
| `gold_events.jsonl`, `gold_relations.jsonl` | 비어 있음. `gold_status.json` 필수 확인 | 빈 파일은 gold 작업 완료를 뜻하지 않음 |
| `split_manifest.csv`, `split_policy.json` | `us-p3-split-1.0`; 43행 | 문서 4행+주석 39행. 행 수를 기사/사건 수로 세지 않음 |

예를 들어 동일 수치는 계약에서 `64727000000 × 1 USD`, 주석에서 `64727 × 1000000 USD`다. 두 파일의 `numeric_value`를 같은 배율로 읽으면 안 된다. 현금 capex 원문 괄호 음수는 `value_raw`에 보존하고 분석값을 양수 지출로 변환했다. Decimal 배율·원 부호·계약↔주석·원본 연결은 `scripts/p04_validate_handoff.py`로 검사한다. 이 매핑은 새 모델 정답을 생성하는 코드가 아니다.

## 주석과 검토

A/B는 서로의 출력 열람을 금지한 별도 agent 문맥에서 동일한 선택 자료·가이드·등록부를 사용해 결정적 변환을 작성했다. 접근 제한은 작업 지시 기반이며 OS 권한으로 차단하지 않았다. 원본 ID와 정리된 메타데이터는 정답 힌트를 포함한다. 따라서 결과는 공유 입력에 대한 구현 일관성이다. 독립 인간 IAA나 문서 전체에서 사건을 찾는 추출 정확도로 해석할 수 없다.

가이드 1.0→1.1에서 registry 명명 규칙을 구체화했고, 연습에서 발견한 MQ06/MQ08 어휘 이탈을 1.2 응답 enum으로 보완했다. 1.2 연습 검사 후 본 주석을 시작했다. 이전 가이드·연습·오류 보고서는 보존했고 버전들을 독립 표본으로 합산하지 않는다.

조정 전 사실 필드 1,329/1,329와 tuple 39/39가 일치했다. null 127쌍·unresolved 24쌍을 제외한 관측 필드는 1,178/1,178이며 모든 필드가 관측된 완전 tuple은 0건/점수 null이다. 숫자 span 33/33, 문자 overlap 230/230 code point다. MQ01~05·07은 각각 39 unknown으로 관측 분모 0이고 MQ06·08만 각각 39개 관측 응답이다. 높은 일치율은 판단의 유효성·대표성·인간 검토 품질을 입증하지 않는다.

## 시간·분할·미해결

기존 문서 3개와 주석 항목 39개를 adaptation에 둔다. train/dev/test는 모두 0건이다. 개발 release의 마지막 발표일 2025-07-30 이후 후보로 2025-10-29 문서를 예약했지만, 비교열 중복·정정·family 연결은 읽지 않아 미확인이다. 예약 그룹은 임시이며 독립성을 인증하지 않는다. 다른 기업 holdout도 없다.

발표일은 date 정밀도이며 시각·시간대를 만들지 않는다. `date_conflict_status=not_yet_checked`는 계약에 유지되어 있고 reviewed 파생 파일이 이를 생략했다고 감사가 완료된 것이 아니다. 페이지 날짜와 dateline 충돌·전체 본문 수동 감사는 미실행이다. 선택 셀의 XPath·hash·span 검증과 본문 완전성은 별개다.

scope 지원 문서는 발행일 미상으로 과거 발표 시점의 근거가 될 수 없다. 관련 24개 의존성은 후향 사용으로 표시했다. 가이드 자체의 사후 문맥 노출도 모든 주석에 기록했으므로 역사적 블라인드 실험이 아니다. 사업부 표시 정의는 FY2024/FY2025로 분리하고 정책 확인 전 교차 비교는 미해결이다. 관계의 실제 사업 유효기간도 미상이다. 이번 주석 항목에 판정용 prior pair·가정을 제공하지 않아 39항목의 MQ01~05·07을 임의 확정하지 않았다. 기존 P03 비교 21쌍은 별도 기록이다. `unresolved_cases.csv`의 78행은 39항목에 걸친 미해결 사유 수다.

## 출처·권리·보관

Microsoft 공식 IR의 최소 숫자·표준 재무 라벨·기간·위치만 agent 자료로 사용했다. 원문 HTML과 약관은 미변형·고지 유지·로컬 개인 비상업 참조 범위로 Git 제외 private에 보관했다. robots/HTTP 성공을 AI 이용권으로 취급하지 않았다. 원문 prose의 AI 입력·학습 권리는 unresolved이며 입력·학습·외부 원문 공유를 수행하지 않았다. 공개 산출물에 원문 본문을 복제하지 않았다. 이 패키지는 포괄적 재배포 라이선스를 부여하지 않는다.

기존 조건은 `../p0/available_20261005/source_conditions.md`, 신규 단일 예약의 2026-10-06 확인은 `source_reservation/source_conditions.md`와 축별 `source_registry.csv`에 있다. 신규 문서 요청 1회와 정책 요청 2회는 별도 분모이며 redirect·재시도는 0회였다. 수동 원문 감사는 0건이다.

## 후속 사용

P05의 adapter·검증기 개발에는 명시된 adaptation 자료를 사용할 수 있다. 독립 benchmark/성능 주장에는 사용할 수 없다. 필요한 후속 작업은 실제 인간 A/B·조정자 배정 및 소요시간 측정, 허용 경로의 유형 확장·무관 대조, prior 및 표시 정책 확인, 새 표본의 권리·본문·중복 감사, 평가를 보기 전 모델·정책 고정이다. `task_status.csv`, `handoff_p3.md`, `execution_briefing.md`에 구현 완료와 미실행 요구를 구분했다.
