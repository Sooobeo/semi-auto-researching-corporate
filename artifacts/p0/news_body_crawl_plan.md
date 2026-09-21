# P01 뉴스 본문 수집 방식

> 2026-09-20 갱신: NAVER 뉴스 검색 API는 현행 약관상 검색 결과·파생물 저장과 AI 입력·학습·평가가 금지되고 전체 본문도 제공하지 않으므로 P01 문체 코퍼스 경로에서 제외한다. 국내 언론 본문 소스와 표본 설계는 [국내 뉴스 문체·표현 청킹 코퍼스 수집 전략](domestic_news_style_corpus_strategy.md)을 따른다.

P01의 뉴스 수집은 **공식 발표에서 사건 정의 → 라이선스 데이터에서 동일 사건 기사 검색 → 본문·표현 단위 검증**으로 나눈다. 뉴스토어 인공지능용 뉴스데이터를 전체 본문 후보로, 빅카인즈를 사건별 기사 모집단과 매체 분포 확인용으로 검토한다. 라이선스 데이터에 없는 매체는 저장·분석 허락이 확인된 경우에만 발행사 URL을 수집한다. 공시·IR 40건의 기간 커버리지와 뉴스의 사건 커버리지는 별도로 집계한다.

## 후보 URL

회사명과 제품·사건명(HBM3E, HBM4, 양산, 공급, 실적 등)을 조합해 회사별·월별 또는 주별 검색 창을 만든다. API 최대 반환 건수에 닿은 창은 더 잘게 나눈다. 발견된 URL은 추적 파라미터를 지우고 정규화해 중복을 줄인다. 검색 API의 `seendate`/`pubDate`는 검색 서비스가 본 시점 또는 제공 시점이므로, 발행사 페이지의 게시일과 별도 필드에 둔다. 최초 보도, 후속 보도, 정정 기사는 본문과 날짜를 확인한 뒤 사건 관계로 연결한다.

## 발행사 페이지 수집

도메인별 작업 대기열을 만들고 먼저 `robots.txt`와 사이트 이용 조건을 확인한다. 도메인당 동시 요청 1개와 최소 간격을 적용하고, 429 응답이나 `Retry-After`가 나오면 해당 도메인 작업을 뒤로 미룬다. 응답이 HTML인지 확인하고 최종 URL, HTTP 상태, 수집 시각, 원본 파일 SHA-256을 기록한다. 원본 HTML 캐시를 재사용하고 실패 URL은 이유와 함께 대기열에 남긴다. 403, 유료벽, robots 차단은 우회하지 않고 접근 실패로 남긴다.

정적 HTML 요청으로 시작한다. 자바스크립트 실행 후에만 본문이 나타나는 도메인에 한해 Playwright를 별도 경로로 적용한다. 많은 URL을 반복 수집할 때는 현재 순차 실행기를 Scrapy 작업 대기열로 옮겨 AutoThrottle과 중단 후 재개 기능을 사용한다. 발행사별 속도·실패율을 먼저 살핀 뒤 전체 동시성을 조절한다.

## 본문 추출과 품질 판정

반복해서 등장하는 발행사는 본문 컨테이너 XPath 프로필을 만든다. 프로필에서 문단·소제목·표 셀을 블록으로 내보내고 각 블록에 원본 DOM XPath를 저장한다. 처음 보는 발행사는 Trafilatura로 본문을 추출하되, 원본 위치가 확인되지 않은 결과는 `text_only_unlocated`로 표시해 검토 전 근거 블록으로 쓰지 않는다. 제목, 게시일, 기사 내 dateline, 검색 서비스 날짜를 분리하고 충돌을 검토한다. 본문 길이, 광고·추천 기사 혼입, 프로필 DOM 대비 문자 커버리지, 블록의 원본 XPath 재조회로 품질을 판정한다. 발행사별 본문 저장·공유 조건을 출처 등록부에 기록한다.

## 이번 시범 결과

[news_body_manifest.csv](news_body_manifest.csv)의 공식 기사/발표 HTML 4건에서 본문 블록 186개와 표 셀 85개를 원본 XPath로 확인했다. 3건은 자동 통과했고 SK하이닉스 2026Q1 발표 1건은 페이지 게시일 **2026-04-22**와 본문 dateline **2026-04-23**이 달라 날짜 검토 대상으로 남겼다. 이 결과는 공식 발행사 2개 도메인의 시범이며, 언론사 전체 기사 수집 성공이나 전체 기간 뉴스 커버리지를 뜻하지 않는다. 언론사에는 일반 추출기가 통하는 정적 페이지도 있지만, robots 차단 페이지와 본문 접근 제한 페이지도 있어 도메인별 시험이 필요하다.

시범 재실행:

```powershell
python -m pip install -r requirements-news.txt
python scripts/p01_news_body_crawl.py --input artifacts/p0/news_manifest.csv
python scripts/p01_verify_news_body.py
```

입력 CSV에는 최소한 `doc_id`, `source_url`을 둔다. 추가 기사는 발견한 발행사 URL을 후보 CSV에 넣는다. 별도 시범의 출력이 위 공식 4건 결과를 덮어쓰지 않도록 `--output-manifest`와 `--output-blocks`로 경로를 지정한다. 수집 결과에서 `body_extracted_unlocated`, `needs_date_review`, `not_extracted`는 검토 대기열로 보낸다.

기술 근거: [NAVER 뉴스 검색 API](https://developers.naver.com/docs/serviceapi/search/news/news.md), [GDELT DOC API](https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/), [Trafilatura Python 사용법](https://trafilatura.readthedocs.io/en/latest/usage-python.html), [Robots Exclusion Protocol](https://www.rfc-editor.org/info/rfc9309), [Scrapy AutoThrottle](https://docs.scrapy.org/en/latest/topics/autothrottle.html), [Scrapy 작업 재개](https://docs.scrapy.org/en/latest/topics/jobs.html).
