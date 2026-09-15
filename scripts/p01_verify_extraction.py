"""Stream-verify every extracted P01 block and the sampled numeric audit."""

import csv
import json
import re
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'artifacts' / 'p0'


def rows(name):
    with (OUT / name).open(encoding='utf-8-sig', newline='') as handle:
        return list(csv.DictReader(handle))


def main():
    manifest = {row['doc_id']: row for row in rows('document_manifest.csv')}
    expected = {row['doc_id']: row for row in rows('block_counts.csv')}
    tables = {row['table_id'] for row in rows('table_registry.csv')}
    assert len(manifest) == len(expected) == 42
    assert len(tables) == sum(int(row['native_tables']) for row in expected.values())
    counts = Counter()
    per_doc = defaultdict(Counter)
    emitted_chars = Counter()
    block_ids = set()
    with (OUT / 'blocks.jsonl').open(encoding='utf-8') as handle:
        for line_number, line in enumerate(handle, 1):
            block = json.loads(line)
            doc_id = block['doc_id']
            assert doc_id in manifest, f'Unknown doc at line {line_number}'
            assert block['revision_id'] == manifest[doc_id]['revision_id']
            block_id = block['block_id']
            assert block_id not in block_ids, f'Duplicate block ID: {block_id}'
            for ref in block['header_refs']:
                assert ref in block_ids, f'Dangling/forward header ref: {block_id} -> {ref}'
            if block['block_type'] == 'table_cell':
                assert block['table_id'] in tables, f'Unregistered table: {block_id}'
                assert block['row_index'] is not None and block['col_index'] is not None
                assert block['rowspan'] >= 1 and block['colspan'] >= 1
            if block['block_type'] == 'pdf_text_block':
                assert 1 <= block['page_number'] <= int(expected[doc_id]['pdf_pages'])
                assert len(block['bbox']) == 4
            if block['block_type'] in ('paragraph', 'heading', 'table_cell', 'inline_text'):
                assert block['source_xpath'] and block['source_entry']
            assert block['normalized_text'] == re.sub(r'\s+', ' ', block['raw_text']).strip()
            block_ids.add(block_id)
            kind = block['block_type']
            counts[kind] += 1
            per_doc[doc_id][kind] += 1
            emitted_chars[doc_id] += len(re.sub(r'\s+', '', block['raw_text']))
    for doc_id, row in expected.items():
        assert row['status'] == 'extracted_full_text'
        assert emitted_chars[doc_id] == int(row['emitted_nonwhite_chars'])
        assert emitted_chars[doc_id] == int(row['source_nonwhite_chars'])
        assert float(row['text_coverage_ratio']) == 1.0
        assert per_doc[doc_id]['table_cell'] == int(row['table_cells'])
        assert per_doc[doc_id]['image_marker'] == int(row['image_markers'])
        assert per_doc[doc_id]['page_break'] == int(row['page_breaks'])
        assert (per_doc[doc_id]['paragraph'] + per_doc[doc_id]['pdf_text_block']
                == int(row['paragraph_or_text_blocks']))
    audit = rows('extraction_audit.csv')
    reconciliation = rows('numeric_reconciliation.csv')
    assert len(audit) == 40 and {row['doc_id'] for row in audit} == {
        doc_id for doc_id, row in manifest.items() if row['source_id'] != 'SKH_NEWSROOM'}
    for row in audit:
        assert row['audit_status'] == 'passed_sample', row['doc_id']
        assert all(row[field] == 'True' for field in (
            'unit_verified', 'period_verified', 'scope_verified', 'value_verified',
            'header_verified', 'paragraph_verified')), row['doc_id']
        assert row['paragraph_location'] and row['paragraph_source_text']
        if row['source_id'] == 'DART':
            assert row['table_id'] in tables and row['value_block_id'] in block_ids
            assert row['extracted_header_refs']
            if row['company_id'] == 'SAM':
                assert row['period_location']
        else:
            assert row['header_bbox'] and row['value_bbox'] and row['paragraph_bbox']
            if row['company_id'] == 'SAM':
                assert row['related_DS_revenue_raw'] and row['related_DS_op_raw']
    assert len(reconciliation) == 20
    assert all(row['status'] == 'within_rounding' and
               Decimal(row['absolute_delta']) <= Decimal(row['tolerance'])
               for row in reconciliation)
    summary = {
        'documents': len(manifest), 'primary_documents': len(audit),
        'auxiliary_documents': len(manifest) - len(audit),
        'blocks': len(block_ids), 'block_types': dict(sorted(counts.items())),
        'native_tables': len(tables),
        'sample_tables_passed': len(audit),
        'quarter_reconciliations_within_rounding': len(reconciliation),
        'source_dom_or_pdf_text_coverage': '42/42 100%',
        'validation_scope': 'all JSONL records, IDs, positions, table references, source-text counts, sample audits',
        'coverage_limit': 'DART recovered DOM and PDF text layer; raster-only content requires OCR',
    }
    (OUT / 'block_validation.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n',
                                               encoding='utf-8')
    print('Verified', summary['documents'], 'documents,', summary['blocks'], 'blocks,',
          summary['native_tables'], 'native tables,', len(audit), 'audit rows,',
          len(reconciliation), 'reconciliations')


if __name__ == '__main__':
    main()
