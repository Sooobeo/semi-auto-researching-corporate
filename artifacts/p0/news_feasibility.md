# P01 뉴스 접근성 시험

P01에서 뉴스가 필요하다. 공시·IR은 공식 수치와 분기 기준을 제공하지만, 사건의 최초 발표, 재보도, 후속 실행과 외부 해석을 비교하려면 기사·공식 발표의 발견 경로와 시점을 시험해야 한다. 기본 공시/IR 40건과 별도 분모로 기록한다.

- 삼성 공식 Newsroom HTML 2건(2024Q1 HBM3E 개발, 2026Q1 HBM4 양산·출하)을 HTTP 200으로 저장하고 본문 문단을 추출했다. 2026Q1 발표의 페이지 표기 날짜는 **2026-02-12**로 IR의 2026Q1 결과 발표보다 앞선 별도 공식 발표다. SK 공식 Newsroom 실적 HTML 2건은 기존 보조 문서와 연결했다. [news_manifest.csv](news_manifest.csv), [news_source_trials.csv](news_source_trials.csv).
- GDELT DOC API는 2024Q1의 `Samsung Electronics HBM` 검색에서 URL·제목·seen-date 후보 10건을 반환했다. 이후 2025Q4 요청과 재시도는 HTTP 429였다. 따라서 역사 기간 검색이 가능한 것은 확인했으나 **2024Q1~2026Q2 전체 뉴스 커버리지는 아직 확보하지 못했다**. `seendate`는 GDELT가 본 시점으로, 언론사 게시 시각을 대신하지 않는다.
- NAVER 뉴스 검색 API는 원문 URL·제목·패시지·`pubDate`를 제공하지만 클라이언트 ID/시크릿이 필요하다. 현재 `.env`에는 해당 자격증명이 없어 실호출을 하지 않았다. 안내문상 `pubDate`도 네이버 제공 시각일 수 있어 원 언론사 시각과 분리해야 한다.
- SK 2026Q1 공식 Newsroom 페이지의 게시일 표기는 **2026-04-22**, 본문 `Seoul, ...` 발표일은 **2026-04-23**이다. 두 날짜를 원문 근거와 함께 분리하고 정확한 게시 시각은 미상으로 둔다.
- GDELT의 **GKG BigQuery 공개 테이블**은 DOC의 소량 기사 목록과 달리 기간 파티션을 제한한 SQL로 과거 기사 URL·조직·제목 메타데이터를 묶어 조회하는 후보이다. 현재 Google Cloud 프로젝트/BigQuery 접속을 설정하지 않아 실쿼리·처리 비용은 확인하지 않았다. 이 경로 역시 언론사 원문 본문 API가 아니다.

다음 수집 단위는 두 기업·2024Q1~2026Q2를 월별로 나눈 검색 창, 제품/사건 키워드, 출처 도메인이다. 후보 URL을 정규화하고 공식 발표·번역·재보도·후속 기사를 다른 문서이자 연결된 사건으로 기록한다. 매체 기사 본문은 사이트별 접근·이용조건을 확인한 뒤 저장하고, GDELT 데이터 이용허락을 원 언론사 기사 본문의 이용허락으로 간주하지 않는다. API 제한으로 잘린 창은 미완료로 남긴다.

## 본문 추출 시범

공식 발행사 HTML의 본문 위치·표·날짜 충돌을 확인한 결과는 [news_body_manifest.csv](news_body_manifest.csv)에, 대량 수집 방식은 [news_body_crawl_plan.md](news_body_crawl_plan.md)에 기록했다. 재실행 순서는 `p01_news_probe.py` → `p01_news_body_crawl.py` → `p01_verify_news_body.py`이다.
