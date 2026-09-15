"""Extract all text and native table cells from P01 documents with provenance.

DART SGML/XML is parsed with lxml recover mode. PDF text blocks retain page
coordinates; visual PDF table relationships are deliberately not guessed.
"""

import csv
import hashlib
import json
import re
import zipfile
from collections import Counter
from pathlib import Path

import fitz
from lxml import etree, html


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'artifacts' / 'p0'
VERSION = 'p01-blocks-v1'
CELL_TAGS = {'TD', 'TH', 'TU', 'TE'}
GROUP_TAGS = {'P', 'TITLE', 'COVER-TITLE', 'IMG-CAPTION', 'DOCUMENT-NAME', 'COMPANY-NAME',
              'H1', 'H2', 'H3', 'H4', 'H5', 'H6'}


def compact(value):
    return re.sub(r'\s+', ' ', value).strip()


def nonwhite_length(value):
    return len(re.sub(r'\s+', '', value))


def csv_rows(path):
    with path.open(encoding='utf-8-sig', newline='') as handle:
        return list(csv.DictReader(handle))


class Emitter:
    def __init__(self, handle, doc, entry):
        self.handle = handle
        self.doc = doc
        self.entry = entry
        self.seq = 0
        self.table_seq = 0
        self.counts = Counter()
        self.emitted_nonwhite = 0
        self.page_break_index = 0
        self.table_rows = []

    def emit(self, kind, raw_text, **extra):
        if not raw_text and kind not in ('image_marker', 'page_break'):
            return None
        self.seq += 1
        block_id = f"{self.doc['doc_id']}:{self.entry}:B{self.seq:07d}"
        record = {'block_id': block_id, 'doc_id': self.doc['doc_id'],
                  'revision_id': self.doc['revision_id'], 'block_type': kind,
                  'page_number': None, 'section_path': '', 'raw_text': raw_text,
                  'normalized_text': compact(raw_text),
                  'offset_mapping': {'status': 'not_available', 'unit': 'unicode_codepoint'},
                  'table_id': None, 'row_index': None, 'col_index': None,
                  'header_refs': [], 'extraction_method': '',
                  'extraction_version': VERSION, 'source_entry': self.entry,
                  'source_xpath': None, 'source_line': None, 'bbox': None,
                  'page_index': None, 'xml_page_break_index': None,
                  'printed_page_number': None, 'unit_context': None,
                  'scope_context': None}
        record.update(extra)
        self.handle.write(json.dumps(record, ensure_ascii=False, separators=(',', ':')) + '\n')
        self.counts[kind] += 1
        self.emitted_nonwhite += nonwhite_length(raw_text)
        return block_id


def text_excluding_tables(node):
    parts = []
    nested = []

    def visit(element):
        if element.text:
            parts.append(element.text)
        for child in element:
            if isinstance(child.tag, str) and child.tag.upper() == 'TABLE':
                nested.append(child)
            else:
                visit(child)
            if child.tail:
                parts.append(child.tail)

    visit(node)
    return ''.join(parts), nested


def native_table_grid(table):
    cell_info = {}
    occupied = set()
    # DART also nests TR inside TR (for example, LIBRARY/TABLE-GROUP/TBODY/TR/TR).
    # Keep descendant rows whose nearest TABLE ancestor is this table, while
    # excluding rows belonging to a genuinely nested TABLE.
    rows = []
    for row in table.iterdescendants():
        if not isinstance(row.tag, str) or row.tag.upper() != 'TR':
            continue
        parent_table = next((ancestor for ancestor in row.iterancestors()
                             if isinstance(ancestor.tag, str) and ancestor.tag.upper() == 'TABLE'), None)
        if parent_table is table and any(isinstance(cell.tag, str) and cell.tag.upper() in CELL_TAGS
                                         for cell in row):
            rows.append(row)
    for ri, row in enumerate(rows):
        col = 0
        for cell in row:
            if not isinstance(cell.tag, str) or cell.tag.upper() not in CELL_TAGS:
                continue
            while (ri, col) in occupied:
                col += 1
            colspan = max(1, int(cell.get('COLSPAN') or cell.get('colspan') or '1'))
            rowspan = max(1, int(cell.get('ROWSPAN') or cell.get('rowspan') or '1'))
            cell_info[cell] = (ri, col, rowspan, colspan)
            for r in range(ri, ri + rowspan):
                for c in range(col, col + colspan):
                    occupied.add((r, c))
            col += colspan
    return cell_info, len(rows), max((c for _, c in occupied), default=-1) + 1


def preceding_context(node):
    pieces = []
    prev = node.getprevious()
    while prev is not None and len(pieces) < 4:
        value = compact(' '.join(prev.itertext()))
        if value:
            pieces.append(value[:220])
        prev = prev.getprevious()
    return ' | '.join(reversed(pieces))


def emit_dom(root, emitter, method):
    tree = root.getroottree()
    source_nonwhite = sum(nonwhite_length(t) for t in root.itertext())
    table_states = {}

    def emit_node(kind, value, node, sections, **extra):
        return emitter.emit(kind, value, section_path=' / '.join(sections),
                            source_xpath=tree.getpath(node), source_line=node.sourceline,
                            xml_page_break_index=emitter.page_break_index if method == 'dart_xml_recover' else None,
                            extraction_method=method, **extra)

    def walk(node, sections=(), table_id=None):
        if not isinstance(node.tag, str):
            return
        tag = node.tag.upper()
        if tag.startswith('SECTION-'):
            title = next((child for child in node if isinstance(child.tag, str)
                          and child.tag.upper() == 'TITLE'), None)
            if title is not None:
                label = compact(''.join(title.itertext()))[:160]
                sections = sections + (label or tag,)
            else:
                sections = sections + (tag,)
        if tag == 'PGBRK':
            emitter.page_break_index += 1
            emitter.emit('page_break', '', section_path=' / '.join(sections),
                         source_xpath=tree.getpath(node), source_line=node.sourceline,
                         xml_page_break_index=emitter.page_break_index,
                         extraction_method=method)
            return
        if tag == 'TABLE':
            emitter.table_seq += 1
            table_id = f"{emitter.doc['doc_id']}:{emitter.entry}:T{emitter.table_seq:06d}"
            cell_info, row_count, col_count = native_table_grid(node)
            context = preceding_context(node)
            table_states[table_id] = {'cell_info': cell_info, 'col_headers': {},
                                      'row_header': {}, 'context': context}
            emitter.table_rows.append({'table_id': table_id, 'doc_id': emitter.doc['doc_id'],
                                       'revision_id': emitter.doc['revision_id'],
                                       'source_entry': emitter.entry, 'source_xpath': tree.getpath(node),
                                       'source_line': node.sourceline, 'row_count': row_count,
                                       'col_count': col_count, 'context': context[:300],
                                       'page_number': '', 'method': method,
                                       'semantic_status': 'native_grid_unreviewed'})
        if tag in GROUP_TAGS or tag in CELL_TAGS:
            value, nested_tables = text_excluding_tables(node)
            kind = 'table_cell' if tag in CELL_TAGS else ('heading' if tag in {'TITLE', 'COVER-TITLE',
                                                                               'H1', 'H2', 'H3', 'H4', 'H5', 'H6'} else 'paragraph')
            extra = {}
            grid = None
            if kind == 'table_cell' and table_id in table_states:
                state = table_states[table_id]
                grid = state['cell_info'].get(node)
                if grid:
                    ri, ci, rowspan, colspan = grid
                    refs = []
                    for c in range(ci, ci + colspan):
                        refs.extend(state['col_headers'].get(c, []))
                    if ci > 0 and ri in state['row_header']:
                        refs.append(state['row_header'][ri])
                    extra = {'table_id': table_id, 'row_index': ri, 'col_index': ci,
                             'rowspan': rowspan, 'colspan': colspan,
                             'header_refs': list(dict.fromkeys(refs)),
                             'unit_context': state['context'][:300]}
                else:
                    extra = {'table_id': table_id, 'grid_status': 'row_not_indexed'}
            block_id = emit_node(kind, value, node, sections, **extra)
            if block_id and kind == 'table_cell' and grid:
                header_like = tag == 'TH' or (ri == 0 and not re.search(r'\d', compact(value)))
                if header_like:
                    for c in range(ci, ci + colspan):
                        state['col_headers'].setdefault(c, []).append(block_id)
                if ci == 0 and not re.fullmatch(r'[\d,.%()\-+△]+', compact(value)):
                    state['row_header'][ri] = block_id
            for nested in nested_tables:
                walk(nested, sections, table_id=None)
            return
        if tag in {'IMG', 'IMAGE'}:
            emitter.emit('image_marker', '', section_path=' / '.join(sections),
                         source_xpath=tree.getpath(node), source_line=node.sourceline,
                         extraction_method=method,
                         image_ref=node.get('SRC') or node.get('src') or node.get('REF'))
        if node.text and node.text.strip():
            emit_node('inline_text', node.text, node, sections, table_id=table_id)
        for child in node:
            walk(child, sections, table_id)
            if child.tail and child.tail.strip():
                emit_node('inline_text', child.tail, child, sections, table_id=table_id,
                          tail_of_child=True)

    walk(root)
    return source_nonwhite, emitter.emitted_nonwhite, emitter.table_rows


def extract_dart(doc, handle):
    path = ROOT / doc['storage_uri']
    totals = Counter()
    tables = []
    with zipfile.ZipFile(path) as archive:
        for entry in archive.namelist():
            if not entry.lower().endswith('.xml'):
                continue
            payload = archive.read(entry)
            root = etree.fromstring(payload, etree.XMLParser(recover=True, huge_tree=True))
            emitter = Emitter(handle, doc, entry)
            source_chars, emitted_chars, rows = emit_dom(root, emitter, 'dart_xml_recover')
            totals.update(emitter.counts)
            totals['source_nonwhite'] += source_chars
            totals['emitted_nonwhite'] += emitted_chars
            totals['xml_entries'] += 1
            tables.extend(rows)
    return totals, tables


def extract_pdf(doc, handle):
    path = ROOT / doc['storage_uri']
    document = fitz.open(path)
    emitter = Emitter(handle, doc, path.name)
    source_nonwhite = 0
    for page_index, page in enumerate(document):
        source_nonwhite += nonwhite_length(page.get_text())
        data = page.get_text('dict', sort=True)
        for block in data['blocks']:
            if block['type'] == 1:
                emitter.emit('image_marker', '', page_number=page_index + 1,
                             page_index=page_index, bbox=list(block['bbox']),
                             extraction_method=f'PyMuPDF {fitz.VersionBind}')
                continue
            lines = []
            for line in block.get('lines', []):
                value = ''.join(span['text'] for span in line.get('spans', []))
                if value:
                    lines.append(value)
            value = '\n'.join(lines)
            emitter.emit('pdf_text_block', value, page_number=page_index + 1,
                         page_index=page_index, bbox=list(block['bbox']),
                         section_path=f'PDF page {page_index + 1}',
                         extraction_method=f'PyMuPDF {fitz.VersionBind}')
    document.close()
    totals = emitter.counts
    totals['source_nonwhite'] = source_nonwhite
    totals['emitted_nonwhite'] = emitter.emitted_nonwhite
    totals['pdf_pages'] = page_index + 1
    return totals, []


def extract_html(doc, handle):
    path = ROOT / doc['storage_uri']
    root = html.fromstring(path.read_bytes())
    article = root.xpath('//article') or root.xpath('//main')
    body = article[0] if article else root
    emitter = Emitter(handle, doc, path.name)
    source_chars, emitted_chars, tables = emit_dom(body, emitter, 'official_html_lxml')
    totals = emitter.counts
    totals['source_nonwhite'] = source_chars
    totals['emitted_nonwhite'] = emitted_chars
    totals['html_entries'] = 1
    return totals, tables


def main():
    manifest = csv_rows(OUT / 'document_manifest.csv')
    temp_path = OUT / 'blocks.jsonl.tmp'
    output_path = OUT / 'blocks.jsonl'
    count_rows = []
    all_tables = []
    with temp_path.open('w', encoding='utf-8', newline='\n') as handle:
        for doc in manifest:
            if doc['source_id'] == 'DART':
                totals, tables = extract_dart(doc, handle)
            elif doc['format'] == 'pdf':
                totals, tables = extract_pdf(doc, handle)
            else:
                totals, tables = extract_html(doc, handle)
            all_tables.extend(tables)
            count_rows.append({'doc_id': doc['doc_id'], 'revision_id': doc['revision_id'],
                               'format': doc['format'], 'source_id': doc['source_id'],
                               'source_nonwhite_chars': totals['source_nonwhite'],
                               'emitted_nonwhite_chars': totals['emitted_nonwhite'],
                               'text_coverage_ratio': round(totals['emitted_nonwhite'] / totals['source_nonwhite'], 5)
                                if totals['source_nonwhite'] else '',
                               'paragraph_or_text_blocks': totals['paragraph'] + totals['pdf_text_block'],
                               'table_cells': totals['table_cell'],
                               'native_tables': len(tables), 'image_markers': totals['image_marker'],
                               'page_breaks': totals['page_break'],
                               'pdf_pages': totals['pdf_pages'],
                               'source_entries': totals['xml_entries'] or totals['html_entries'] or 1,
                               'status': 'extracted_full_text' if totals['emitted_nonwhite'] >= totals['source_nonwhite'] * 0.995
                                else 'coverage_gap', 'parser_version': VERSION})
            print(doc['doc_id'], 'blocks', sum(totals[k] for k in ('paragraph', 'pdf_text_block', 'table_cell', 'heading', 'inline_text')),
                  'tables', len(tables), 'coverage', count_rows[-1]['text_coverage_ratio'], flush=True)
    temp_path.replace(output_path)
    count_fields = list(count_rows[0])
    with (OUT / 'block_counts.csv').open('w', encoding='utf-8-sig', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=count_fields)
        writer.writeheader()
        writer.writerows(count_rows)
    table_fields = list(all_tables[0])
    with (OUT / 'table_registry.csv').open('w', encoding='utf-8-sig', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=table_fields)
        writer.writeheader()
        writer.writerows(all_tables)
    print('TOTAL', len(count_rows), 'documents;', len(all_tables), 'native tables;',
          output_path.stat().st_size, 'JSONL bytes')


if __name__ == '__main__':
    main()
