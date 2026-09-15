"""Collect P01 filing inventory and six-document access trial.

Uses only Python standard library plus PyMuPDF when installed. Authenticated
request URLs and the API key are never stored or printed.
"""

import csv
import hashlib
import io
import json
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / '.env'
OUT = ROOT / 'artifacts' / 'p0'
RAW = OUT / 'raw'
QUARTERS = [(year, quarter) for year in (2024, 2025, 2026) for quarter in range(1, 5)
            if (year, quarter) <= (2026, 2)]
MONTH = {1: '03', 2: '06', 3: '09', 4: '12'}
REPORT = {1: '분기보고서', 2: '반기보고서', 3: '분기보고서', 4: '사업보고서'}
COMPANIES = [('SAM', '삼성전자', 'P01_SAMSUNG_STOCK_CODE'),
             ('SKH', 'SK하이닉스', 'P01_SKHYNIX_STOCK_CODE')]
IR_TRIALS = {
    'SAM-2025Q4-IR': ('SAM', '2025Q4', '삼성전자 2025Q4 실적발표 IR',
                      'https://images.samsung.com/kdp/ir/events/2025/2025_4Q_conference_kor.pdf', 'pdf'),
    'SAM-2026Q1-IR': ('SAM', '2026Q1', '삼성전자 2026Q1 실적발표 IR',
                      'https://images.samsung.com/kdp/ir/events/2026/2026_1Q_conference_kor.pdf', 'pdf'),
    'SKH-2025Q4-IR-ALT': ('SKH', '2025Q4', 'SK하이닉스 FY2025 공식 실적발표 HTML (IR 대체 후보)',
                          'https://news.skhynix.com/en/sk-hynix-announces-fy25-financial-results/', 'html'),
    'SKH-2026Q1-IR-ALT': ('SKH', '2026Q1', 'SK하이닉스 2026Q1 공식 실적발표 HTML (IR 대체 후보)',
                          'https://news.skhynix.com/en/q1-2026-business-results/', 'html'),
}


def env_values():
    result = {}
    for line in ENV.read_text(encoding='utf-8').splitlines():
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            result[k] = v.strip()
    return result


def request(url, params=None):
    if params:
        url = url + '?' + urllib.parse.urlencode(params)
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'P01-research/0.1'}), timeout=40) as response:
            return response.read(), response.headers.get('Content-Type', ''), response.status
    except Exception as exc:
        # Exception strings from urllib can contain the authenticated URL.
        raise RuntimeError(type(exc).__name__) from None


def dart(env, endpoint, params):
    payload, mime, status = request(env['OPENDART_BASE_URL'].rstrip('/') + '/' + endpoint,
                                    {'crtfc_key': env['OPENDART_API_KEY'], **params})
    if payload[:2] != b'PK':
        try:
            obj = json.loads(payload)
        except ValueError:
            raise RuntimeError(f'Unexpected OpenDART response: {endpoint}, HTTP {status}') from None
        if obj.get('status') not in ('000', '013'):
            raise RuntimeError(f"OpenDART {endpoint}: {obj.get('status')} {obj.get('message')}")
        return obj
    if not zipfile.is_zipfile(io.BytesIO(payload)):
        raise RuntimeError(f'Invalid ZIP response: {endpoint}')
    return payload


def write_csv(name, rows, fields):
    with (OUT / name).open('w', newline='', encoding='utf-8-sig') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)


def corp_codes(env):
    data = dart(env, 'corpCode.xml', {})
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        root = ET.fromstring(archive.read('CORPCODE.xml'))
    by_stock = {row.findtext('stock_code'): row for row in root.findall('list')}
    results = {}
    entity_rows = []
    for cid, name, stock_var in COMPANIES:
        stock = env[stock_var]
        row = by_stock.get(stock)
        if row is None:
            raise RuntimeError(f'{cid} stock code not found in official corpCode.xml')
        code = row.findtext('corp_code')
        results[cid] = code
        entity_rows.append({'company_id': cid, 'legal_name': row.findtext('corp_name'),
                            'corp_code': code, 'ticker': stock,
                            'corp_eng_name': row.findtext('corp_eng_name'),
                            'official_modify_date': row.findtext('modify_date'),
                            'evidence': 'OpenDART corpCode.xml', 'scope_id':
                            'SAM:memory/DS/company' if cid == 'SAM' else 'SKH:product/company'})
    write_csv('entities.csv', entity_rows, list(entity_rows[0]))
    return results


def filings(env, codes):
    rows = []
    for cid, code in codes.items():
        page = 1
        while True:
            result = dart(env, 'list.json', {'corp_code': code,
                        'bgn_de': env['P01_RECEIPT_START_DATE'],
                        'end_de': env['P01_RECEIPT_END_DATE'],
                        'last_reprt_at': 'N', 'pblntf_ty': 'A',
                        'page_count': '100', 'page_no': str(page)})
            if result.get('status') == '013':
                break
            for item in result.get('list', []):
                rows.append({'company_id': cid, 'corp_code': code, **item})
            if page >= int(result.get('total_page', 1)):
                break
            page += 1
    write_csv('dart_filings.csv', rows, ['company_id', 'corp_code', 'corp_name', 'stock_code',
              'report_nm', 'rcept_no', 'flr_nm', 'rcept_dt', 'rm', 'corp_cls'])
    return rows


def matching_filings(rows, cid, year, quarter):
    suffix = f'({year}.{MONTH[quarter]})'
    return sorted((row for row in rows if row['company_id'] == cid and
                   REPORT[quarter] in row['report_nm'] and suffix in row['report_nm']),
                  key=lambda row: (row['rcept_dt'], row['rcept_no']))


def store_raw(doc_id, suffix, data):
    RAW.mkdir(parents=True, exist_ok=True)
    path = RAW / f'{doc_id}.{suffix}'
    path.write_bytes(data)
    return {'storage_uri': str(path.relative_to(ROOT)).replace('\\', '/'),
            'byte_size': len(data), 'sha256': hashlib.sha256(data).hexdigest()}


def main():
    env = env_values()
    if not env.get('OPENDART_API_KEY'):
        raise RuntimeError('OPENDART_API_KEY is missing from .env')
    OUT.mkdir(parents=True, exist_ok=True)
    observed = datetime.now(timezone.utc).isoformat(timespec='seconds')
    codes = corp_codes(env)
    all_filings = filings(env, codes)
    coverage = []
    for cid, _, _ in COMPANIES:
        for year, quarter in QUARTERS:
            matches = matching_filings(all_filings, cid, year, quarter)
            coverage.append({'company_id': cid, 'quarter': f'{year}Q{quarter}',
                             'report_type': REPORT[quarter], 'report_period': f'{year}.{MONTH[quarter]}',
                             'dart_match_count': len(matches),
                             'dart_latest_rcept_no': matches[-1]['rcept_no'] if matches else '',
                             'dart_status': 'listed' if matches else 'not_found',
                             'ir_status': 'initial_trial' if year == 2025 and quarter == 4 or year == 2026 and quarter == 1 else 'not_tested'})
    write_csv('coverage_matrix.csv', coverage, list(coverage[0]))

    trials = []
    manifest = []
    for cid in ('SAM', 'SKH'):
        matches = matching_filings(all_filings, cid, 2025, 4)
        doc_id = f'{cid}-2025-FY-DART'
        if not matches:
            trials.append({'doc_id': doc_id, 'source_id': 'DART', 'status': 'not_found',
                           'reason': 'No 2025.12 사업보고서 in list.json'})
            continue
        item = matches[-1]
        viewer = f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={item['rcept_no']}"
        try:
            data = dart(env, 'document.xml', {'rcept_no': item['rcept_no']})
            if not isinstance(data, bytes):
                raise RuntimeError(f"OpenDART returned {data.get('status')}")
            meta = store_raw(doc_id, 'zip', data)
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                names = archive.namelist()
            status, reason = 'downloaded', f'ZIP entries={len(names)}'
            manifest.append({'doc_id': doc_id, 'revision_id': item['rcept_no'], 'source_id': 'DART',
                             'source_url': viewer, 'title': item['report_nm'], 'company_ids': cid,
                             'reference_period_start': '2025-01-01', 'reference_period_end': '2025-12-31',
                             'published_date': item['rcept_dt'], 'time_precision': 'date',
                             'observed_at': observed, 'format': 'zip/xml', 'parse_status': 'not_tested', **meta})
        except RuntimeError as exc:
            status, reason = 'failed', str(exc)
        trials.append({'doc_id': doc_id, 'source_id': 'DART', 'source_url': viewer,
                       'status': status, 'reason': reason, 'observed_at': observed})

    for doc_id, (cid, quarter, title, url, fmt) in IR_TRIALS.items():
        try:
            data, mime, http = request(url)
            signature_ok = data[:4] == b'%PDF' if fmt == 'pdf' else b'<html' in data[:300].lower() or b'<!doctype' in data[:300].lower()
            if http != 200 or not signature_ok:
                raise RuntimeError(f'HTTP={http}, MIME={mime}, signature_ok={signature_ok}')
            meta = store_raw(doc_id, fmt, data)
            status, reason = 'downloaded', f'HTTP={http}; MIME={mime}; signature_ok=True'
            year, q = map(int, re.match(r'(\d{4})Q(\d)', quarter).groups())
            manifest.append({'doc_id': doc_id, 'revision_id': meta['sha256'][:16],
                             'source_id': 'SAMSUNG_IR' if cid == 'SAM' else 'SKH_NEWSROOM',
                             'source_url': url, 'title': title, 'company_ids': cid,
                             'reference_period_start': f'{year}-{(q-1)*3+1:02d}-01',
                             'reference_period_end': f'{year}-{q*3:02d}-' + ('31' if q in (1, 4) else '30'),
                             'published_date': '', 'time_precision': 'unknown', 'observed_at': observed,
                             'format': fmt, 'parse_status': 'not_tested', **meta})
        except RuntimeError as exc:
            status, reason = 'failed', str(exc)
        trials.append({'doc_id': doc_id, 'source_id': 'SAMSUNG_IR' if cid == 'SAM' else 'SKH_NEWSROOM',
                       'source_url': url, 'status': status, 'reason': reason,
                       'observed_at': observed})
    # The two original SK hynix IR PDFs remain independent from their HTML alternatives.
    for quarter in ('2025Q4', '2026Q1'):
        trials.append({'doc_id': f'SKH-{quarter}-IR', 'source_id': 'SKH_IR',
                       'source_url': 'https://www.skhynix.com/ir/UI-FR-IR06/',
                       'status': 'not_tested', 'reason': 'Dynamic listing; individual file URL unresolved',
                       'observed_at': observed})
    write_csv('access_trials.csv', trials, ['doc_id', 'source_id', 'source_url', 'status', 'reason', 'observed_at'])
    write_csv('document_manifest.csv', manifest,
              ['doc_id', 'revision_id', 'source_id', 'source_url', 'title', 'company_ids',
               'reference_period_start', 'reference_period_end', 'published_date', 'time_precision',
               'observed_at', 'format', 'storage_uri', 'byte_size', 'sha256', 'parse_status'])
    print(json.dumps({'corp_codes': codes, 'regular_filings': len(all_filings),
                      'quarter_slots': len(coverage), 'matched_slots': sum(x['dart_status'] == 'listed' for x in coverage),
                      'downloaded': sum(x['status'] == 'downloaded' for x in trials),
                      'failed': [x['doc_id'] for x in trials if x['status'] == 'failed']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
