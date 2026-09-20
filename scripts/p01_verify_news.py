"""Verify official news pilot metadata, raw files and extracted paragraph paths."""

import csv
import hashlib
import json
import re
from pathlib import Path

from lxml import html


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'artifacts' / 'p0'


def rows(name):
    with (OUT / name).open(encoding='utf-8-sig', newline='') as handle:
        return list(csv.DictReader(handle))


def compact(text):
    return re.sub(r'\s+', ' ', text).strip()


def main():
    manifest = {row['doc_id']: row for row in rows('news_manifest.csv')}
    assert len(manifest) == 4
    assert sum(row['source_id'] == 'SAM_NEWSROOM' for row in manifest.values()) == 2
    for doc_id, row in manifest.items():
        path = ROOT / row['storage_uri']
        data = path.read_bytes()
        assert len(data) == int(row['byte_size']), doc_id
        assert hashlib.sha256(data).hexdigest() == row['sha256'], doc_id
        assert int(row['body_chars']) > 500, doc_id
        if row['source_id'] == 'SAM_NEWSROOM':
            assert row['published_date'] and row['time_precision'] == 'date_only'
        else:
            assert row['published_date'] and row['time_precision'] == 'date_only'
    assert manifest['SAM-2024Q1-NEWS-HBM3E']['published_date'] == '2024-02-27'
    assert manifest['SAM-2026Q1-NEWS-HBM4']['published_date'] == '2026-02-12'
    assert manifest['SKH-2025Q4-IR-ALT']['published_date'] == '2026-01-28'
    assert manifest['SKH-2026Q1-IR-ALT']['published_date'] == '2026-04-22'
    assert manifest['SKH-2026Q1-IR-ALT']['article_dateline_date'] == '2026-04-23'
    seen = set()
    with (OUT / 'news_blocks.jsonl').open(encoding='utf-8') as handle:
        for line in handle:
            block = json.loads(line)
            assert block['doc_id'] in manifest and manifest[block['doc_id']]['source_id'] == 'SAM_NEWSROOM'
            assert block['block_id'] not in seen
            seen.add(block['block_id'])
            source = html.fromstring((ROOT / manifest[block['doc_id']]['storage_uri']).read_bytes())
            matches = source.xpath(block['source_xpath'])
            assert len(matches) == 1 and compact(''.join(matches[0].itertext())) == block['raw_text']
    assert len(seen) == 22
    trials = rows('news_source_trials.csv')
    assert len(trials) == 6
    assert any(row['source_id'] == 'GDELT_DOC' and row['http_status'] == '200'
               for row in trials)
    assert any(row['source_id'] == 'GDELT_DOC' and row['http_status'] == '429'
               for row in trials)
    assert all(row['status'] == 'body_read' for row in trials if row['source_id'] in
               ('SAM_NEWSROOM', 'SKH_NEWSROOM'))
    print('Verified 4 official news bodies, 22 Samsung paragraph blocks, GDELT 200/429 trial records')


if __name__ == '__main__':
    main()
