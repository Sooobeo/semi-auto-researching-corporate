# P02 검색·설계 실행 범위

기준일 2026-10-05 · 가이드 개발 0.1.0 · 작성자 Codex · 팀 검토 미실시.

현행 입력은 structure v1.2이며 이전 한국기업 자료·gold·성능은 제외했다. Microsoft와 NVIDIA는 접근 조사 후보일 뿐 선정 기업이 아니다. 기업·회계기간·문서 quota·독립 주석 담당은 미확정이다. 이번 작업은 검색 계획과 규약 구현이며 팀의 범위 합의를 대신하지 않는다.

| RQ | 이번 설계 질문 | 검색어 / 포함 조건 | 제외·제약 |
| --- | --- | --- | --- |
| RQ1 | 한 문서 복수 주장과 여러 문서 동일 발표를 어떻게 기록하는가? | financial document-level event extraction annotation schema; 원저자 논문 본문·공식 proceedings | 중국어 성능을 미국 영어 정확도로 환산하지 않음 |
| RQ2 | 수치·표·문장 근거와 계산을 어떻게 분리하는가? | financial numerical reasoning evidence program; FinQA 본문 | 공개 데이터셋의 기업 원문 이용권을 논문 라이선스로 가정하지 않음 |
| RQ3 | 숫자 없는 관계 변화·부인·후속을 어떻게 표현하는가? | ontology relationship provenance temporal claim; W3C·EDM Council 공식 표준 | 이름의 동시 출현은 관계 근거에서 제외 |
| RQ4 | 회계 materiality와 리서치 행동은 어떻게 다른가? | IFRS materiality practice statement; SEC materiality; event studies; 공식 기관·원논문 | 사후 수익률·감성을 과거 판단 라벨로 사용하지 않음 |
| RQ5 | 무엇을 독립 일치도와 gold로 부르는가? | inter-coder agreement reliability unitizing; 원논문 | agent 여러 회답을 독립 인간 주석으로 세지 않음 |
| RQ6 | 회계 개념을 사업 질문과 어떻게 연결하는가? | financial statement analysis framework; non-GAAP free cash flow; SEC·CFA 공개 안내 | 유료 전문·회사 정책·재무 해석은 미독/미검토로 남김 |

먼저 REFERENCES의 primary URL을 열어 서지·버전과 실제 읽은 절을 등록했다. 핵심 본문의 선택 구간을 읽고 설계 결정에 연결했으며 논문 전체 정독은 주장하지 않는다. 실패 URL·초록만 읽음·공식 개요만 확인을 literature_map.csv에 보존한다. 추가 검색은 현재 스키마에서 해결되지 않은 영어 관계/시간 주석과 미국 기업 원문 사례에 한정한다.

P02-T01의 질문·검색 계획은 작성 완료다. 팀별 가용시간·교차검증 담당·최초 기업 합의는 미완료이며 guideline_questions.md에서 추적한다.
