"""P01 news feasibility: official article bodies and media-discovery API trials.

This is a scoped access pilot, not a claim that all relevant publisher articles
have been discovered or that third-party full text can be redistributed.
"""

import csv
import hashlib
import json
import re
import urllib.request
from datetime import date
from pathlib import Path

from lxml import html


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'artifacts' / 'p0'
RAW = OUT / 'news_raw'
SAMSUNG = [
    ('SAM-2024Q1-NEWS-HBM3E', '2024Q1',
     'https://news.samsung.com/global/samsung-develops-industry-first-36gb-hbm3e-12h-dram'),
    ('SAM-2026Q1-NEWS-HBM4', '2026Q1',
     'https://news.samsung.com/global/samsung-ships-industry-first-commercial-hbm4-with-ultimate-performance-for-ai-computing'),
]


def read_csv(name):
    with (OUT / name).open(encoding='utf-8-sig', newline='') as handle:
        return list(csv.DictReader(handle))


def write_csv(name, records, fields):
    with (OUT / name).open('w', encoding='utf-8-sig', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(records)


def compact(value):
    return re.sub(r'\s+', ' ', value).strip()


def english_date(value):
    match = re.search(r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),\s+(\d{4})', value)
    if not match:
        return ''
    from datetime import datetime
    return datetime.strptime(match.group(0), '%B %d, %Y').date().isoformat()


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    manifest = []
    blocks = []
    trials = []
    for doc_id, quarter, url in SAMSUNG:
        response = urllib.request.urlopen(urllib.request.Request(
            url, headers={'User-Agent': 'Mozilla/5.0 P01 news feasibility'}), timeout=30)
        payload = response.read()
        source = html.fromstring(payload)
        title = compact(''.join(source.xpath('//h1[contains(@class,"single-title")]')[0].itertext()))
        date_text = compact(''.join(source.xpath('//*[contains(@class,"single-date")]')[0].itertext()))
        body = source.xpath('//*[contains(@class,"single_contents")]')[0]
        paragraphs = [node for node in body.xpath('.//p|.//h2|.//h3') if compact(''.join(node.itertext()))]
        assert title and paragraphs and len(compact(''.join(body.itertext()))) > 500
        path = RAW / f'{doc_id}.html'
        path.write_bytes(payload)
        published_date = english_date(date_text)
        if not published_date:
            raise RuntimeError(f'Official displayed date not parsed: {doc_id}')
        manifest.append({'doc_id': doc_id, 'company_id': 'SAM', 'quarter': quarter,
                         'source_id': 'SAM_NEWSROOM', 'source_type': 'official_announcement',
                         'source_url': url, 'title': title,
                         'published_date': published_date, 'published_date_evidence': date_text,
                         'time_precision': 'date_only', 'article_dateline_date': '',
                         'observed_at': date.today().isoformat(),
                         'storage_uri': str(path.relative_to(ROOT)).replace('\\', '/'),
                         'byte_size': len(payload), 'sha256': hashlib.sha256(payload).hexdigest(),
                         'body_chars': len(compact(''.join(body.itertext()))),
                         'access_status': 'body_read', 'reuse_status': 'source_specific_review_needed',
                         'relation_candidate': 'SAM-2026Q1-IR:prior_official_announcement' if quarter == '2026Q1' else ''})
        tree = source.getroottree()
        for index, node in enumerate(paragraphs, 1):
            blocks.append({'block_id': f'{doc_id}:B{index:05d}', 'doc_id': doc_id,
                           'block_type': 'heading' if node.tag in ('h2', 'h3') else 'paragraph',
                           'source_url': url, 'source_xpath': tree.getpath(node),
                           'raw_text': compact(''.join(node.itertext())),
                           'extraction_method': 'lxml_single_contents',
                           'observed_at': date.today().isoformat()})
        trials.append({'source_id': 'SAM_NEWSROOM', 'probe_id': doc_id, 'query_or_url': url,
                       'window': quarter, 'http_status': response.status,
                       'result_count': len(paragraphs), 'result_type': 'article_body_paragraphs',
                       'status': 'body_read', 'limitation': 'date-only publication; reuse rules depend on article/media'})
        response.close()

    base = {row['doc_id']: row for row in read_csv('document_manifest.csv')}
    for doc_id, quarter in [('SKH-2025Q4-IR-ALT', '2025Q4'),
                            ('SKH-2026Q1-IR-ALT', '2026Q1')]:
        row = base[doc_id]
        path = ROOT / row['storage_uri']
        body = html.fromstring(path.read_bytes())
        article = body.xpath('//article') or body.xpath('//main')
        content = article[0] if article else body
        dates = content.xpath('.//*[contains(concat(" ", normalize-space(@class), " "), " post-info ")]//*[contains(concat(" ", normalize-space(@class), " "), " date ")]')
        date_text = compact(''.join(dates[0].itertext())) if dates else ''
        site_date = english_date(date_text)
        dateline = re.search(r'\bSeoul,\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}\b',
                             compact(' '.join(content.itertext()))[:1000])
        dateline_date = english_date(dateline.group()) if dateline else ''
        manifest.append({'doc_id': doc_id, 'company_id': 'SKH', 'quarter': quarter,
                         'source_id': 'SKH_NEWSROOM', 'source_type': 'official_earnings_announcement',
                         'source_url': row['source_url'], 'title': row['title'],
                         'published_date': site_date, 'published_date_evidence': date_text or 'not_verified',
                         'time_precision': 'date_only' if site_date else 'unknown',
                         'article_dateline_date': dateline_date,
                         'observed_at': row['observed_at'],
                         'storage_uri': row['storage_uri'], 'byte_size': row['byte_size'],
                         'sha256': row['sha256'], 'body_chars': len(compact(''.join(content.itertext()))),
                         'access_status': 'body_read', 'reuse_status': 'unverified',
                         'relation_candidate': doc_id.replace('-ALT', '') + ':alternate_publication'})
        trials.append({'source_id': 'SKH_NEWSROOM', 'probe_id': doc_id,
                       'query_or_url': row['source_url'], 'window': quarter,
                       'http_status': 200, 'result_count': 1, 'result_type': 'official_HTML_body',
                       'status': 'body_read', 'limitation': 'page date and article dateline differ' if site_date != dateline_date else 'date-only publication'})
    write_csv('news_manifest.csv', manifest, list(manifest[0]))
    with (OUT / 'news_blocks.jsonl').open('w', encoding='utf-8', newline='\n') as handle:
        for block in blocks:
            handle.write(json.dumps(block, ensure_ascii=False, separators=(',', ':')) + '\n')

    # Direct API observations made during this P01 run; keep the 429 visible.
    gdelt_url = 'https://api.gdeltproject.org/api/v2/doc/doc'
    trials.extend([
        {'source_id': 'GDELT_DOC', 'probe_id': 'GDELT-SAM-2024Q1-HBM',
         'query_or_url': gdelt_url + '?query=Samsung+Electronics+HBM&mode=artlist&format=json&startdatetime=20240101000000&enddatetime=20240331235959&maxrecords=10',
         'window': '2024Q1', 'http_status': 200, 'result_count': 10,
         'result_type': 'publisher_URL_title_seen_date_metadata', 'status': 'candidate_discovery_success',
         'limitation': 'result limit 10; seendate is GDELT discovery, not verified publisher publication'},
        {'source_id': 'GDELT_DOC', 'probe_id': 'GDELT-SAM-2025Q4-HBM',
         'query_or_url': gdelt_url + '?query=Samsung+Electronics+HBM&mode=artlist&format=json&startdatetime=20251001000000&enddatetime=20260101000000&maxrecords=250',
         'window': '2025Q4', 'http_status': 429, 'result_count': '',
         'result_type': 'publisher_metadata', 'status': 'rate_limited',
         'limitation': 'stop/retry with backoff; no full-period coverage claim'},
    ])
    write_csv('news_source_trials.csv', trials, list(trials[0]))

    registry = read_csv('source_registry.csv')
    registry = [row for row in registry if row['source_id'] not in ('SAM_NEWSROOM', 'GDELT_DOC', 'NAVER_NEWS')]
    for row in registry:
        if row['source_id'] == 'SKH_NEWSROOM':
            row['status'] = 'adopt_official_news_for_P01_pilot'
            row['automated_access'] = '2_HTML_success'
    fields = list(registry[0])
    registry.extend([
        {'source_id': 'SAM_NEWSROOM', 'provider': 'Samsung Global Newsroom',
         'source_type': 'official_announcement_HTML', 'landing_url': 'https://news.samsung.com/global/',
         'terms_url': 'https://news.samsung.com/kr/%EC%82%BC%EC%84%B1%EC%A0%84%EC%9E%90-%EB%89%B4%EC%8A%A4%EB%A3%B8-%EC%BD%98%ED%85%90%EC%B8%A0-%EC%9D%B4%EC%9A%A9%EC%97%90-%EB%8C%80%ED%95%9C-%EC%95%88%EB%82%B4',
         'checked_at': date.today().isoformat(), 'authentication': 'none_observed',
         'manual_read': 'official_article_pages_read', 'automated_access': '2_HTML_success',
         'storage_policy': 'local pilot copy', 'sharing_policy': 'source_specific_review_needed',
         'redistribution_policy': 'source_specific_review_needed', 'rate_limit_evidence': 'not_tested',
         'status': 'adopt_official_news_for_P01_pilot',
         'unresolved_reason': 'Korean Newsroom guidance has exceptions for externally supplied content/media; Global page terms need separate review'},
        {'source_id': 'GDELT_DOC', 'provider': 'The GDELT Project DOC 2.0',
         'source_type': 'news_candidate_metadata_API', 'landing_url': gdelt_url,
         'terms_url': 'https://gdeltproject.org/about.html',
         'checked_at': date.today().isoformat(), 'authentication': 'none_observed',
         'manual_read': 'official_documentation_read', 'automated_access': 'historical_200_then_429',
         'storage_policy': 'URL/title/seen-date metadata only',
         'sharing_policy': 'GDELT dataset reuse with attribution; publisher article rights separate',
         'redistribution_policy': 'GDELT dataset reuse with attribution; publisher article rights separate',
         'rate_limit_evidence': 'HTTP 429 on repeated DOC requests',
         'status': 'candidate_discovery_probe_only',
         'unresolved_reason': 'No complete 20-quarter coverage; GDELT seen date is not publisher published date'},
        {'source_id': 'NAVER_NEWS', 'provider': 'NAVER Search API News',
         'source_type': 'news_candidate_metadata_API',
         'landing_url': 'https://openapi.naver.com/v1/search/news.json',
         'terms_url': 'https://developers.naver.com/docs/serviceapi/search/news/news.md',
         'checked_at': date.today().isoformat(), 'authentication': 'client ID and secret required',
         'manual_read': 'official_documentation_read', 'automated_access': 'not_tested_no_credentials',
         'storage_policy': 'URL/title/passage/date metadata after credential setup',
         'sharing_policy': 'unverified', 'redistribution_policy': 'publisher article rights separate',
         'rate_limit_evidence': 'official guide: 25,000/day; 100/result page; start <= 1000',
         'status': 'hold_for_credentials',
         'unresolved_reason': 'No NAVER client credentials in .env; pubDate may be NAVER supply date'},
    ])
    write_csv('source_registry.csv', registry, fields)
    scope = (OUT / 'scope.md').read_text(encoding='utf-8')
    if '뉴스 접근성 시험' not in scope:
        scope += '\n뉴스 접근성 시험: P01의 보조 조사 대상으로 삼성·SK 공식 Newsroom 원문 표본과 비공식 기사 후보 발견 API를 포함한다. 기본 공시/IR 40건의 분모에는 합치지 않는다. 전체 기사 본문 대량 수집은 출처별 이용조건·기간 커버리지·중복 규칙을 확인한 뒤 별도 코퍼스로 수행한다. [news_feasibility.md](news_feasibility.md).\n'
        (OUT / 'scope.md').write_text(scope, encoding='utf-8')
    news_report = f'''# P01 뉴스 접근성 시험

P01에서 뉴스가 필요하다. 공시·IR은 공식 수치와 분기 기준을 제공하지만, 사건의 최초 발표, 재보도, 후속 실행과 외부 해석을 비교하려면 기사·공식 발표의 발견 경로와 시점을 시험해야 한다. 기본 공시/IR 40건과 별도 분모로 기록한다.

- 삼성 공식 Newsroom HTML 2건(2024Q1 HBM3E 개발, 2026Q1 HBM4 양산·출하)을 HTTP 200으로 저장하고 본문 문단을 추출했다. 2026Q1 발표의 페이지 표기 날짜는 **2026-02-12**로 IR의 2026Q1 결과 발표보다 앞선 별도 공식 발표다. SK 공식 Newsroom 실적 HTML 2건은 기존 보조 문서와 연결했다. [news_manifest.csv](news_manifest.csv), [news_source_trials.csv](news_source_trials.csv).
- GDELT DOC API는 2024Q1의 `Samsung Electronics HBM` 검색에서 URL·제목·seen-date 후보 10건을 반환했다. 이후 2025Q4 요청과 재시도는 HTTP 429였다. 따라서 역사 기간 검색이 가능한 것은 확인했으나 **2024Q1~2026Q2 전체 뉴스 커버리지는 아직 확보하지 못했다**. `seendate`는 GDELT가 본 시점으로, 언론사 게시 시각을 대신하지 않는다.
- NAVER 뉴스 검색 API는 원문 URL·제목·패시지·`pubDate`를 제공하지만 클라이언트 ID/시크릿이 필요하다. 현재 `.env`에는 해당 자격증명이 없어 실호출을 하지 않았다. 안내문상 `pubDate`도 네이버 제공 시각일 수 있어 원 언론사 시각과 분리해야 한다.
- SK 2026Q1 공식 Newsroom 페이지의 게시일 표기는 **2026-04-22**, 본문 `Seoul, ...` 발표일은 **2026-04-23**이다. 두 날짜를 원문 근거와 함께 분리하고 정확한 게시 시각은 미상으로 둔다.
- GDELT의 **GKG BigQuery 공개 테이블**은 DOC의 소량 기사 목록과 달리 기간 파티션을 제한한 SQL로 과거 기사 URL·조직·제목 메타데이터를 묶어 조회하는 후보이다. 현재 Google Cloud 프로젝트/BigQuery 접속을 설정하지 않아 실쿼리·처리 비용은 확인하지 않았다. 이 경로 역시 언론사 원문 본문 API가 아니다.

다음 수집 단위는 두 기업·2024Q1~2026Q2를 월별로 나눈 검색 창, 제품/사건 키워드, 출처 도메인이다. 후보 URL을 정규화하고 공식 발표·번역·재보도·후속 기사를 다른 문서이자 연결된 사건으로 기록한다. 매체 기사 본문은 사이트별 접근·이용조건을 확인한 뒤 저장하고, GDELT 데이터 이용허락을 원 언론사 기사 본문의 이용허락으로 간주하지 않는다. API 제한으로 잘린 창은 미완료로 남긴다.
'''
    if (OUT / 'news_body_manifest.csv').is_file():
        news_report += ('\n## 본문 추출 시범\n\n'
                        '공식 발행사 HTML의 본문 위치·표·날짜 충돌을 확인한 결과는 '
                        '[news_body_manifest.csv](news_body_manifest.csv)에, 대량 수집 방식은 '
                        '[news_body_crawl_plan.md](news_body_crawl_plan.md)에 기록했다. '
                        '재실행 순서는 `p01_news_probe.py` → `p01_news_body_crawl.py` '
                        '→ `p01_verify_news_body.py`이다.\n')
    (OUT / 'news_feasibility.md').write_text(news_report, encoding='utf-8')
    print('News pilot:', len(manifest), 'official bodies;', len(blocks),
          'Samsung paragraph blocks; GDELT historical 200 then 429')


if __name__ == '__main__':
    main()
