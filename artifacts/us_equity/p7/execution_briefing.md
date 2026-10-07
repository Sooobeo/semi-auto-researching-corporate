# P08 실행 결과 — 2026-10-07

현재 범위의 개발·자동 검증과 같은 사이트 게시를 완료했다. active run은 `integration_012`, 재현/장애복구 run은 `integration_resume_013`이다. 연구 상태는 `not_evaluated`, 정식 benchmark 완료는 false다.

## 실제 입력과 결과

Microsoft FY2024 Q4(2024-07-30)·FY2025 Q4(2025-07-30) 발표 2문서, 2 family의 기존 검증 입력만 처리했다. 기준 cutoff `2026-10-06`을 보존했다. P05 `m0_004` → P07 `change_002` → P06 `review_change_003`의 계약을 새 배치 출력에서 재현하고 의미 hash를 비교했다. 기존 한국기업/P04/P05 자료나 결과를 다시 생성하지 않았다.

| 단위 | 입력 | 출력/확인 |
| --- | --- | --- |
| 발표 문서 / family | 2 / 2 | 2 / 2, 같은 개발 노출 그룹 |
| 후보 | 39 = 숫자33 + 관계6 | 39개 모두 카드 연결 |
| 카드 | 후보를 검토 그룹으로 묶음 | 33개, 확정 사건 ID 없음 |
| 사람 feedback / gold / 독립 test | 0 / 0 / 0 | 0 / 0 / 0 |
| 신규 수집 / 외부 API·LLM 호출 | 0 | 0 |

권리 근거는 기존 미국기업 출처 등록·P05의 제한된 숫자/표준 라벨/기간/원문 위치 사용 판단이다. 이번 실행에서 이용허락을 확대하거나 새 본문을 수집하지 않았다. 공개 본문 재배포·AI/외부 LLM 이용권을 주장하지 않는다. 공유 snapshot에는 제한 prose·raw/private·개인 메모·키·토큰을 넣지 않았다.

## 구현과 검증

고정 CLI 배치, 단계별 입력/코드/출력 hash, 성공 단계 재사용, 실패/timeout/재개 기록, 카드와 candidate 연결표를 구현했다. 숫자는 Decimal 문자열, 발표일/관측시각/대상 기간은 별도이며 세 검색 시점과 비교/계산 불가 이유를 보존한다.

피드백은 단일 작성자 잠금과 원자적 journal에서 이력을 보존한다. 중복 가져오기·변조 before·없는 ID·허용되지 않은 필드/값·과대 파일을 검사한다. 다른 run에서도 같은 card ID/version/field 수정은 충돌로 처리한다. 카드 내용이 바뀌면 이전 검토를 상속하지 않는다. 채택/같은 값 병합/보류는 별도 소유자 기록이며 원래 예측을 덮어쓰거나 gold로 승격하지 않는다.

최종 P09 공학 검사12/12, P08 장애/합성30/30과 P09 평가 조건7/7, 로컬 API12/12이 통과했다. P04/P05 원래 package도 통과했다. 데스크톱/390px 모바일 로컬 Chrome에서 목록·상세·날짜/scope/빈 결과·근거·초안 재열기·파일 내보내기·평가 사례를 확인했다. 합성 초안은 실제 feedback에 넣지 않았다. 이는 사람 사용성 검사가 아니다.

## 게시와 미완료

[기존 사이트](https://corporate-research-p05.sooobeo.chatgpt.site)에 버전 **4** 배포가 `succeeded`(2026-10-07 13:58 KST)로 확인됐다. 통합 카드·단계 상태·파일 초안/내보내기·P09 개발 평가와 전체 보류 사례가 반영됐다. 기존 custom 접근 2인·revision2를 유지했다. 실제 팀원 로그인은 확인하지 않았다. 게시 페이지 재조회로 배포를 검증하지 않고 Sites의 최종 배포 상태를 기록했다.

정확한 발표시각·날짜 충돌·사업부 정의·보고 관계 유효기간·완전 본문·독립 사람 판단은 여전히 미확인이다. API가 있는 로컬 화면과 게시 snapshot은 다르며 브라우저 저장은 공동 영속 저장이 아니다. 전체 금전 비용·peak memory는 미측정(null)이다.

[실행 manifest](runs/integration_012/run_manifest.json) · [게시 manifest](runs/integration_012/site_update_manifest.json) · [본문/카드 검증](runs/integration_012/validation_report.json) · [브라우저 QA](runs/integration_012/browser_qa.json) · [운영 안내](operator_guide.md) · [전체 변경 파일](../p8/delivery_index.md)
