# P01 로컬 본문 위치·offset 진단

2026-09-22. 최종 로컬 재추출 기록은 이 `body_audit_003` 디렉터리다. 네트워크 요청 없이 기존 수집 manifest와 HTML을 사용했다. 실행 코드는 `scripts/p01_domestic_body_audit.py`다.

```powershell
python scripts/p01_domestic_body_audit.py --manifest artifacts/p0/domestic_pilot_20260922/collect_smoke/manifest.csv --manifest artifacts/p0/domestic_pilot_20260922/collect_remaining/manifest.csv --candidates artifacts/p0/domestic_pilot_20260922/article_candidates.csv --output-dir artifacts/p0/domestic_pilot_20260922/body_audit_NEW
```

출력 디렉터리는 존재하지 않는 새 경로여야 한다. 수집·실패·이전 실행 기록을 덮어쓰지 않는다.

- 후보/시도 39개를 보존했다. 저장 본문 22개(ETNEWS 10, ZDNET_KR 9, EDAILY 3)를 로컬 재추출했고 본문 없는 17개도 사유와 함께 유지했다.
- 3개 매체에서 실제 저장 HTML의 DOM 구조를 확인했다. ET/ZD의 `#articleBody`, ED의 `.news_body[itemprop=articleBody]`를 사용했다. 본문 속 광고·관련기사 위젯은 제외 사유와 위치를 기록한다. 제외된 요소의 tail은 이어지는 기사일 수 있으므로 유지한다.
- DOM `text()[n]`/tail 원자별 원본 XPath 재조회, 조립 본문 offset 대응, 삽입 줄바꿈 구간을 검사했다. 22/22건의 위치·offset 무결성이 통과했고 선택 DOM 문자 회계 차이는 없었다. 이는 본문 의미적 완전성이나 recall 100%를 뜻하지 않는다.
- 규칙 문장 후보 448개와 인용·숫자·단위·기간·회사 등 span 후보 1,233개를 만들었다. 저장 파일을 재읽은 codepoint roundtrip도 통과했다. 문장 규칙은 약어·인용·줄바꿈 경계에서 오분할할 수 있고 형태소 분석·lemma·gold는 만들지 않았다.
- UTF-8 인식 22개, 대체문자 U+FFFD 0개, 본문 한글 음절 수 최솟값 98, 제목과 검색 제목의 문자 유사도 최솟값 약 0.814를 확인했다. 제목 유사도는 식별 보조값이며 동일 기사나 완전성 판정 기준이 아니다.
- 게시·수정 날짜를 따로 수집했다. 표시 정밀도만 다른 날짜는 공통 정밀도로 비교하며, 양쪽에 명시된 시간대가 있을 때만 UTC로 비교한다. 시간대 없는 값에 시간대를 부여하지 않았다. 게시 날짜 22개가 공통 정밀도에서 양립했고 실제 충돌 후보는 0개다. 수정 날짜 후보가 있는 본문은 12개다. ET의 별도 지면 날짜처럼 역할을 확정하지 않은 날짜는 `unknown`을 유지한다.
- ZDNET_KR `CAND-d6ef03257775547f`는 조립 본문 346자로 `short_body_manual_review`다. 짧은 속보인지 누락인지 사람 원문 검토가 필요하다.
- 제목·부제·바이라인·본문·문장·짧은 span 텍스트는 모두 `raw/` 아래에만 썼다. 공개 index에는 텍스트 대신 hash·offset·위치·후보 라벨을 썼고 `git check-ignore`로 비공개 파일 제외를 확인했다.

합성 회귀 점검은 광고 요소 뒤 tail 보존, HTML comment 제외, 이모지의 Unicode codepoint 위치, XPath 왕복, 분/초 정밀도 비교, 명시 시간대의 동일 순간, 실제 분·날짜 차이 보존을 확인했다.

`body_audit_001`은 HTML comment 처리 예외가 남은 최초 실행이다. 이를 보존하고 수정한 `002`는 22개 본문을 처리했으나 시간 표기 정밀도 차이를 날짜 충돌로 과잉 표시했다. 수정한 `003`을 최종 사용한다. 002와 003의 22개 본문 hash·문장/규칙 span 결과는 같다.

**사람 감사 통과 0개, 완전 본문 최종 검증 0개, 독립 원저작 검증 0개, 주장 매칭 검증 0개다.** 회사·기자·인용 화자와 기사 장르/기원은 확정하지 않았다. 출처 권리 `unresolved`와 사용자의 연구 실행 지시는 별도 상태이며 이 도구는 권리를 판정하거나 승인하지 않는다. 온톨로지 작업은 하지 않았다.
