"""Audit one scoped revenue table per P01 document and reconcile DART vs IR.

For DART, inspect the original native XML table, its adjacent unit/period
context, and the extracted table-cell blocks. For PDF, use word coordinates
for a current-quarter revenue row and retain page/header/value positions.
"""

import csv
import json
import re
import zipfile
from collections import Counter
from decimal import Decimal
from pathlib import Path

import fitz
from lxml import etree

from p01_extract_blocks import native_table_grid, compact


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'artifacts' / 'p0'
NUM = re.compile(r'[-+△]?\(?\d[\d,]*(?:\.\d+)?\)?')


def rows(name):
    with (OUT / name).open(encoding='utf-8-sig', newline='') as handle:
        return list(csv.DictReader(handle))


def write_csv(name, data, fields):
    with (OUT / name).open('w', encoding='utf-8-sig', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(data)


def number(value):
    match = NUM.search(value)
    if not match:
        raise ValueError(f'No numeric value: {value[:60]}')
    raw = match.group(0).replace(',', '').replace('△', '-')
    if raw.startswith('(') and raw.endswith(')'):
        raw = '-' + raw[1:-1]
    return Decimal(raw)


def prev_context(table, limit=9):
    pieces = []
    node = table.getprevious()
    while node is not None and len(pieces) < limit:
        text = compact(''.join(node.itertext()))
        if text:
            pieces.append((node.tag.upper() if isinstance(node.tag, str) else '', text[:260], node))
        node = node.getprevious()
    return pieces


def dart_sample(doc, registry):
    with zipfile.ZipFile(ROOT / doc['storage_uri']) as archive:
        main = next(name for name in archive.namelist() if name.endswith('.xml') and '_' not in name)
        root = etree.fromstring(archive.read(main), etree.XMLParser(recover=True, huge_tree=True))
    tree = root.getroottree()
    target_label = 'DS' if doc['company_ids'] == 'SAM' else '\ubc18\ub3c4\uccb4'
    candidates = []
    for index, table in enumerate(root.xpath('.//TABLE')[:200]):
        text = compact(''.join(table.itertext()))
        if not all(x in text for x in ('\ub9e4\ucd9c\uc561', 'DRAM')) or target_label not in text:
            continue
        grid, row_count, col_count = native_table_grid(table)
        row_nodes = table.xpath('./TR|./THEAD/TR|./TBODY/TR|./TFOOT/TR')
        if row_count < 2 or col_count < 3:
            continue
        header_cells = [cell for cell in row_nodes[0] if cell in grid]
        revenue_header = next((cell for cell in header_cells if '\ub9e4\ucd9c\uc561' in compact(''.join(cell.itertext()))
                               and '\ube44\uc911' not in compact(''.join(cell.itertext()))), None)
        if revenue_header is None:
            continue
        header_col = grid[revenue_header][1]
        target_row = None
        value_cell = None
        for row in row_nodes[1:]:
            cells = [cell for cell in row if cell in grid]
            if not cells:
                continue
            label = compact(''.join(cells[0].itertext()))
            if doc['company_ids'] == 'SAM':
                desired = label.startswith('DS') and '\ubd80\ubb38' in label
            else:
                desired = '\ubc18\ub3c4\uccb4' in label and '\ubd80\ubb38' in label
            if desired:
                target_row = cells[0]
                value_cell = next((cell for cell in cells if grid[cell][1] == header_col), None)
                break
        if value_cell is None:
            continue
        context = prev_context(table)
        unit = next((text for _, text, _ in context if '\ub2e8\uc704' in text and
                     ('\uc5b5\uc6d0' in text or '\ubc31\ub9cc\uc6d0' in text)), '')
        if not unit:
            continue
        score = (20 if '\uc8fc\uc694\uc81c\ud488' in text.replace(' ', '') else 0)
        score += (10 if '\ube44\uc911' in text else 0)
        score += (5 if '\uad6c\ubd84' in text or '\ubd80\ubb38' in text else 0)
        score += (5 if '100' in text else 0)
        score -= index / 1000
        candidates.append((score, index, table, revenue_header, target_row, value_cell, unit, context, grid))
    if not candidates:
        raise RuntimeError(f"No scoped numeric table found in {doc['doc_id']}")
    _, index, table, header, label_cell, value_cell, unit, context, grid = max(candidates, key=lambda x: x[0])
    table_xpath = tree.getpath(table)
    registry_key = (doc['doc_id'], main, table_xpath)
    table_id = registry.get(registry_key)
    if table_id is None:
        raise RuntimeError(f"Extracted table missing in {doc['doc_id']}: {table_xpath}")
    value_raw = compact(''.join(value_cell.itertext()))
    source_header = compact(''.join(header.itertext()))
    source_label = compact(''.join(label_cell.itertext()))
    period_context = next((text for _, text, _ in context if re.search(r'\[\uc81c\d+\uae30', text)), '')
    period_location = ''
    if doc['company_ids'] == 'SAM':
        year = doc['reference_period_end'][:4]
        quarter = int(doc['doc_id'][9]) if 'Q' in doc['doc_id'] else 4
        expected = {1: '1\ubd84\uae30', 2: '\ubc18\uae30', 3: '3\ubd84\uae30', 4: ''}[quarter]
        for preceding in reversed(table.xpath('preceding::P')[-40:]):
            value = compact(''.join(preceding.itertext()))
            if year + '\ub144' in value and '\ub9e4\ucd9c' in value and (not expected or expected in value):
                period_context = value[:200]
                period_location = main + ':' + tree.getpath(preceding)
                break
        if not period_context:
            raise RuntimeError(f"No Samsung period narrative near table: {doc['doc_id']}")
    paragraph = next(((tree.getpath(node), text[:200]) for tag, text, node in context
                      if tag == 'P' and ('DRAM' in text or '\uc5f0\uacb0' in text or '\ub9e4\ucd9c' in text)),
                     ('', ''))
    period = f"{doc['reference_period_start']}~{doc['reference_period_end']}"
    return {'doc_id': doc['doc_id'], 'company_id': doc['company_ids'], 'source_id': 'DART',
            'table_location': f'{main}:{table_xpath}', 'table_id': table_id,
            'paragraph_location': f'{main}:{paragraph[0]}' if paragraph[0] else '',
            'paragraph_source_text': paragraph[1],
            'source_header': source_header, 'source_row_label': source_label,
            'source_unit': unit, 'source_period': period_context or period,
            'period_location': period_location,
            'source_scope': 'SAM_DS_segment_including_nonmemory' if doc['company_ids'] == 'SAM'
                            else 'SKH_consolidated_semiconductor_segment',
            'metric': 'DS_revenue' if doc['company_ids'] == 'SAM' else 'company_revenue',
            'value_raw': value_raw, 'value_decimal': str(number(value_raw)),
            'reference_period_start': doc['reference_period_start'],
            'reference_period_end': doc['reference_period_end'],
            'review_method': 'native_XML_source_and_block_compare',
            'table_index_in_main_xml': index, 'unit_verified': bool(unit),
            'period_verified': bool(period_context),
            'scope_verified': bool(source_label),
            'value_verified': False, 'header_verified': False,
            'paragraph_verified': False, 'audit_status': 'pending_block_compare',
            'notes': 'DART table value covers report period (often year-to-date), not necessarily current quarter'}


def current_header(page, year, quarter, side='left'):
    needle = f"{quarter}Q '{year % 100:02d}"
    rects = page.search_for(needle)
    if side == 'left':
        rects = [r for r in rects if r.x0 < page.rect.width * .6]
    else:
        rects = [r for r in rects if r.x0 > page.rect.width * .6]
    return rects[0] if rects else None, needle


def numeric_at_row(page, label, header, side='left'):
    if header is None:
        return None
    words = page.get_text('words')
    labels = [w for w in words if label in w[4] and
              (w[0] < page.rect.width * .5 if side == 'left' else w[0] > page.rect.width * .5)]
    best = None
    for word in labels:
        choices = [w for w in words if re.fullmatch(r'\(?\d[\d,.]*\)?', w[4])
                   and abs(w[1] - word[1]) < 6 and abs(w[0] - header.x0) < 95]
        if not choices:
            continue
        value = min(choices, key=lambda w: abs(w[0] - header.x0))
        candidate = (word, value, abs(value[0] - header.x0))
        if best is None or candidate[2] < best[2]:
            best = candidate
    return best


def pdf_paragraph(pdf, preferred_page):
    """Keep a source text block with prose and its actual PDF page/box."""
    order = [preferred_page] + [i for i in range(len(pdf)) if i != preferred_page]
    for page_index in order:
        for block in pdf[page_index].get_text('dict', sort=True)['blocks']:
            if block['type'] != 0:
                continue
            value = '\n'.join(''.join(span['text'] for span in line.get('spans', []))
                              for line in block.get('lines', []))
            if len(compact(value)) >= 35 and ('.' in value or '\ub2e4.' in value):
                return page_index + 1, value[:200], [round(x, 2) for x in block['bbox']]
    raise RuntimeError('No prose block found in PDF')


def samsung_pdf_sample(doc):
    year = int(doc['doc_id'][4:8])
    quarter = int(doc['doc_id'][9])
    pdf = fitz.open(ROOT / doc['storage_uri'])
    candidates = []
    for index, page in enumerate(pdf):
        header, label = current_header(page, year, quarter, 'left')
        memory = numeric_at_row(page, '\uba54\ubaa8\ub9ac', header, 'left')
        if memory is None:
            continue
        right_header, _ = current_header(page, year, quarter, 'right')
        ds_profit = numeric_at_row(page, 'DS\ubd80\ubb38', right_header, 'right')
        if ds_profit is None:
            ds_profit = numeric_at_row(page, 'DS', right_header, 'right')
        ds_revenue = numeric_at_row(page, 'DS\ubd80\ubb38', header, 'left')
        if ds_revenue is None:
            ds_revenue = numeric_at_row(page, 'DS', header, 'left')
        score = (5 if ds_revenue else 0) + (4 if ds_profit else 0)
        candidates.append((score, index, page, header, memory, ds_revenue, right_header, ds_profit, label))
    if not candidates:
        raise RuntimeError(f"No current-quarter memory revenue table in {doc['doc_id']}")
    _, page_index, page, header, memory, ds_rev, right_header, ds_profit, label = max(candidates, key=lambda x: x[0])
    text = page.get_text()
    if '\uc870\uc6d0' not in text:
        raise RuntimeError(f"Trillion-won unit not found in {doc['doc_id']}")
    mem_label, mem_value, _ = memory
    ds_value = ds_rev[1][4] if ds_rev else ''
    op_value = ds_profit[1][4] if ds_profit else ''
    paragraph_page, paragraph_text, paragraph_bbox = pdf_paragraph(pdf, page_index)
    pdf.close()
    return {'doc_id': doc['doc_id'], 'company_id': 'SAM', 'source_id': 'SAMSUNG_IR',
            'table_location': f'PDF page {page_index + 1}', 'table_id': '',
            'paragraph_location': f'PDF page {paragraph_page}',
            'paragraph_source_text': paragraph_text, 'paragraph_bbox': json.dumps(paragraph_bbox),
            'source_header': label,
            'source_row_label': '\uba54\ubaa8\ub9ac', 'source_unit': '\uc870\uc6d0',
            'source_period': label, 'source_scope': 'SAM_memory_revenue_only',
            'metric': 'memory_revenue', 'value_raw': mem_value[4],
            'value_decimal': str(number(mem_value[4])),
            'reference_period_start': doc['reference_period_start'],
            'reference_period_end': doc['reference_period_end'],
            'review_method': 'PDF_word_geometry_and_page_render',
            'value_bbox': json.dumps([round(x, 2) for x in mem_value[:4]]),
            'header_bbox': json.dumps([round(header.x0, 2), round(header.y0, 2),
                                       round(header.x1, 2), round(header.y1, 2)]),
            'related_DS_revenue_raw': ds_value, 'related_DS_op_raw': op_value,
            'unit_verified': True, 'period_verified': True,
            'scope_verified': bool(ds_rev and ds_profit),
            'value_verified': False, 'header_verified': False,
            'paragraph_verified': False, 'audit_status': 'pending_block_compare',
            'notes': 'Memory revenue is separate from DS revenue and DS operating profit; PDF table cells are not automatically inferred'}


def skh_pdf_sample(doc):
    year = int(doc['doc_id'][4:8])
    quarter = int(doc['doc_id'][9])
    pdf = fitz.open(ROOT / doc['storage_uri'])
    page_index = len(pdf) - 1
    page = pdf[page_index]
    text = page.get_text()
    if '[Attachment2] Income Statement' not in text or 'K-IFRS (KRW Billion)' not in text:
        raise RuntimeError(f"SK income table/unit missing in {doc['doc_id']}")
    header = next((w for w in page.get_text('words') if w[4] == f"Q{quarter}'{year % 100:02d}"), None)
    if header is None:
        raise RuntimeError(f"SK current quarter header missing in {doc['doc_id']}")
    row = next((w for w in page.get_text('words') if w[4] == 'Revenue'), None)
    if row is None:
        raise RuntimeError(f"SK Revenue row missing in {doc['doc_id']}")
    choices = [w for w in page.get_text('words') if re.fullmatch(r'\d[\d,]*', w[4])
               and abs(w[1] - row[1]) < 5 and abs(w[0] - header[0]) < 55]
    if not choices:
        raise RuntimeError(f"SK current revenue value missing in {doc['doc_id']}")
    value = min(choices, key=lambda w: abs(w[0] - header[0]))
    consolidated = any('consolidated' in p.get_text().lower() for p in pdf)
    paragraph_page, paragraph_text, paragraph_bbox = pdf_paragraph(pdf, 1)
    pdf.close()
    return {'doc_id': doc['doc_id'], 'company_id': 'SKH', 'source_id': 'SKH_IR',
            'table_location': f'PDF page {page_index + 1}', 'table_id': '',
            'paragraph_location': f'PDF page {paragraph_page}',
            'paragraph_source_text': paragraph_text, 'paragraph_bbox': json.dumps(paragraph_bbox),
            'source_header': header[4],
            'source_row_label': 'Revenue', 'source_unit': 'KRW Billion',
            'source_period': header[4], 'source_scope': 'SKH_consolidated_company_total',
            'metric': 'company_revenue', 'value_raw': value[4],
            'value_decimal': str(number(value[4])),
            'reference_period_start': doc['reference_period_start'],
            'reference_period_end': doc['reference_period_end'],
            'review_method': 'PDF_word_geometry_and_page_render',
            'value_bbox': json.dumps([round(x, 2) for x in value[:4]]),
            'header_bbox': json.dumps([round(x, 2) for x in header[:4]]),
            'related_DS_revenue_raw': '', 'related_DS_op_raw': '',
            'unit_verified': True, 'period_verified': True,
            'scope_verified': consolidated,
            'value_verified': False, 'header_verified': False,
            'paragraph_verified': False, 'audit_status': 'pending_block_compare',
            'notes': 'IR quarterly revenue is rounded to KRW billion; DART regular report is usually cumulative and in KRW million'}


def compare_blocks(samples):
    by_table = {row['table_id']: row for row in samples if row.get('table_id')}
    by_pdf = {row['doc_id']: row for row in samples if row['source_id'] != 'DART'}
    by_dart_doc = {row['doc_id']: row for row in samples if row['source_id'] == 'DART'}
    seen_cells = {table_id: {} for table_id in by_table}
    paragraph_found = set()
    period_found = set()
    pdf_text = {doc_id: [] for doc_id in by_pdf}
    with (OUT / 'blocks.jsonl').open(encoding='utf-8') as handle:
        for line in handle:
            block = json.loads(line)
            table_id = block.get('table_id')
            if table_id in by_table and block['block_type'] == 'table_cell':
                seen_cells[table_id][block['block_id']] = block
            doc_id = block['doc_id']
            if doc_id in by_pdf and block['block_type'] == 'pdf_text_block':
                pdf_text[doc_id].append((block['page_number'], block['raw_text']))
            row = by_dart_doc.get(doc_id)
            if row and row['paragraph_location'] and block['block_type'] == 'paragraph':
                if block['source_entry'] + ':' + block['source_xpath'] == row['paragraph_location']:
                    paragraph_found.add(doc_id)
            if row and row.get('period_location') and block['block_type'] == 'paragraph':
                if block['source_entry'] + ':' + block['source_xpath'] == row['period_location']:
                    period_found.add(doc_id)
    for row in samples:
        if row['source_id'] == 'DART':
            cells = seen_cells[row['table_id']]
            value_cells = [cell for cell in cells.values() if compact(cell['raw_text']) == row['value_raw']
                           and cell.get('row_index') not in (None, 0)]
            header_cells = [cell for cell in cells.values() if row['source_header'] in compact(cell['raw_text'])
                            and cell.get('row_index') == 0]
            matching = next((cell for cell in value_cells if any(ref in cells and
                             row['source_header'] in compact(cells[ref]['raw_text'])
                             for ref in cell.get('header_refs', []))), None)
            row['value_verified'] = bool(value_cells)
            row['header_verified'] = bool(header_cells and matching)
            row['paragraph_verified'] = row['doc_id'] in paragraph_found
            if row.get('period_location'):
                row['period_verified'] = row['period_verified'] and row['doc_id'] in period_found
            if matching:
                row['value_block_id'] = matching['block_id']
                row['extracted_header_refs'] = '|'.join(matching['header_refs'])
        else:
            table_page = int(row['table_location'].split()[-1])
            source = ''.join(value for page, value in pdf_text[row['doc_id']] if page == table_page)
            row['value_verified'] = row['value_raw'] in source
            row['header_verified'] = row['source_header'] in source
            paragraph_page = int(row['paragraph_location'].split()[-1])
            row['paragraph_verified'] = any(row['paragraph_source_text'] in value
                                            for page, value in pdf_text[row['doc_id']]
                                            if page == paragraph_page)
            row['value_block_id'] = ''
            row['extracted_header_refs'] = ''
        row['audit_status'] = ('passed_sample' if all(row[x] for x in
                               ('unit_verified', 'period_verified', 'scope_verified',
                                'value_verified', 'header_verified', 'paragraph_verified'))
                               else 'needs_review')


def reconcile(samples):
    dart_by_company = {cid: {} for cid in ('SAM', 'SKH')}
    ir_by_company = {cid: {} for cid in ('SAM', 'SKH')}
    for row in samples:
        quarter = re.search(r'(\d{4}Q\d)', row['doc_id']).group(1) if re.search(r'(\d{4}Q\d)', row['doc_id']) else '2025Q4'
        if row['source_id'] == 'DART':
            dart_by_company[row['company_id']][quarter] = row
        elif row['source_id'] in ('SAMSUNG_IR', 'SKH_IR'):
            ir_by_company[row['company_id']][quarter] = row
    comparisons = []
    for cid in ('SAM', 'SKH'):
        for year in (2024, 2025, 2026):
            previous = Decimal(0)
            for quarter in range(1, 5):
                if year == 2026 and quarter > 2:
                    break
                qid = f'{year}Q{quarter}'
                dart = dart_by_company[cid].get(qid)
                ir = ir_by_company[cid].get(qid)
                if not dart or not ir:
                    comparisons.append({'company_id': cid, 'quarter': qid, 'status': 'missing_pair'})
                    continue
                cumulative = Decimal(dart['value_decimal'])
                quarterly = cumulative - previous
                previous = cumulative
                if cid == 'SAM':
                    dart_quarter_unit = quarterly / Decimal(10000)  # 10,000 KRW 100M per KRW trillion
                    ir_unit = Decimal(ir.get('related_DS_revenue_raw', '') or 'NaN')
                    tolerance = Decimal('0.15')
                    scope = 'SAM_DS_revenue'
                else:
                    dart_quarter_unit = quarterly / Decimal(1000)  # KRW million to billion
                    ir_unit = Decimal(ir['value_decimal'])
                    tolerance = Decimal('1.0')
                    scope = 'SKH_company_revenue'
                delta = abs(dart_quarter_unit - ir_unit)
                status = 'within_rounding' if delta <= tolerance else 'mismatch'
                comparisons.append({'company_id': cid, 'quarter': qid, 'metric_scope': scope,
                                    'dart_doc_id': dart['doc_id'], 'ir_doc_id': ir['doc_id'],
                                    'dart_cumulative_raw': dart['value_raw'],
                                    'dart_quarter_converted': str(dart_quarter_unit),
                                    'ir_quarter_raw': str(ir_unit), 'absolute_delta': str(delta),
                                    'tolerance': str(tolerance), 'status': status})
                dart['comparison_doc_id'] = ir['doc_id']
                dart['comparison_delta'] = str(delta)
                ir['comparison_doc_id'] = dart['doc_id']
                ir['comparison_delta'] = str(delta)
                if status == 'mismatch':
                    dart['audit_status'] = ir['audit_status'] = 'needs_review'
    return comparisons


def main():
    manifest = rows('document_manifest.csv')
    registry = {(row['doc_id'], row['source_entry'], row['source_xpath']): row['table_id']
                for row in rows('table_registry.csv')}
    samples = []
    for doc in manifest:
        if doc['source_id'] == 'DART':
            samples.append(dart_sample(doc, registry))
        elif doc['source_id'] == 'SAMSUNG_IR':
            samples.append(samsung_pdf_sample(doc))
        elif doc['source_id'] == 'SKH_IR':
            samples.append(skh_pdf_sample(doc))
    compare_blocks(samples)
    comparisons = reconcile(samples)
    fields = ['doc_id', 'company_id', 'source_id', 'review_method', 'table_location', 'table_id',
              'table_index_in_main_xml', 'paragraph_location', 'paragraph_source_text', 'paragraph_bbox',
              'source_header', 'source_row_label', 'source_unit', 'source_period', 'period_location', 'source_scope',
              'metric', 'value_raw', 'value_decimal', 'related_DS_revenue_raw', 'related_DS_op_raw',
              'reference_period_start', 'reference_period_end', 'header_bbox', 'value_bbox',
              'value_block_id', 'extracted_header_refs', 'comparison_doc_id', 'comparison_delta',
              'unit_verified', 'period_verified', 'scope_verified', 'value_verified',
              'header_verified', 'paragraph_verified', 'audit_status', 'notes']
    write_csv('extraction_audit.csv', samples, fields)
    write_csv('numeric_reconciliation.csv', comparisons,
              ['company_id', 'quarter', 'metric_scope', 'dart_doc_id', 'ir_doc_id',
               'dart_cumulative_raw', 'dart_quarter_converted', 'ir_quarter_raw',
               'absolute_delta', 'tolerance', 'status'])
    status = Counter(row['audit_status'] for row in samples)
    reconciled = Counter(row['status'] for row in comparisons)
    print('Audited:', len(samples), 'sample tables;', status)
    print('Reconciled:', len(comparisons), 'quarter pairs;', reconciled)
    for row in comparisons:
        if row['status'] != 'within_rounding':
            print('REVIEW', row['company_id'], row['quarter'], row['status'],
                  row.get('dart_quarter_converted'), row.get('ir_quarter_raw'))


if __name__ == '__main__':
    main()
