"""Fetch Samsung quarterly Korean IR PDFs for 2024Q1–2026Q2."""

import csv
import io
from datetime import datetime, timezone

import fitz

from p01_collect import OUT, QUARTERS, request, store_raw


def read_csv(name):
    with (OUT / name).open(encoding='utf-8-sig', newline='') as handle:
        return list(csv.DictReader(handle))


def write_csv(name, rows, fields):
    with (OUT / name).open('w', encoding='utf-8-sig', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)


def main():
    manifest = read_csv('document_manifest.csv')
    trials = read_csv('access_trials.csv')
    existing = {row['doc_id'] for row in manifest}
    observed = datetime.now(timezone.utc).isoformat(timespec='seconds')
    successes = failures = 0
    for year, quarter in QUARTERS:
        doc_id = f'SAM-{year}Q{quarter}-IR'
        if doc_id in existing:
            continue
        url = f'https://images.samsung.com/kdp/ir/events/{year}/{year}_{quarter}Q_conference_kor.pdf'
        try:
            data, mime, http = request(url)
            if http != 200 or data[:4] != b'%PDF':
                raise RuntimeError(f'HTTP={http}; MIME={mime}; PDF signature failed')
            pdf = fitz.open(stream=data, filetype='pdf')
            first = pdf[0].get_text().replace(' ', '').replace('\n', '')
            if str(year) not in first or f'{quarter}분기' not in first:
                raise RuntimeError(f'Cover title does not match {year}Q{quarter}')
            page_count = len(pdf)
            pdf.close()
            meta = store_raw(doc_id, 'pdf', data)
            start_month = (quarter - 1) * 3 + 1
            end_month = quarter * 3
            end_day = '31' if quarter in (1, 4) else '30'
            manifest.append({'doc_id': doc_id, 'revision_id': meta['sha256'][:16],
                             'source_id': 'SAMSUNG_IR', 'source_url': url,
                             'title': f'삼성전자 {year}Q{quarter} 경영설명회 (국문)',
                             'company_ids': 'SAM',
                             'reference_period_start': f'{year}-{start_month:02d}-01',
                             'reference_period_end': f'{year}-{end_month:02d}-{end_day}',
                             'published_date': '', 'time_precision': 'unknown',
                             'observed_at': observed, 'format': 'pdf',
                             'parse_status': 'not_tested', **meta})
            trials.append({'doc_id': doc_id, 'source_id': 'SAMSUNG_IR', 'source_url': url,
                           'status': 'downloaded', 'reason': f'HTTP={http}; PDF pages={page_count}; cover matched',
                           'observed_at': observed})
            successes += 1
            existing.add(doc_id)
        except RuntimeError as exc:
            trials.append({'doc_id': doc_id, 'source_id': 'SAMSUNG_IR', 'source_url': url,
                           'status': 'failed', 'reason': str(exc), 'observed_at': observed})
            failures += 1
    write_csv('document_manifest.csv', manifest,
              ['doc_id', 'revision_id', 'source_id', 'source_url', 'title', 'company_ids',
               'reference_period_start', 'reference_period_end', 'published_date', 'time_precision',
               'observed_at', 'format', 'storage_uri', 'byte_size', 'sha256', 'parse_status'])
    write_csv('access_trials.csv', trials,
              ['doc_id', 'source_id', 'source_url', 'status', 'reason', 'observed_at'])
    print('New Samsung IR PDFs downloaded:', successes, 'failed:', failures)


if __name__ == '__main__':
    main()
