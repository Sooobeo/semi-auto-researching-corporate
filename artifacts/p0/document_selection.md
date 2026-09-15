# P01 API 수집 대상 결정

기준일: 2026-09-15. 범위는 삼성전자(메모리/DS 문장·표, 전사 문맥 보존)와 SK하이닉스(연결 기준)의 2024Q1~2026Q2, 기업당 10개 분기다. 이 파일은 대상 결정이며 API 호출·원문 확보 성공 기록은 아니다.

실행 결과: 기본 후보 40건 원문을 확보했고, SK하이닉스 IR은 공식 사이트의 공개 목록 API에서 첨부 경로를 확인했다. 실제 접수번호·첨부 URL·성공/실패는 [document_manifest.csv](document_manifest.csv), [access_trials.csv](access_trials.csv), [data_feasibility.md](data_feasibility.md)를 기준으로 본다. 아래 첫 시험 표의 상태 열은 **선정 당시의 상태**다.

## 첫 접근 시험: 고유 문서 6개

| ID | 기업 | 대상 문서 | 경로 | 상태 |
| --- | --- | --- | --- | --- |
| SAM-2025Q4-IR | 삼성전자 | 2025년 4분기 실적발표 IR PDF (국문) | [공식 PDF](https://images.samsung.com/kdp/ir/events/2025/2025_4Q_conference_kor.pdf) | URL 확인, 다운로드·본문 추출 미시험 |
| SAM-2026Q1-IR | 삼성전자 | 2026년 1분기 실적발표 IR PDF (국문) | [공식 PDF](https://images.samsung.com/kdp/ir/events/2026/2026_1Q_conference_kor.pdf) | URL 확인, 다운로드·본문 추출 미시험 |
| SAM-2025-FY-DART | 삼성전자 | 사업보고서 (2025.12) | OpenDART `list.json`으로 접수번호 검색 → `document.xml` | 접수번호·원문 미확인 |
| SKH-2025Q4-IR | SK하이닉스 | 2025년 4분기/FY2025 실적발표 IR 자료 | [공식 실적발표 목록](https://www.skhynix.com/ir/UI-FR-IR06/) | 개별 PDF URL·자동 접근 미확인 |
| SKH-2026Q1-IR | SK하이닉스 | 2026년 1분기 실적발표 IR 자료 | [공식 실적발표 목록](https://www.skhynix.com/ir/UI-FR-IR06/) | 개별 PDF URL·자동 접근 미확인 |
| SKH-2025-FY-DART | SK하이닉스 | 사업보고서 (2025.12) | OpenDART `list.json`으로 접수번호 검색 → `document.xml` | 접수번호·원문 미확인 |

SK하이닉스 IR 파일을 자동으로 얻지 못하면 같은 발표의 [2025년 4분기 공식 발표 HTML](https://news.skhynix.com/en/sk-hynix-announces-fy25-financial-results/)과 [2026년 1분기 공식 발표 HTML](https://news.skhynix.com/en/q1-2026-business-results/)을 **대체 문서**로 시험한다. IR PDF와 발표 HTML은 서로 다른 문서로 기록하고, 대체 사유를 남긴다. 이 HTML은 공개 웹 페이지이며 OpenDART 문서 API 결과가 아니다.

## 전 기간 후보 목록

각 기업·분기마다 실적발표 IR 1건과 정기보고서 1건을 기본 대상으로 삼는다. 총 40개 고유 문서 후보(2개 기업 × 10개 분기 × 2종)이며 정정본·언어별 자료·공식 발표·Q&A는 추가 문서다.

| 분기 | 정기보고서명 | IR 대상 |
| --- | --- | --- |
| 2024Q1, 2025Q1, 2026Q1 | 분기보고서 (각 연도 03) | 해당 분기 실적발표 |
| 2024Q2, 2025Q2, 2026Q2 | 반기보고서 (각 연도 06) | 해당 분기 실적발표 |
| 2024Q3, 2025Q3 | 분기보고서 (각 연도 09) | 해당 분기 실적발표 |
| 2024Q4, 2025Q4 | 사업보고서 (각 연도 12) | 해당 분기/연간 실적발표 |

OpenDART에서 `corpCode.xml`로 두 기업의 `corp_code`를 확인하고, `list.json`을 `corp_code`, 접수일 범위, `pblntf_ty=A`, `last_reprt_at=N`으로 조회한다. `report_nm`의 기간을 기준으로 정기보고서를 매칭하고 `rcept_no`로 `document.xml` 원문 ZIP을 가져온다. 접수일만으로 대상 회계기간을 판정하지 않는다. 정정 제출은 별도 revision과 공개시점으로 보존한다. IR은 회사 공식 사이트의 PDF/HTML에 HTTP 접근을 시험하되, 공개된 안정적 문서 API가 확인되기 전에는 **OpenDART API 수집 건수에 포함하지 않는다**.

초기 P01 대상에서 KRX 시세·ECOS·GDELT·SEC EDGAR, 하위 기업 ISC/리노공업, 일반 뉴스·증권사 보고서는 제외한다. 이들은 이후 단계의 외부 변수·적응·확장용이며 초기 원문 접근성의 분모를 흐린다. 공식 실적 발표 HTML과 Q&A/스크립트는 기본 40건의 대체 또는 보조 근거로 목록화한다.

근거: [P01 설계](../../structure/P01_phase0_data_feasibility.md), [OpenDART 고유번호](https://opendart.fss.or.kr/guide/detail.do?apiGrpCd=DS001&apiId=2019018), [공시검색](https://opendart.fss.or.kr/guide/detail.do?apiGrpCd=DS001&apiId=2019001), [원본파일](https://opendart.fss.or.kr/guide/detail.do?apiGrpCd=DS001&apiId=2019003), [삼성 실적발표 목록](https://www.samsung.com/global/ir/financial-information/earnings-release/), [SK하이닉스 실적발표 목록](https://www.skhynix.com/ir/UI-FR-IR06/).
