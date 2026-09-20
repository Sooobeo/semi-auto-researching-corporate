"""Fetch candidate article pages and extract source-located body blocks.

Run with the official pilot manifest by default. A CSV with doc_id/source_url
can be supplied for more candidates. Existing raw copies are reused; new URLs
are checked against robots.txt and fetched sequentially with a per-host delay.
Static HTML is used first. Dynamic/paywalled pages are recorded for review,
not bypassed. For unknown layouts Trafilatura provides a text fallback, marked
unlocated so it cannot be silently treated as audited evidence.
"""

import argparse
import csv
import hashlib
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.robotparser import RobotFileParser

import trafilatura
from lxml import html

from p01_extract_blocks import Emitter, emit_dom, compact


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'artifacts' / 'p0'
RAW = OUT / 'news_raw'
USER_AGENT = 'P01ResearchCrawler/0.1 (research; article access probe)'
BODY_SELECTORS = {
    'news.samsung.com': ('//*[contains(concat(" ", normalize-space(@class), " "), " single_contents ")]',
                         'Samsung Newsroom article body'),
    'news.skhynix.com': ('//*[contains(concat(" ", normalize-space(@class), " "), " post-contents ")]',
                           'SK hynix Newsroom article body'),
}


def csv_rows(path):
    with path.open(encoding='utf-8-sig', newline='') as handle:
        return list(csv.DictReader(handle))


def write_csv(path, rows):
    if not rows:
        return
    with path.open('w', encoding='utf-8-sig', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)


def normalized_url(url):
    parsed = urllib.parse.urlsplit(url.strip())
    if parsed.scheme not in ('http', 'https') or not parsed.netloc:
        raise ValueError(f'Not an HTTP article URL: {url[:80]}')
    host = parsed.hostname.lower()
    port = f':{parsed.port}' if parsed.port and parsed.port not in (80, 443) else ''
    path = urllib.parse.quote(urllib.parse.unquote(parsed.path or '/'), safe='/%-._~')
    query = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
    query = [(k, v) for k, v in query if not re.match(r'^(utm_|fbclid$|gclid$|mc_cid$)', k, re.I)]
    return urllib.parse.urlunsplit((parsed.scheme.lower(), host + port, path,
                                   urllib.parse.urlencode(query), ''))


def displayed_date(root, host):
    if host == 'news.samsung.com':
        nodes = root.xpath('//*[contains(concat(" ", normalize-space(@class), " "), " single-date ")]')
    elif host == 'news.skhynix.com':
        nodes = root.xpath('//*[contains(concat(" ", normalize-space(@class), " "), " post-info ")]//*[contains(concat(" ", normalize-space(@class), " "), " date ")]')
    else:
        nodes = []
    source = compact(''.join(nodes[0].itertext())) if nodes else ''
    match = re.search(r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}\b', source)
    if match:
        return datetime.strptime(match.group(), '%B %d, %Y').date().isoformat(), source
    return '', source


def dateline_date(body):
    text = compact(' '.join(body.itertext()))[:500]
    match = re.search(r'\b(?:Seoul|Korea),\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}\b', text)
    if not match:
        return '', ''
    date_phrase = match.group().split(', ', 1)[1]
    return datetime.strptime(date_phrase, '%B %d, %Y').date().isoformat(), match.group()


def robots_decision(url, cache):
    parsed = urllib.parse.urlsplit(url)
    origin = parsed.scheme + '://' + parsed.netloc
    if origin not in cache:
        robots_url = origin + '/robots.txt'
        try:
            response = urllib.request.urlopen(urllib.request.Request(
                robots_url, headers={'User-Agent': USER_AGENT}), timeout=12)
            status, text = response.status, response.read(256000).decode('utf-8', 'replace')
            response.close()
        except urllib.error.HTTPError as exc:
            status, text = exc.code, ''
        except Exception:
            cache[origin] = (False, 'robots_unavailable')
            return cache[origin]
        if status == 200:
            parser = RobotFileParser()
            parser.parse(text.splitlines())
            cache[origin] = (parser, 'robots_200')
        elif status == 404:
            cache[origin] = (True, 'robots_404')
        else:
            cache[origin] = (False, f'robots_http_{status}')
    policy, note = cache[origin]
    allowed = policy.can_fetch(USER_AGENT, url) if isinstance(policy, RobotFileParser) else policy
    return allowed, note


def fetch_html(url, robots_cache, host_last, delay):
    allowed, robots_note = robots_decision(url, robots_cache)
    if not allowed:
        return None, '', f'robots_blocked_or_unknown:{robots_note}', None
    parsed = urllib.parse.urlsplit(url)
    host = parsed.hostname
    policy = robots_cache[parsed.scheme + '://' + parsed.netloc][0]
    declared_delay = policy.crawl_delay(USER_AGENT) if isinstance(policy, RobotFileParser) else None
    effective_delay = max(delay, declared_delay or 0)
    remaining = effective_delay - (time.monotonic() - host_last.get(host, -1000))
    if remaining > 0:
        time.sleep(remaining)
    host_last[host] = time.monotonic()
    try:
        response = urllib.request.urlopen(urllib.request.Request(
            url, headers={'User-Agent': USER_AGENT, 'Accept': 'text/html,application/xhtml+xml'}),
            timeout=25)
        status = response.status
        mime = response.headers.get('Content-Type', '').split(';')[0].lower()
        data = response.read(5_000_001)
        final_url = response.geturl()
        response.close()
        if len(data) > 5_000_000:
            return None, final_url, 'response_over_5mb', status
        if mime not in ('text/html', 'application/xhtml+xml'):
            return None, final_url, f'wrong_mime:{mime}', status
        return data, final_url, 'downloaded', status
    except urllib.error.HTTPError as exc:
        return None, url, f'http_{exc.code}', exc.code
    except Exception as exc:
        return None, url, f'network_error:{type(exc).__name__}', None


def extraction(record, raw, final_url, handle):
    root = html.fromstring(raw)
    host = urllib.parse.urlsplit(final_url).hostname.lower()
    profile = BODY_SELECTORS.get(host)
    selected = root.xpath(profile[0]) if profile else []
    generic_json = trafilatura.extract(raw, output_format='json', with_metadata=True,
                                        include_comments=False, include_tables=True)
    generic = json.loads(generic_json) if generic_json else {}
    headings = root.xpath('//h1')
    title = (compact(''.join(headings[0].itertext())) if headings else
             compact(generic.get('title') or record.get('title') or ''))
    if not title:
        title = compact(record.get('title') or '')
    page_date, page_evidence = displayed_date(root, host)
    if selected:
        body = selected[0]
        dateline, dateline_evidence = dateline_date(body)
        doc = dict(record)
        doc['revision_id'] = hashlib.sha256(raw).hexdigest()[:16]
        emitter = Emitter(handle, doc, Path(urllib.parse.urlsplit(final_url).path).name or 'index.html')
        source_chars, emitted_chars, tables = emit_dom(body, emitter, 'news_profile_dom')
        body_text = compact(''.join(body.itertext()))
        method = profile[1]
        location_status = 'source_xpath'
        block_count = sum(emitter.counts.values())
        table_count = len(tables)
        coverage = emitted_chars / source_chars if source_chars else 0
    else:
        dateline = dateline_evidence = ''
        body_text = compact(generic.get('text') or '')
        doc = dict(record)
        doc['revision_id'] = hashlib.sha256(raw).hexdigest()[:16]
        emitter = Emitter(handle, doc, Path(urllib.parse.urlsplit(final_url).path).name or 'index.html')
        if body_text:
            emitter.emit('article_text', body_text, extraction_method='trafilatura_json',
                         source_xpath=None, source_entry=final_url,
                         location_status='text_only_unlocated')
        method = 'trafilatura_json'
        location_status = 'text_only_unlocated'
        block_count = sum(emitter.counts.values())
        table_count = 0
        coverage = None
    date_conflict = bool(page_date and dateline and page_date != dateline)
    published_date = page_date or generic.get('date') or ''
    quality = ('body_extracted_located' if location_status == 'source_xpath'
               and len(body_text) >= 400 and block_count >= 2 and not date_conflict else
               'needs_date_review' if date_conflict else
               'body_extracted_unlocated' if len(body_text) >= 400 else 'body_missing_or_short')
    return {'title': title, 'publisher_page_date': page_date, 'publisher_date_evidence': page_evidence,
            'article_dateline_date': dateline, 'dateline_evidence': dateline_evidence,
            'trafilatura_date': generic.get('date') or '',
            'published_date': published_date, 'time_precision': 'date_only' if published_date else 'unknown',
            'date_conflict': date_conflict, 'body_chars': len(body_text),
            'block_count': block_count, 'native_tables': table_count,
            'text_coverage_against_selected_dom': round(coverage, 5) if coverage is not None else '',
            'extraction_method': method, 'location_status': location_status,
            'quality_status': quality}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', default=str(OUT / 'news_manifest.csv'))
    parser.add_argument('--output-manifest', default=str(OUT / 'news_body_manifest.csv'))
    parser.add_argument('--output-blocks', default=str(OUT / 'news_body_blocks.jsonl'))
    parser.add_argument('--delay', type=float, default=2.0,
                        help='Minimum seconds between requests to the same host')
    args = parser.parse_args()
    if args.delay < 0:
        parser.error('--delay must be nonnegative')
    candidates = csv_rows(Path(args.input))
    assert candidates, 'No candidate URLs'
    RAW.mkdir(parents=True, exist_ok=True)
    seen_urls = set()
    seen_doc_ids = set()
    rows = []
    robots_cache = {}
    host_last = {}
    manifest_path = Path(args.output_manifest)
    block_path = Path(args.output_blocks)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    block_path.parent.mkdir(parents=True, exist_ok=True)
    with block_path.open('w', encoding='utf-8', newline='\n') as handle:
        for candidate in candidates:
            candidate_url = candidate.get('source_url', '')
            try:
                url = normalized_url(candidate_url)
            except ValueError:
                url = ''
            doc_id = candidate.get('doc_id') or 'NEWS-' + hashlib.sha256(candidate_url.encode()).hexdigest()[:16]
            base = {'doc_id': doc_id, 'company_id': candidate.get('company_id', ''),
                    'source_id': candidate.get('source_id', ''),
                    'candidate_url': candidate_url, 'normalized_url': url,
                    'observed_at': datetime.now(timezone.utc).isoformat(timespec='seconds'),
                    'revision_id': '', 'final_url': '', 'http_status': '', 'storage_uri': '',
            'byte_size': '', 'sha256': '', 'title': '', 'publisher_page_date': '',
                    'publisher_date_evidence': '', 'article_dateline_date': '',
                    'dateline_evidence': '', 'trafilatura_date': '', 'published_date': '',
                    'time_precision': 'unknown', 'date_conflict': '', 'body_chars': '',
                    'block_count': '', 'native_tables': '',
                    'text_coverage_against_selected_dom': '', 'extraction_method': '',
                    'location_status': '', 'quality_status': '', 'fetch_status': ''}
            if not url:
                base.update({'quality_status': 'not_extracted', 'fetch_status': 'invalid_candidate_url'})
                rows.append(base)
                continue
            if doc_id in seen_doc_ids:
                base.update({'quality_status': 'not_extracted',
                             'fetch_status': 'duplicate_candidate_doc_id'})
                rows.append(base)
                continue
            seen_doc_ids.add(doc_id)
            if url in seen_urls:
                base['fetch_status'] = 'duplicate_candidate_url'
                rows.append(base)
                continue
            seen_urls.add(url)
            cached = candidate.get('storage_uri', '')
            cached_path = ROOT / cached if cached else None
            if cached_path and cached_path.is_file():
                raw = cached_path.read_bytes()
                final_url, fetch_status, http_status = url, 'reused_existing_raw', ''
                raw_path = cached_path
            else:
                raw, final_url, fetch_status, http_status = fetch_html(url, robots_cache, host_last, args.delay)
                if raw is None:
                    base.update({'final_url': final_url, 'http_status': http_status or '',
                                 'fetch_status': fetch_status, 'quality_status': 'not_extracted'})
                    rows.append(base)
                    continue
                digest = hashlib.sha256(raw).hexdigest()
                raw_path = RAW / f'{doc_id}-{digest[:16]}.html'
                raw_path.write_bytes(raw)
            digest = hashlib.sha256(raw).hexdigest()
            base.update({'revision_id': digest[:16], 'final_url': final_url,
                         'http_status': http_status or '',
                         'storage_uri': str(raw_path.relative_to(ROOT)).replace('\\', '/'),
                         'byte_size': len(raw), 'sha256': digest,
                         'fetch_status': fetch_status})
            try:
                result = extraction({**candidate, 'doc_id': doc_id}, raw, final_url, handle)
                base.update(result)
            except Exception as exc:
                base['quality_status'] = 'extraction_error:' + type(exc).__name__
            rows.append(base)
            print(doc_id, base['quality_status'], 'chars', base['body_chars'],
                  'blocks', base['block_count'], flush=True)
    write_csv(manifest_path, rows)
    print('Body crawl:', len(rows), 'candidate rows;', Counter(r['quality_status'] for r in rows))


if __name__ == '__main__':
    main()
