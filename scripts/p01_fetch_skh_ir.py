"""Fetch 10 SK hynix IR presentations via the official site board API."""

import csv
import json
import re
from datetime import datetime, timezone

import fitz

from p01_collect import OUT, QUARTERS, request, store_raw


API = 'https://homeapi.skhynix.com/board/list'


def read_csv(name):
    with (OUT / name).open(encoding='utf-8-sig', newline='') as handle:
        return list(csv.DictReader(handle))


def write_csv(name, rows, fields):
    with (OUT / name).open('w', encoding='utf-8-sig', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)


def main():
    data, mime, http = request(API, {'bcode': '105', 'lang': 'ENG', 'page': '1', 'pageSize': '200'})
    if http != 200:
        raise RuntimeError(f'SK hynix board API HTTP={http}')
    board = json.loads(data)
    cdn = board['cdnUrl']
    selected = []
    for year, quarter in QUARTERS:
        pattern = re.compile(rf'FY{year}\s+Q{quarter}\s+Earnings Results')
        candidates = [row for row in board['list'] if pattern.search(row.get('title', ''))]
        if len(candidates) != 1 or not candidates[0].get('fileUrl2'):
            raise RuntimeError(f'SK hynix board API lacks unique FY{year} Q{quarter} PDF')
        selected.append((year, quarter, candidates[0]))
    list_rows = [{'quarter': f'{year}Q{quarter}', 'seq': row['seq'], 'title': row['title'],
                  'event_date_raw': row.get('eventDate', ''), 'display_date_raw': row.get('displayDate', ''),
                  'file_name': row.get('fileName2', ''), 'file_url': cdn + row['fileUrl2'],
                  'api_url': API, 'api_bcode': 105, 'api_lang': 'ENG'}
                 for year, quarter, row in selected]
    write_csv('sk_ir_list.csv', list_rows, list(list_rows[0]))

    manifest = read_csv('document_manifest.csv')
    trials = read_csv('access_trials.csv')
    existing = {row['doc_id'] for row in manifest}
    observed = datetime.now(timezone.utc).isoformat(timespec='seconds')
    successes = failures = 0
    for year, quarter, item in selected:
        doc_id = f'SKH-{year}Q{quarter}-IR'
        if doc_id in existing:
            continue
        url = cdn + item['fileUrl2']
        try:
            pdf_data, pdf_mime, pdf_http = request(url)
            if pdf_http != 200 or pdf_data[:4] != b'%PDF':
                raise RuntimeError(f'HTTP={pdf_http}; MIME={pdf_mime}; PDF signature failed')
            pdf = fitz.open(stream=pdf_data, filetype='pdf')
            cover = pdf[0].get_text()
            if f'FY{year}' not in cover:
                raise RuntimeError(f'PDF cover does not match FY{year}')
            page_count = len(pdf)
            pdf.close()
            meta = store_raw(doc_id, 'pdf', pdf_data)
            start_month, end_month = (quarter - 1) * 3 + 1, quarter * 3
            end_day = '31' if quarter in (1, 4) else '30'
            manifest.append({'doc_id': doc_id, 'revision_id': meta['sha256'][:16],
                             'source_id': 'SKH_IR', 'source_url':
                             'https://www.skhynix.com/ir/UI-FR-IR06/',
                             'title': item['title'], 'company_ids': 'SKH',
                             'reference_period_start': f'{year}-{start_month:02d}-01',
                             'reference_period_end': f'{year}-{end_month:02d}-{end_day}',
                             'published_date': '', 'time_precision': 'unknown',
                             'observed_at': observed, 'format': 'pdf',
                             'parse_status': 'not_tested', **meta})
            successes += 1
            status, reason = 'downloaded', f'API seq={item["seq"]}; HTTP={pdf_http}; PDF pages={page_count}'
            existing.add(doc_id)
        except RuntimeError as exc:
            failures += 1
            status, reason = 'failed', str(exc)
        old = next((row for row in trials if row['doc_id'] == doc_id), None)
        if old is not None:
            old.update({'source_id': 'SKH_IR', 'source_url': url, 'status': status,
                        'reason': reason, 'observed_at': observed})
        else:
            trials.append({'doc_id': doc_id, 'source_id': 'SKH_IR', 'source_url': url,
                           'status': status, 'reason': reason, 'observed_at': observed})
    write_csv('document_manifest.csv', manifest,
              ['doc_id', 'revision_id', 'source_id', 'source_url', 'title', 'company_ids',
               'reference_period_start', 'reference_period_end', 'published_date', 'time_precision',
               'observed_at', 'format', 'storage_uri', 'byte_size', 'sha256', 'parse_status'])
    write_csv('access_trials.csv', trials,
              ['doc_id', 'source_id', 'source_url', 'status', 'reason', 'observed_at'])
    coverage = read_csv('coverage_matrix.csv')
    for row in coverage:
        doc_id = f"{row['company_id']}-{row['quarter']}-IR"
        row['ir_status'] = 'downloaded' if doc_id in existing else 'failed_or_unresolved'
    write_csv('coverage_matrix.csv', coverage, list(coverage[0]))
    print('SK hynix board API records:', len(selected),
          'new PDFs downloaded:', successes, 'failed:', failures)


if __name__ == '__main__':
    main()
