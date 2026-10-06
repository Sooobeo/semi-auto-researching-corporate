# P04 실행 브리핑 — 2026-10-06

요청한 **1~5번 실행 묶음**을 순서대로 수행하고 각 단계의 자가검증·개선 이력을 남겼다. 결과는 Microsoft 자료의 agent 개발용 주석 패키지다. 실제 인간 주석·gold·미노출 test는 0건이며, 정식 P04 전체 완료와 구별한다.

| 순서 | 수행·검증 | 반영한 개선 |
| --- | --- | --- |
| 1. 표본·노출·예약 | 숫자 33·관계 6·발표 family 2, 기존 지원 문서 1; 신규 후보 접근 1/1·예약 1/1 | 기존 event ID 유지, 비교열 중복 3개·후향 scope 의존성 24개 분리, 실제 hash 비교 |
| 2. 계약·가이드 | 공통 계약 39/39, 근거 84개, 오류 변형 22/22 차단 | 현금흐름 enum·원 capex 부호·미감사 출처·기간 시작 파생 근거·관계 보고기간/실제 유효기간 구분 |
| 3. 연습·본 주석 | 최종 연습 8항목×2, 본 주석 39×2=78 및 평가 78; 원자료 대응·계약 검사 통과 | 가이드 1.1 명명 규칙, 1.2 질문 응답 enum으로 연습 오류 수정; 이전본 보존 |
| 4. 비교·검토 | 별도 구현 재계산, 22/22 반례; 39개 agent 조정·원본 연결 | null·unresolved 151쌍 제외 분모 추가, 완전 관측 tuple 0/null, human gold와 분리 |
| 5. 분할·연결·인계 | 43행 분할 manifest; adaptation 42행·예약 1행; 수치/참조 검사 39/39 및 13/13 반례 | 파일별 백만 USD/base USD 계약표, 최신 예약 상태, entity/scope 검사 분리, 미완료 설계 항목 명시 |

최종 통과 여부와 실행 시각은 `stage_reviews/stage_01_final.json`부터 `stage_05_final.json`까지가 기준이다. 각 `stage_*_improvements.md`에 발견 사항과 수정 결과를 기록했으며 이전 단계 게이트 후 다음 번호를 실행했다. 오류·이전 가이드·연습을 지워 통과 이력만 남기지 않았다.

## 확보·산출물

- 개발: MSFT FY2024 Q4/FY2025 Q4 release 2문서·2 family. 원자 숫자 33, 보고 사업부 관계 6(기존 숫자 6개 참조·고유 endpoint 3), agent 발표 그룹 2.
- 지원: FY2025 annual report 1문서. 발행일 미상/2026-10-05 관측이며 사건 quota·과거 기준 근거에서 제외.
- 신규: [FY2026 Q1 공식 문서](https://www.microsoft.com/en-us/Investor/earnings/FY-2026-Q1/press-release-webcast) 후보 1·접근 1·예약 1, 발표일 2025-10-29. 정책 요청 2는 별도. 본문·수치·비교열·라벨은 개발에 노출하지 않았고 완전 본문 수동 감사 0건이다.
- 본 주석 78, 평가 78, agent 검토 39; 미해결 78행은 고유 39항목에 대한 사유다. 인간 독립 기록·조정·gold·주석 소요시간은 미측정/0.
- 기존 P0/P1/P2 입력 14개와 원문 hash를 보존했다. 신규 결과는 `artifacts/us_equity/p3/`, 실행·검증 코드는 `scripts/p04_*.py`, 탐색 링크는 루트/structure 문서에 추가했다. 파일별 목록과 hash는 `artifact_inventory.csv`·`package_manifest.json`에서 확인한다.

## 일치도의 해석

A/B는 동일 선택 자료·등록부·가이드로 결정적 변환을 작성했다. 전체 필드 1,329/1,329, 관측 필드 1,178/1,178, 숫자 span 33/33 일치다. 이는 공유 입력의 구현 일관성이다. 완전 관측 tuple 0, 6개 질문의 관측 분모 0이므로 해당 점수는 null이다. 사람 IAA·추출 정확도·중요성 판단 성능을 측정한 결과가 아니다.

## 제한과 다음 작업

모든 기존 자료는 adaptation이다. 신규 후보도 unlabeled이며 중복·본문·AI 이용권이 미확인이라 test로 인증하지 않았다. train/dev/test 각 0, 다른 기업 holdout 0이다. 가이드 자체의 사후 문맥 때문에 역사적 블라인드 실험을 주장하지 않는다.

과거 scope 24개·사업부 표시 정의 9개·관계 실제 유효기간 6개·prior 39개의 부족을 유지했다. 발표 날짜와 dateline 충돌·전체 본문 수동 감사는 미실행이다. 계획·실행·정정·부인·무관 대조·고객/공급 관계가 없어 유형별 추출 recall이나 일반화도 평가하지 못했다.

원문은 Microsoft의 좁은 개인·비상업 정보 참조 조건으로 private에 미변형·고지 유지 보관했다. 권리 근거와 축별 상태는 `source_reservation/source_conditions.md`·`source_registry.csv` 및 기존 P0 기록에 있다. AI 입력·학습·원문 외부 공유 권리를 HTTP 성공으로 추론하지 않았으며 원문 prose를 AI 입력/학습하거나 공유하지 않았다. 독립 인간 검토·신규 이용 범위/본문/누수 감사·prior/정의 정책 확보가 정식 P04의 남은 작업이다.

읽을 순서는 [dataset card](dataset_card.md) → [분할 감사](split_audit.md) → [인계](handoff_p3.md) → [작업별 상태](task_status.csv)다. 검증 재실행은 [verification_commands.md](verification_commands.md)를 따른다.
