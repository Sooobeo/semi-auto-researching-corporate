"""Publish the completed P01 extraction/audit status without fetching again."""

import csv
import json
from collections import Counter
from datetime import date
from decimal import Decimal
from pathlib import Path

import fitz


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'artifacts' / 'p0'


def rows(name):
    with (OUT / name).open(encoding='utf-8-sig', newline='') as handle:
        return list(csv.DictReader(handle))


def write_csv(name, data, fields):
    with (OUT / name).open('w', encoding='utf-8-sig', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(data)


def main():
    validation = json.loads((OUT / 'block_validation.json').read_text(encoding='utf-8'))
    manifest = rows('document_manifest.csv')
    counts = {row['doc_id']: row for row in rows('block_counts.csv')}
    audit = {row['doc_id']: row for row in rows('extraction_audit.csv')}
    compare = rows('numeric_reconciliation.csv')
    assert validation['documents'] == len(manifest) == len(counts) == 42
    assert validation['sample_tables_passed'] == len(audit) == 40
    assert validation['quarter_reconciliations_within_rounding'] == len(compare) == 20
    for row in manifest:
        row['parse_status'] = 'full_text_layer_extracted'
    write_csv('document_manifest.csv', manifest, list(manifest[0]))

    existing = {row['doc_id']: row for row in rows('parser_trials.csv')}
    trials = []
    raster_only = 0
    raster_docs = 0
    for doc in manifest:
        count = counts[doc['doc_id']]
        missing_pages = 0
        if doc['format'] == 'pdf':
            pdf = fitz.open(ROOT / doc['storage_uri'])
            missing_pages = sum(not page.get_text().strip() and bool(page.get_images()) for page in pdf)
            pdf.close()
            raster_only += missing_pages
            raster_docs += bool(missing_pages)
        original = existing.get(doc['doc_id'], {})
        trials.append({'doc_id': doc['doc_id'], 'format': doc['format'],
                       'parser': count['parser_version'],
                       'text_chars': count['emitted_nonwhite_chars'],
                       'pages': count['pdf_pages'] or '',
                       'paragraphs': count['paragraph_or_text_blocks'],
                       'tables': count['native_tables'],
                       'keyword_hbm_found': original.get('keyword_hbm_found', ''),
                       'status': 'full_text_layer_extracted',
                       'image_only_pages': missing_pages,
                       'limitation': ('Image-only PDF pages have image markers but no OCR text'
                                      if missing_pages else
                                      'PDF tables retain text/geometry but not native cell grid'
                                      if doc['format'] == 'pdf' else
                                      'DART XML parsed in recover mode; character coverage is against recovered DOM'
                                      if doc['source_id'] == 'DART' else
                                      'HTML article/main content extracted')})
    write_csv('parser_trials.csv', trials, list(trials[0]))
    max_sam = max(Decimal(row['absolute_delta']) for row in compare if row['company_id'] == 'SAM')
    max_skh = max(Decimal(row['absolute_delta']) for row in compare if row['company_id'] == 'SKH')
    s24 = audit['SAM-2024Q1-IR']
    s25 = audit['SAM-2025Q4-IR']
    s26 = audit['SAM-2026Q1-IR']
    sk26 = audit['SKH-2026Q1-IR']
    report = f'''# P01 데이터 가능성 조사 — 검증 결과

기준일: {date.today().isoformat()}. 조사 범위는 삼성전자와 SK하이닉스의 2024Q1~2026Q2, 각 10개 분기다. 공식 정기보고서 20건(OpenDART `document.xml` ZIP), 공식 실적 IR PDF 20건, SK 공식 Newsroom 보조 HTML 2건을 확보했다. 기본 조사 대상 40건은 모두 원본 크기와 SHA-256을 대조했고, 20개 회사·분기 칸에 정기보고서와 IR이 각각 있다.

## 본문 추출

- 42개 문서의 XML/HTML 본문 또는 PDF 텍스트 레이어를 `blocks.jsonl`에 전부 분리했다. 블록 {validation['blocks']:,}개(문단 {validation['block_types']['paragraph']:,}, PDF 텍스트 블록 {validation['block_types']['pdf_text_block']:,}, 원문 표 셀 {validation['block_types']['table_cell']:,}, 제목 {validation['block_types']['heading']:,})와 원문 표 {validation['native_tables']:,}개다. 문서·원본 ZIP 항목·XPath/소스 행 또는 PDF 페이지/bbox를 남겼다. [block_counts.csv](block_counts.csv), [block_validation.json](block_validation.json), [parser_trials.csv](parser_trials.csv).
- 원본을 해석한 XML DOM/HTML 본문과 PDF 텍스트 레이어에서 공백 제외 문자 수가 추출 블록과 42/42건 일치한다. 전체 JSONL 레코드, 고유 ID, 표 머리글 참조, 행·열 좌표와 페이지 범위를 스트리밍 검사했다. DART 비표준 중첩 행 80셀도 원문 표 그리드에 매핑했다.
- SK IR {raster_docs}건에는 이미지로만 된 구분 페이지 {raster_only}쪽이 있다. 이 페이지는 이미지 위치만 기록하고 OCR 텍스트는 생성하지 않았다. 검토한 구분 페이지에는 `Financial Results`, `Market Outlook / Company Plan`, `Appendix` 제목이 보인다. 따라서 위의 100%는 **XML 복구 DOM/HTML 본문/PDF 텍스트 레이어 기준**이며 이미지 안의 글자까지 포함하는 원본 전체의 의미적 완전성을 뜻하지 않는다. PDF 표는 텍스트와 좌표를 보존했지만 자동 셀 그리드는 없다.

## 숫자표·문단 감사

- 기본 문서 40건마다 본문 문단 1개와 매출 숫자표 1개를 원문 위치 및 추출 블록과 대조했다. 표 머리글, 단위, 보고 기간, 사업 범위, 값, 문단이 40/40건 통과했다. DART는 XML 원문 표 셀·주변 단위/기간 문장과 블록의 `header_refs`를 확인했고, PDF는 원본 페이지 화면과 단어 좌표를 확인했다. [extraction_audit.csv](extraction_audit.csv).
- 삼성 IR의 **메모리 매출**은 **DS 부문 매출** 및 **DS 부문 영업이익**과 별개의 행이다. 예를 들어 2024Q1은 각각 {s24['value_raw']}·{s24['related_DS_revenue_raw']}·{s24['related_DS_op_raw']}조원, 2025Q4는 {s25['value_raw']}·{s25['related_DS_revenue_raw']}·{s25['related_DS_op_raw']}조원, 2026Q1은 {s26['value_raw']}·{s26['related_DS_revenue_raw']}·{s26['related_DS_op_raw']}조원이다. 삼성 정기보고서의 DS 매출 표에는 DRAM/NAND 외 모바일 AP도 포함되므로 메모리 전용 매출로 대체하지 않았다.
- SK IR 2026Q1 손익계산서의 머리글은 `Q1'26`, 단위는 `K-IFRS (KRW Billion)`, 전사 매출은 {sk26['value_raw']}십억원이다. 정기보고서는 백만원, 삼성 정기보고서는 억원 단위이며 Q2/Q3 정기보고서 값은 반기/3분기 누적이다. 연초 누적 값을 차분하여 IR 분기 값과 맞춘 결과 20/20쌍이 표시 반올림 범위에서 일치했다. 최대 차이는 삼성 DS 매출 {max_sam}조원, SK 전사 매출 {max_skh}십억원이다. [numeric_reconciliation.csv](numeric_reconciliation.csv).

## P01 판단과 남은 한계

기본 40건의 API/HTTP 확보와 텍스트 레이어 추출, 문서별 표본 감사, 10분기 커버리지는 재현 가능했다. P01의 수치 사용 시 삼성 메모리·DS와 SK 전사 범위를 분리하고, 정기보고서 누적 기간을 분기 값으로 보정해야 한다. 이미지형 구분 페이지 제목이나 그림 속 새 수치가 필요하면 해당 페이지에 OCR과 원본 화면 검토를 추가한다. OpenDART와 공식 IR 자료의 재배포·공유 조건, 삼성 IR 목록 페이지의 자동 접근 차단, SK 공개 보드 엔드포인트의 안정성은 [source_registry.csv](source_registry.csv)에 미확인으로 남겼다.

재실행 순서: `p01_collect.py` → 세 `p01_fetch_*.py` → `p01_inspect.py` → `p01_finalize.py` → `p01_extract_blocks.py` → `p01_audit_numbers.py` → `p01_verify.py` → `p01_verify_extraction.py` → `p01_complete.py`. API 키는 Git 제외 `.env`에서만 읽고 원본 및 전체 블록은 Git에서 제외했다.
'''
    (OUT / 'data_feasibility.md').write_text(report, encoding='utf-8')
    print('Completed report: 42 documents, 40 audited samples, 20 reconciliations,',
          raster_only, 'image-only PDF pages')


if __name__ == '__main__':
    main()
