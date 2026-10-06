# 확보 가능한 Microsoft 공식 사실 참조 — 2026-10-05

<a id="msft-factual-reference"></a>

이번 실행은 개인/비상업 정보 참조를 위한 소량의 비표현적 재무 사실 확인이다. 회사 웹 본문을 재사용 가능한 AI 코퍼스로 채택한 실행이 아니다. 사용자가 인간 검증을 건너뛰고 확보 가능한 자료로 후속 작업을 진행하라고 지시했으므로 인간 검토 상태는 `waived_by_user_not_observed`이며 수행된 독립 주석·gold로 표시하지 않는다.

## 공식 근거와 적용 범위

- 공식 [Microsoft Terms of Use](https://www.microsoft.com/en-us/legal/terms-of-use), 표시 갱신일 2022-02-07, 확인일 2026-10-05. `Documents` 절은 고지 유지, 정보용 비상업 또는 개인 이용, 원문 수정 금지, 네트워크 복사·게시·방송 제한을 둔다. `Personal and Non-Commercial Use Limitation`, `Content`, `No Unlawful or Prohibited Use`도 함께 적용한다.
- 기업 IR footer의 약관 연결은 앞선 P01 [출처 조건 검토](../source_conditions_review.md)에 기록되어 있다. 이번 두 earnings release와 annual report는 그와 같은 `www.microsoft.com`의 공개 공식 문서이다. 원본 HTTP 응답은 같은 호스트에서 200으로 반환했고 redirect가 없었다.
- 원본 HTML 3개는 `private/`의 수정되지 않은 로컬 참조 복사본이다. 페이지의 고지를 유지하고 `private/permission_notice.txt` 및 해당 약관 원본을 함께 보관했다. `.gitignore`의 `artifacts/us_equity/**/private/`가 이 위치를 제외한다. 원본·레이아웃·로고·표 전체를 Git, 공유 문서, agent prompt 또는 외부 LLM에 내보내지 않았다.
- 공개한 파생 파일은 소량의 숫자·기간·표 셀 위치, 표준 재무 라벨, 보고 사업부의 이름·관계, 연결 회계정책의 비표현적 확인 결과만 포함한다. 이는 원문 재배포 허락을 주장하는 경로가 아니라 좁은 사실 참조에 대한 프로젝트 운영 판단이다. 기업/상업 서비스용 운영, 원문 네트워크 공유, 원문 AI 입력, 모델 학습에 대한 포괄 이용권은 확보하지 않았다.
- 약관의 `AI Services` 데이터 추출 금지는 Microsoft가 AI 서비스로 표시·설명한 서비스에 관한 절이다. 일반 IR 보도자료에 기계적으로 적용하지 않았으며, 이를 반대로 일반 IR 원문의 AI 이용 허락으로 해석하지도 않았다.
- 자동 접근은 공개 문서의 소량 로컬 읽기만 조건부로 채택했다. `www.microsoft.com/robots.txt`를 실제 직접 확인하고 각 경로를 검사했다. robots 허용을 저장·AI 이용권의 근거로 삼지 않았다. 원문 자동수집·AI 코퍼스의 확장은 보류한다.

## 실제 경로와 분모

| 단계 | 실제 시도 / 확보 또는 통과 | 범위 |
| --- | --- | --- |
| 정책·접근 preflight | 3 요청 / 3 읽기 | robots 최초 확인 1, 보관용 robots 확인 1, TOU 1. 자료 확보 분자에 제외. |
| 공식 문서 로컬 참조 | 3 고유 문서 / 3 HTTP 200 및 원본 보관 | FY2024 Q4 release, FY2025 Q4 release, FY2025 annual report scope 보완. |
| 숫자 추출 | 2 문서 / 2 숫자 하위표본 | release 2개에서만 33 숫자 occurrence. annual report는 숫자 추출 분자에 제외. |
| 연결 기준 보완 | 1 문서 / 1 로컬 확인 | annual report의 `Principles of Consolidation`과 뒤 정책 위치를 로컬로 확인. 원문 prose는 내보내지 않음. |
| 값·배율·원문 셀 code point offset | 33 / 33 | 최종 `facts_v0_3.jsonl`. |
| 특정 기간·연도 헤더 셀 | 33 / 33 | Q4/FY colspan 그룹과 balance 날짜 셀을 개별 연결. |
| 숫자 문서·독립 발표 family | 2 문서 / 2 family | 각 연도 Q4 실적 발표. scope 보완 문서는 신규 발표 family로 세지 않음. |
| 사업부 보고 관계 | 6 발표 주장 / 3 고유 관계 | `reports_segment`; 고객·공급·제품 상업관계가 아님. |
| 전체 본문 완전성 감사 | 0 / 0 | 실행하지 않음. 표 셀 QA를 본문 완전성으로 보고하지 않음. |
| 원문 AI 입력·학습 | 0 / 0 | 미실행. |
| 인간 독립 검토 | 미실행 | 사용자 지시에 따른 게이트 면제. 독립 gold/일치도 없음. |

새 호스트 직접 네트워크 요청은 정책 3회 + 자료 3회 = 6회이며 모두 200이었다. 최초 robots preflight는 tool trace에만 날짜·결과가 남아 `preflight_access_trials.jsonl`에 정확 시각 미상으로 기록했다. 보관용 robots·약관·release 요청 4회는 `access_trials.jsonl`, annual report 1회는 `scope_corroboration.json`에 개별 시각·hash·위치를 기록했다. 이후 검증·정규화는 로컬 파일만 읽었다. 기존 SEC `data.sec.gov`/`www.sec.gov`의 403 경로는 재시도하지 않았고 NVIDIA 자동 접근도 하지 않았다.

## 자료와 사실 단위

- [FY2024 Q4 release](https://www.microsoft.com/en-us/Investor/earnings/FY-2024-Q4/press-release-webcast), 원문 dateline 2024-07-30. 현재 분기 2024-04-01~2024-06-30(91일)과 현재 연도 2023-07-01~2024-06-30(366일), 2024-06-30 잔액을 분리했다.
- [FY2025 Q4 release](https://www.microsoft.com/en-us/Investor/earnings/FY-2025-Q4/press-release-webcast), 원문 dateline 2025-07-30. 현재 분기 2025-04-01~2025-06-30(91일)과 현재 연도 2024-07-01~2025-06-30(365일), 2025-06-30 잔액을 분리했다.
- [FY2025 annual report](https://www.microsoft.com/investor/reports/ar25/index.html)는 현재 시점 연결 회계기준의 보완 자료다. 정확 발행일은 확인하지 않았으며 2026-10-05 관측시각만 기록했다. 이 보완 자료가 2024 발표 당시 사용 가능했다는 근거로 소급하지 않는다. `scope_corroboration.json`에 정책 위치·hash와 로컬 확인 boolean을 보존했다.

33 숫자 occurrence는 전사 24개(각 release의 Q4/FY 5지표와 잔액 2지표) + 보고 사업부 연매출 9개(두 release의 현재 연도 3개씩, FY2025 release의 FY2024 비교열 3개)다. FY2024 비교열의 사업부 수치는 FY2024 release와 다르므로 발표별 definition version을 분리했다. 전사 FY2024 매출이 두 자료에서 같은 값이라고 사업부 정의까지 동일하다고 판정하지 않는다. 재분류의 원인·범위 정책은 이번 좁은 표 참조에서 감사하지 않았다.

USD million을 원 배율로 보존하고 base-unit 파생값도 별도 보관했다. 회사 공표 표는 `Unaudited` 표시이며 `actual_reported`는 회사가 보고한 실적이라는 뜻이다. 외부 사실 확인·감사 완료를 뜻하지 않는다. 현금 설비투자 원문 괄호 음수는 보존하고 `positive_cash_capex`에는 부호 변환 규칙을 별도 기록했다. 기간의 시작일은 3/12개월 ended-date 헤더에서 calendar-month 경계를 계산한 파생값으로 명시했다.

## 버전과 남은 제한

최종 입력은 `facts_v0_3.jsonl`, `document_manifest_v0_3.csv`, `extraction_audit_v0_3.csv`, `verification_report_v0_3.json`이다. `facts.jsonl` 및 v0.2, 해당 당시 감사·검증 결과를 보존했다. v0.3은 숫자를 바꾸지 않았으며 원문 기간 헤더의 공백 차이와 특정 열 그룹 연결을 보완했다. 이전 감사의 `period_header_confirmed=False`를 전체 기간 검증 통과로 사용하지 않는다. `business_relations.jsonl`의 보고 사업부 관계 6개는 동일하다.

새 미국 기업 1개와 두 실적 발표로 온톨로지를 검증한 adaptation 표본이다. NVIDIA·다른 섹터·고객/공급/제품 관계·전 기간 자료·본문 추출·독립 인간 gold·기업 간 일반화는 미완료다. 권리 조건이나 이용 목적이 이 좁은 범위를 벗어나면 원문 관련 작업을 확장하지 않는다.
