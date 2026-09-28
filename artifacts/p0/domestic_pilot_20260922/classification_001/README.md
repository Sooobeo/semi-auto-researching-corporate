# P01 잠정 분류 상태와 사람 검토 대기열

2026-09-22. `body_audit_003`의 로컬 본문·문장·규칙 span과 원래 후보 39개를 입력으로 만들었다. 온톨로지나 확정 분류 결과가 아니다.

| 파일 | 실제 행 수 | 의미 |
| --- | ---: | --- |
| article_classification.csv | 39 | 본문 확보 22개/미확보 17개의 현재 상태; 장르·기사 scope·기원 판단 대기 |
| rule_signals.csv | 39 | 제목 표식·짧은 본문·인용·회사 언급 등 단순 규칙 신호; 라벨 확정 근거 아님 |
| article_event_links.csv | 39 | 원래 표집 family 연결 유지; 사건 역할·coverage·주장 대응 미확정 |
| human_review_queue.csv | 40 | 실제 본문 20개 × 사람 검토자 2명 슬롯; 모두 미배정·pending |

검토 목표는 20개이며 실제 선정도 20개다. 짧은 본문 1개를 우선 포함하고 서로 다른 family와 매체를 고려했다. 선정 표본은 13개 family, ETNEWS 9개·ZDNET_KR 8개·EDAILY 3개다. 전체 확보 본문 22개와 검토 선정 본문 20개를 구분한다. 이전 검토 대기열은 변경하지 않았다.

제목 표식은 출처 본문이 있으면 저장된 원 언론사 제목, 없으면 검색 제목에서 검사한다. 이번 39개 입력에서 지정된 괄호형 속보·칼럼/사설/기고·인터뷰 표식은 모두 0개였다. 표식 부재가 일반 기사·스트레이트·원저작을 뜻하지 않는다. `urgency_format`도 `unknown`을 유지한다.

본문 미확보 17개는 접근 불가 상태를 명시하며 숫자·인용·문장 신호를 빈칸과 사유로 남긴다. 이를 본문 내 언급 0개로 해석하지 않는다. 나머지 22개도 본문 완전성, 기사 범위, 독립 원저작, 동일 주장·화자·위치 검토가 남아 있어 문체 분석 대기다. 단순 회사 언급 수로 사업 범위나 사건 역할을 확정하지 않았다.

원문·제목·짧은 span은 이 디렉터리에 복제하지 않았다. 비공개 자료의 doc/revision 참조, hash, offset index 위치만 기록했다. 원시 본문은 기존 Git 제외 `body_audit_003/raw/`에 있다. 권리 상태와 사용자 연구 실행 지시를 별도로 이어받으며 새 권한을 부여하지 않는다.

입력 body hash와 저장 span roundtrip, 39행 보존, 20개 문서 각각 2개 슬롯, 전체 pending 상태, 출력의 원문 필드 부재를 점검했다. 사람 검토 완료·확정 장르·확정 기원·확정 scope·주장 정렬은 모두 0개다.

재실행 시 존재하지 않는 출력 디렉터리를 지정한다.

```powershell
python scripts/p01_domestic_classify.py --candidates artifacts/p0/domestic_pilot_20260922/article_candidates.csv --body-audit-dir artifacts/p0/domestic_pilot_20260922/body_audit_003 --output-dir artifacts/p0/domestic_pilot_20260922/classification_NEW
```
