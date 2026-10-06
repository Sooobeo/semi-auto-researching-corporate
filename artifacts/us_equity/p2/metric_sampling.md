# P03 표본·분모 고정

2026-10-05 · 등록부 `us-p2-0.1.0` · 확보 가능한 공식 표의 소표본 실행.

사용자의 최신 지시 “인간 검증은 했다고 치고 다음꺼 해봐 확보할 수 있는 자료들 선에서 해결해”를 P02-T10/P03-T09의 독립 인간 검증 **진행 조건 면제**로 적용한다. 상태는 `user_waived_requirement`다. 수행 증거가 없는 인간 주석·일치도·조정 결과를 만들거나 완료했다고 기록하지 않는다. 기존 미완료 기록은 이 시점의 면제와 함께 보존한다.

초기 실행 대상은 실제 접근한 Microsoft 전사 재무 표다. NVIDIA는 앞선 접근 조사 후보이며 확보 전에는 선정 기업 분모나 실제 사례에 포함하지 않는다. 회사 coverage 분모는 **선정·실제 적용 기업 1개**이고 후보 기업 수 2개와 구분한다. 전사와 보고 사업부는 다른 scope다. 표에 나온 제품/고객 이름만으로 공급·고객·경쟁 관계를 만들지 않는다.

기본 표본은 FY2024 Q4 공식 release의 연간·Q4 손익, 연간·Q4 현금흐름, 기말 재무상태와 사업부 표다. 같은 기준을 FY2025 Q4 release에 먼저 적용하고 별도 기간 문서의 적용 예외를 남긴다. 두 문서는 서로 다른 실적 발표 family다. 자료의 실제 날짜·원 기간 머리글을 사용하며 FY2024 연간 366일과 FY2025 연간 365일을 기록한다. 사업부 표의 전년도 비교열은 그 문서의 표시 기준으로 보존하고 이전 release의 같은 이름 수치와 자동 병합하지 않는다.

재무 후보는 revenue, operating_income, net_income, cfo, positive_cash_capex, total_assets, cash_and_equivalents다. 프로젝트 FCF와 operating_margin은 별도 계산 정의이며 원문 회사 실적 claim이 아니다. 회사 FCF는 회사 정의 확인 전 candidate다. 생산능력/생산량/출하량은 혼용 차단용 candidate 정의이며 실제 관측·기업 KPI 채택으로 세지 않는다.

관계 후보는 회사가 보고하는 사업부 `reports_segment`와 공개 근거 확인 때만 사용할 제품/서비스·협업·공급·경쟁 정의다. 사업부 표는 회사→사업부 구조의 발표 근거로 사용할 수 있지만 고객 계약이나 제품 공급의 근거가 아니다. 기간상 관계는 해당 표의 reporting period만 지지하며 사업부 창설일·종료일을 추정하지 않는다.

확보 경로와 권리의 최종 근거는 `../p0/available_20261005/source_registry.csv`, `source_conditions.md`, `document_manifest_v0_3.csv`다. 원본은 private/raw 제외 규칙 아래 보관하며 표 수치·짧은 line label·위치의 최소 사실 레코드만 등록부에 연결한다. 기업 본문 prose의 대량 저장·AI 입력 조건이 unresolved인 구간은 확장하지 않는다. 원문 사실은 `facts_v0_3.jsonl`, 감사는 `extraction_audit_v0_3.csv`에서 재계산한다. 앞선 facts/manifest/audit를 보존하고 전사 연결 범위의 공식 연차보고서 로컬 확인을 새 revision으로 연결한다. 문서 전체/본문 추출 성공률과 최소 표셀 확보율을 혼동하지 않는다.

`occurrence`는 문서·revision·행/열·reference period의 개별 표현이다. 고유 문서·발표 family·회사·기간 수는 각각 catalog에 집계한다. 같은 이전 기간 수치가 후속 release에 다시 나타나도 독립 시계열 사건이 늘어난 것으로 해석하지 않는다. 두 발표의 각 source claim은 보존한다. 관계 claim 수와 고유 주체–타입–대상 관계 수를 나눈다.

조사하지 않은 범위는 NVIDIA 실적·제품 및 고객 관계, Microsoft 제품별 수익·고객/공급/경쟁 본문, 회사 non-GAAP/FCF reconciliation, Q&A, 연결 범위 외의 공시 주석, 추가 섹터다. 원문 미공개·미접근·미조사를 구분하며 이 범위에서 못 찾았다는 사실을 회사가 공개하지 않았다는 결론으로 바꾸지 않는다. 표본은 가이드/등록부 개발에 노출된 adaptation이고 gold·untouched test가 아니다.

`baseline_registry_0.1.0/`는 FY2024만의 등록 상태를 재구성해 script 적용 전에 hash로 고정한 기록이다. FY2025 사실은 수집 과정에서 이미 보였으므로 이 재적용은 사후 adaptation 점검이다. 블라인드 전이 시험이나 미열람 자료 검증으로 해석하지 않는다. 18개 FY2025 문서 source claim을 적용했으며 개별 필드 판단은 72행으로 별도 집계한다.

실제 최종 개수는 `handoff_p2.md`에 기재한다. 근거 확보 전 표에 0이 있으면 `statistics_status=not_yet_checked`이며 실제 부재를 검증한 수치가 아니다. 확보 후의 0은 명시된 선택 표셀 안에서 관측되지 않았다는 뜻이다. CSV 빈칸은 미상/미확인 유효 날짜, JSON의 null은 기록된 missing reason을 뜻한다.
