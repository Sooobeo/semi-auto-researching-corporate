"""Check every source-located official-news block against saved HTML."""

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

from lxml import html

from p01_extract_blocks import compact, text_excluding_tables


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'artifacts' / 'p0'


def rows(name):
    with (OUT / name).open(encoding='utf-8-sig', newline='') as handle:
        return list(csv.DictReader(handle))


def main():
    manifest = {row['doc_id']: row for row in rows('news_body_manifest.csv')}
    assert len(manifest) == 4
    sources = {}
    for doc_id, row in manifest.items():
        raw = (ROOT / row['storage_uri']).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == row['sha256']
        assert len(raw) == int(row['byte_size'])
        assert row['location_status'] == 'source_xpath'
        assert row['text_coverage_against_selected_dom'] == '1.0'
        sources[doc_id] = html.fromstring(raw)
    ids = set()
    counts = Counter()
    types = Counter()
    with (OUT / 'news_body_blocks.jsonl').open(encoding='utf-8') as handle:
        for line in handle:
            block = json.loads(line)
            doc_id = block['doc_id']
            assert doc_id in sources
            assert block['revision_id'] == manifest[doc_id]['revision_id']
            assert block['block_id'] not in ids
            for ref in block['header_refs']:
                assert ref in ids, f'Dangling header reference: {ref}'
            assert block['normalized_text'] == compact(block['raw_text'])
            if block['block_type'] in ('paragraph', 'heading', 'table_cell'):
                nodes = sources[doc_id].xpath(block['source_xpath'])
                assert len(nodes) == 1, block['block_id']
                text, _ = text_excluding_tables(nodes[0])
                assert compact(text) == compact(block['raw_text']), block['block_id']
            if block['block_type'] == 'table_cell':
                assert block['table_id'] and block['row_index'] is not None
                assert block['col_index'] is not None
            ids.add(block['block_id'])
            counts[doc_id] += 1
            types[block['block_type']] += 1
    for doc_id, row in manifest.items():
        assert counts[doc_id] == int(row['block_count'])
    assert len(ids) == 186
    assert manifest['SKH-2026Q1-IR-ALT']['quality_status'] == 'needs_date_review'
    assert manifest['SKH-2026Q1-IR-ALT']['publisher_page_date'] == '2026-04-22'
    assert manifest['SKH-2026Q1-IR-ALT']['article_dateline_date'] == '2026-04-23'
    assert sum(int(x['native_tables']) for x in manifest.values()) == 3
    print('Verified 4 official article bodies,', len(ids), 'source-located blocks,',
          types['table_cell'], 'table cells, 1 date conflict')


if __name__ == '__main__':
    main()
