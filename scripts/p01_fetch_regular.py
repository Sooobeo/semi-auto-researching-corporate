"""Fetch all 20 selected regular-report original ZIPs from OpenDART."""

import csv
import io
import zipfile
from datetime import datetime, timezone

from p01_collect import ENV, OUT, ROOT, dart, env_values, store_raw


def read_csv(name):
    with (OUT / name).open(encoding='utf-8-sig', newline='') as handle:
        return list(csv.DictReader(handle))


def write_csv(name, rows, fields):
    with (OUT / name).open('w', encoding='utf-8-sig', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)


def main():
    env = env_values()
    coverage = read_csv('coverage_matrix.csv')
    filings = read_csv('dart_filings.csv')
    manifest = read_csv('document_manifest.csv')
    trials = read_csv('access_trials.csv')
    existing = {row['doc_id'] for row in manifest}
    observed = datetime.now(timezone.utc).isoformat(timespec='seconds')
    successes = failures = 0
    for slot in coverage:
        cid, quarter, receipt = slot['company_id'], slot['quarter'], slot['dart_latest_rcept_no']
        if not receipt:
            continue
        doc_id = f'{cid}-{quarter}-DART'
        if quarter == '2025Q4':
            doc_id = f'{cid}-2025-FY-DART'
        if doc_id in existing:
            continue
        item = next((row for row in filings if row['rcept_no'] == receipt), None)
        if item is None:
            raise RuntimeError(f'{receipt} missing from dart_filings.csv')
        viewer = f'https://dart.fss.or.kr/dsaf001/main.do?rcpNo={receipt}'
        try:
            data = dart(env, 'document.xml', {'rcept_no': receipt})
            if not isinstance(data, bytes):
                raise RuntimeError(f"OpenDART status={data.get('status')}")
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                entries = archive.namelist()
                if not entries:
                    raise RuntimeError('Empty document ZIP')
            meta = store_raw(doc_id, 'zip', data)
            year = int(quarter[:4])
            month = {'Q1': '03-31', 'Q2': '06-30', 'Q3': '09-30', 'Q4': '12-31'}[quarter[4:]]
            manifest.append({'doc_id': doc_id, 'revision_id': receipt, 'source_id': 'DART',
                             'source_url': viewer, 'title': item['report_nm'], 'company_ids': cid,
                             'reference_period_start': f'{year}-01-01',
                             'reference_period_end': f'{year}-{month}',
                             'published_date': item['rcept_dt'], 'time_precision': 'date',
                             'observed_at': observed, 'format': 'zip/xml',
                             'parse_status': 'not_tested', **meta})
            trials.append({'doc_id': doc_id, 'source_id': 'DART', 'source_url': viewer,
                           'status': 'downloaded', 'reason': f'ZIP entries={len(entries)}',
                           'observed_at': observed})
            successes += 1
            existing.add(doc_id)
        except RuntimeError as exc:
            trials.append({'doc_id': doc_id, 'source_id': 'DART', 'source_url': viewer,
                           'status': 'failed', 'reason': str(exc), 'observed_at': observed})
            failures += 1
    write_csv('document_manifest.csv', manifest,
              ['doc_id', 'revision_id', 'source_id', 'source_url', 'title', 'company_ids',
               'reference_period_start', 'reference_period_end', 'published_date', 'time_precision',
               'observed_at', 'format', 'storage_uri', 'byte_size', 'sha256', 'parse_status'])
    write_csv('access_trials.csv', trials,
              ['doc_id', 'source_id', 'source_url', 'status', 'reason', 'observed_at'])
    print('New regular reports downloaded:', successes, 'failed:', failures,
          'manifest rows:', len(manifest))


if __name__ == '__main__':
    main()
