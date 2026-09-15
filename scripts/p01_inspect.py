"""Measure extraction readiness of the downloaded P01 sample documents."""

import csv
import warnings
import zipfile
from pathlib import Path

import fitz
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'artifacts' / 'p0'
RAW = OUT / 'raw'
warnings.filterwarnings('ignore', category=XMLParsedAsHTMLWarning)
PRIMARY = {'SAM-2025-FY-DART', 'SKH-2025-FY-DART',
           'SAM-2025Q4-IR', 'SAM-2026Q1-IR',
           'SKH-2025Q4-IR', 'SKH-2026Q1-IR'}


def main():
    rows = []
    for path in sorted(RAW.glob('*.zip')):
        if path.stem not in PRIMARY:
            continue
        with zipfile.ZipFile(path) as archive:
            main_xml = next(name for name in archive.namelist()
                            if name.endswith('.xml') and '_' not in name)
            xml = archive.read(main_xml).decode('utf-8')
        soup = BeautifulSoup(xml, 'lxml')
        text = soup.get_text(' ', strip=True)
        rows.append({'doc_id': path.stem, 'format': 'dart_zip_xml', 'parser': 'BeautifulSoup/lxml',
                     'text_chars': len(text), 'pages': '',
                     'paragraphs': len(soup.find_all('p')), 'tables': len(soup.find_all('table')),
                     'keyword_hbm_found': 'HBM' in text.upper(), 'status': 'text_observed',
                     'limitation': 'XML is not strict well-formed; table headers and cells not audited'})
    for path in sorted(RAW.glob('*.pdf')):
        if path.stem not in PRIMARY:
            continue
        document = fitz.open(path)
        texts = [page.get_text() for page in document]
        rows.append({'doc_id': path.stem, 'format': 'pdf', 'parser': f'PyMuPDF {fitz.VersionBind}',
                     'text_chars': sum(map(len, texts)), 'pages': len(document),
                     'paragraphs': '', 'tables': '',
                     'keyword_hbm_found': any('HBM' in x.upper() for x in texts),
                     'status': 'text_observed',
                     'limitation': 'PDF text layer readable; table header and cell geometry not audited'})
        document.close()
    for path in sorted(RAW.glob('*-ALT.html')):
        html = path.read_text(encoding='utf-8')
        soup = BeautifulSoup(html, 'lxml')
        main = soup.find('article') or soup.find('main') or soup
        text = main.get_text(' ', strip=True)
        rows.append({'doc_id': path.stem, 'format': 'html', 'parser': 'BeautifulSoup/lxml',
                     'text_chars': len(text), 'pages': '',
                     'paragraphs': len(main.find_all('p')), 'tables': len(main.find_all('table')),
                     'keyword_hbm_found': 'HBM' in text.upper(), 'status': 'text_observed',
                     'limitation': 'Official press HTML is an IR substitute; boilerplate and table headers not audited'})
    fields = ['doc_id', 'format', 'parser', 'text_chars', 'pages', 'paragraphs', 'tables',
              'keyword_hbm_found', 'status', 'limitation']
    with (OUT / 'parser_trials.csv').open('w', encoding='utf-8-sig', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    for row in rows:
        print(row['doc_id'], row['format'], 'chars', row['text_chars'], 'pages', row['pages'],
              'tables', row['tables'], 'HBM', row['keyword_hbm_found'])


if __name__ == '__main__':
    main()
