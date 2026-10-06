# P03 온톨로지 결정

2026-10-05 · 등록부 `us-p2-0.1.0`, metric 기본 정의 `0.1.0`.

| 결정 | 채택 이유와 실제 사용 한계 |
| --- | --- |
| P03-001 · 인간 진행 조건 면제 | 최신 사용자 지시로 P02-T10/P03-T09의 인간 확인을 다음 작업 진입 조건에서 해제한다. `user_waived_requirement`이며 인간 완료·독립 일치도·gold 증거가 아니다. |
| P03-002 · 확보된 한 기업부터 | Microsoft 실제 표만 선정 기업 분모 1로 실행한다. NVIDIA 후보·접근 실패를 삭제하지 않으며 미확보 후보를 company coverage 성공으로 세지 않는다. |
| P03-003 · 일곱 재무 관측과 계산 분리 | 손익/현금흐름의 flow와 기말 assets/cash의 balance를 분리한다. source capex 현금유출을 양의 cash payment로 정규화할 때 원 부호·현금 line 정의를 남긴다. FCF/margin은 입력·수식·정의가 있는 derived이며 회사 발표 수치를 새로 만들지 않는다. |
| P03-004 · 회사 FCF candidate | [SEC Q102.07](https://www.sec.gov/rules-regulations/staff-guidance/corporation-finance-interpretations/non-gaap-financial-measures)은 FCF 정의의 비통일 문제를 설명한다. 기업별 정의와 reconciliation 확인 전 company FCF와 project FCF를 병합하지 않는다. |
| P03-005 · labels와 개념의 분리 | [SKOS §5/§7/§10](https://www.w3.org/TR/skos-reference/)를 참고해 라벨·상하위·동일 매핑을 구분한다. 관측한 line label만 source-backed alias로 채우며 모호한 라벨은 candidate다. FIBO 특정 term/release를 확인한 것으로 표시하지 않는다. |
| P03-006 · guard 있는 배율 | [Python Decimal 공식 문서](https://docs.python.org/3/library/decimal.html)의 문자열 입력·정밀도·반올림 제어를 사용한다. CSV의 `precision=28`, `ROUND_HALF_EVEN`은 계산 정책이다. 원문 숫자의 공개 정밀도를 높이지 않는다. 통화·기간·scope가 같을 때만 scale 변환한다. |
| P03-007 · 자동변환 범위 | `unit_rules.csv`의 scale만 직접 허용한다. %와 %p, 환율, YTD 차분, capex 부호는 별도 guard와 원 입력 확인이 필요하다. unit rule의 존재가 엔진의 해당 계산 실행 완료를 뜻하지 않는다. |
| P03-008 · 회사·사업부·제품 scope | `US-MSFT-CONSOLIDATED`는 이 프로젝트의 전사 reporting scope ID다. 원문에서 consolidated를 명시했는지는 별도 사실로 남긴다. 회사→보고사업부 `reports_segment`, `entity_type=segment`를 P03 sidecar 확장으로 허용한다. 이는 product/customer/supplier 관계가 아니다. P1의 event claim 스키마가 자동 변경되거나 gold가 생성됐다는 뜻은 아니다. |
| P03-009 · 사업부 표시 정의 | 같은 이름의 사업부라도 두 문서의 표시 기준·전년도 비교열이 다르면 definition version을 분리한다. 표시 차이의 원인은 표만으로 추측하지 않는다. FY2024 원본과 FY2025 문서의 FY2024 비교열은 둘 다 보존한다. |
| P03-010 · 관계 사실과 실적 영향 | 관계의 양끝·방향·역할·scope·보고기간·modality·원문 위치를 기록한다. 회사는 segment의 보고 주체이며 금액이 있는 business relation에서도 매출 영향의 인과 추정을 만들지 않는다. 수율·재고·제품 mix·ASP 없는 생산능력→출하량→매출은 proposed다. |
| P03-011 · 전이 범위 축소 | 같은 기업의 별도 실적 발표에 고정 기본 정의를 적용한다. 적용 전 기준과 결과를 보존하고 표시 정의 예외를 adaptation으로 기록한다. 회사 holdout/다른 섹터 일반화/시스템 정확도를 보고하지 않는다. |
| P03-012 · 증거 층 | 최소 numeric/label/table-location fact는 source_supported agent extraction이고 externally_verified/independent_human/gold가 아니다. 본문 policy/제품관계 미조사를 인간 면제로 해소됐다고 쓰지 않는다. |

CSV의 `definition_version`은 개별 정의, `registry_version`은 패키지 버전이다. 정의 변경은 `definition_history.csv`에 새 행으로 남기며 기존 occurrence/source claim을 덮어쓰지 않는다. 별칭의 빈 유효 날짜는 시작/종료를 조사하지 못했다는 의미다. 각 회사 정책을 일반 입문 문헌의 예시로 대신하지 않는다.
