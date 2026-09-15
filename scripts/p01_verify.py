"""Verify P01 file integrity and report/IR coverage without printing secrets."""

import csv
import hashlib
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'artifacts' / 'p0'


def rows(name):
    with (OUT / name).open(encoding='utf-8-sig', newline='') as handle:
        return list(csv.DictReader(handle))


def main():
    manifest = rows('document_manifest.csv')
    coverage = rows('coverage_matrix.csv')
    trials = rows('access_trials.csv')
    parsed = rows('parser_trials.csv')
    ids = [row['doc_id'] for row in manifest]
    assert len(ids) == len(set(ids)), 'Duplicate doc_id in manifest'
    for row in manifest:
        path = ROOT / row['storage_uri']
        assert path.is_file(), f"Missing raw file: {row['doc_id']}"
        data = path.read_bytes()
        assert len(data) == int(row['byte_size']), f"Wrong byte size: {row['doc_id']}"
        assert hashlib.sha256(data).hexdigest() == row['sha256'], f"Wrong SHA-256: {row['doc_id']}"
        assert 'crtfc_key' not in row['source_url'].lower()
        assert 'crtfc_key' not in row['attachment_url'].lower()
    sources = Counter(row['source_id'] for row in manifest)
    assert sources['DART'] == 20 and sources['SAMSUNG_IR'] == 10 and sources['SKH_IR'] == 10
    assert len(coverage) == 20 and all(row['dart_status'] == 'listed' and
                                       row['ir_status'] == 'downloaded' for row in coverage)
    primary_ids = {row['doc_id'] for row in manifest if row['source_id'] != 'SKH_NEWSROOM'}
    assert len(primary_ids) == 40
    assert all(row['status'] == 'downloaded' for row in trials if row['doc_id'] in primary_ids)
    initial = {'SAM-2025-FY-DART', 'SKH-2025-FY-DART',
               'SAM-2025Q4-IR', 'SAM-2026Q1-IR',
               'SKH-2025Q4-IR', 'SKH-2026Q1-IR'}
    assert initial <= {row['doc_id'] for row in parsed}
    # Search only shareable metadata and code, not downloaded raw documents.
    env_key = next(line.split('=', 1)[1] for line in (ROOT / '.env').read_text().splitlines()
                   if line.startswith('OPENDART_API_KEY='))
    if env_key:
        for path in [*OUT.glob('*.csv'), *OUT.glob('*.md'), *ROOT.glob('scripts/*.py')]:
            assert env_key not in path.read_text(encoding='utf-8-sig'), f'Credential found in {path.name}'
    print('Verified: 40 primary files, 2 auxiliary files, 20 quarter slots, 6 initial parser trials; hashes match')


if __name__ == '__main__':
    main()
