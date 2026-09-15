"""Build P01 source and feasibility summaries from observed collection records."""

import csv
from collections import Counter
from datetime import date

from p01_collect import OUT, dart, env_values


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
    entities = read_csv('entities.csv')
    overview = []
    for entity in entities:
        body = dart(env, 'company.json', {'corp_code': entity['corp_code']})
        if body.get('status') != '000' or body.get('stock_code') != entity['ticker']:
            raise RuntimeError(f"Official company overview mismatch: {entity['company_id']}")
        entity['corpcode_name'] = entity.get('corpcode_name') or entity['legal_name']
        entity['legal_name'] = body['corp_name']
        entity['corp_eng_name'] = body.get('corp_name_eng', entity['corp_eng_name'])
        overview.append({'company_id': entity['company_id'], 'corp_code': entity['corp_code'],
                         'corp_name': body['corp_name'], 'corp_name_eng': body.get('corp_name_eng', ''),
                         'stock_name': body.get('stock_name', ''), 'stock_code': body['stock_code'],
                         'corp_cls': body.get('corp_cls', ''), 'ir_url': body.get('ir_url', ''),
                         'hm_url': body.get('hm_url', ''), 'acc_mt': body.get('acc_mt', ''),
                         'source_endpoint': 'company.json', 'checked_at': date.today().isoformat()})
    write_csv('company_overview.csv', overview, list(overview[0]))
    write_csv('entities.csv', entities,
              ['company_id', 'legal_name', 'corpcode_name', 'corp_code', 'ticker',
               'corp_eng_name', 'official_modify_date', 'evidence', 'scope_id'])

    manifest = read_csv('document_manifest.csv')
    sk_list = {row['quarter']: row for row in read_csv('sk_ir_list.csv')}
    parsed = {row['doc_id']: row for row in read_csv('parser_trials.csv')}
    for row in manifest:
        if row['source_id'] == 'DART':
            row['attachment_url'] = ('https://opendart.fss.or.kr/api/document.xml?rcept_no='
                                     + row['revision_id'])
            row['source_api_record_id'] = row['revision_id']
            row['event_date_raw'] = ''
        elif row['source_id'] == 'SKH_IR':
            quarter = row['doc_id'].split('-')[1]
            item = sk_list[quarter]
            row['attachment_url'] = item['file_url']
            row['source_api_record_id'] = item['seq']
            row['event_date_raw'] = item['event_date_raw']
        else:
            row['attachment_url'] = row['source_url']
            row['source_api_record_id'] = ''
            row['event_date_raw'] = ''
        if row['doc_id'] in parsed and row.get('parse_status') != 'full_text_layer_extracted':
            row['parse_status'] = 'text_observed_partial'
    fields = ['doc_id', 'revision_id', 'source_id', 'source_url', 'attachment_url',
              'source_api_record_id', 'title', 'company_ids', 'reference_period_start',
              'reference_period_end', 'published_date', 'event_date_raw', 'time_precision',
              'observed_at', 'format', 'storage_uri', 'byte_size', 'sha256', 'parse_status']
    write_csv('document_manifest.csv', manifest, fields)

    sources = [
        {'source_id': 'DART', 'provider': '금융감독원 OpenDART', 'source_type': 'authenticated_api',
         'landing_url': 'https://opendart.fss.or.kr/',
         'terms_url': 'https://opendart.fss.or.kr/intro/terms.do',
         'authentication': 'API key required; held in .env', 'manual_read': 'not_tested',
         'automated_access': 'observed_success', 'storage_policy': 'local raw copy; public filing',
         'sharing_policy': 'unverified', 'redistribution_policy': 'unverified',
         'rate_limit_evidence': 'Official company.json guide lists status 020 and generally 20,000+ requests; actual key quota unverified',
         'status': 'adopt_for_P01', 'unresolved_reason': 'Sharing/redistribution and account-specific quota unverified'},
        {'source_id': 'SAMSUNG_IR', 'provider': '삼성전자 IR', 'source_type': 'official_pdf_http',
         'landing_url': 'https://www.samsung.com/global/ir/financial-information/earnings-release/',
         'terms_url': '', 'authentication': 'none_observed', 'manual_read': 'not_tested',
         'automated_access': 'PDF_direct_success; landing_HTML_403',
         'storage_policy': 'local raw copy; sharing unverified', 'sharing_policy': 'unverified',
         'redistribution_policy': 'unverified', 'rate_limit_evidence': 'not_verified',
         'status': 'adopt_direct_PDF_for_P01', 'unresolved_reason': 'Landing page blocks automated fetch; document API not identified'},
        {'source_id': 'SKH_IR', 'provider': 'SK하이닉스 IR', 'source_type': 'public_site_board_api_and_pdf',
         'landing_url': 'https://www.skhynix.com/ir/UI-FR-IR06/', 'terms_url': '',
         'authentication': 'none_observed', 'manual_read': 'not_tested',
         'automated_access': 'board/list_and_PDF_success',
         'storage_policy': 'local raw copy; sharing unverified', 'sharing_policy': 'unverified',
         'redistribution_policy': 'unverified', 'rate_limit_evidence': 'not_verified',
         'status': 'adopt_with_endpoint_watch',
         'unresolved_reason': 'Public site endpoint is not a documented external API; stability and terms unverified'},
        {'source_id': 'SKH_NEWSROOM', 'provider': 'SK하이닉스 Newsroom', 'source_type': 'official_html_http',
         'landing_url': 'https://news.skhynix.com/en/category/ir/', 'terms_url': '',
         'authentication': 'none_observed', 'manual_read': 'not_tested',
         'automated_access': 'observed_success',
         'storage_policy': 'local auxiliary copy; sharing unverified', 'sharing_policy': 'unverified',
         'redistribution_policy': 'unverified', 'rate_limit_evidence': 'not_verified',
         'status': 'auxiliary_only', 'unresolved_reason': 'Distinct publication from IR PDF'},
    ]
    for row in sources:
        row['checked_at'] = date.today().isoformat()
    source_fields = ['source_id', 'provider', 'source_type', 'landing_url', 'terms_url',
                     'checked_at', 'authentication', 'manual_read', 'automated_access',
                     'storage_policy', 'sharing_policy', 'redistribution_policy',
                     'rate_limit_evidence', 'status', 'unresolved_reason']
    write_csv('source_registry.csv', sources, source_fields)

    relations = [
        {'doc_id': f'SKH-{quarter}-IR-ALT', 'related_doc_id': f'SKH-{quarter}-IR',
         'relation_type': 'same_announcement_alternate_publication',
         'evidence': 'Official IR PDF and official Newsroom HTML; different hash and format',
         'duplicate_decision': 'not_exact_duplicate'}
        for quarter in ('2025Q4', '2026Q1')
    ]
    write_csv('document_relations.csv', relations, list(relations[0]))

    coverage = read_csv('coverage_matrix.csv')
    trials = read_csv('access_trials.csv')
    regular = [row for row in manifest if row['source_id'] == 'DART']
    ir = [row for row in manifest if row['source_id'] in ('SAMSUNG_IR', 'SKH_IR')]
    primary = [row for row in parsed.values() if row['doc_id'] in {
        'SAM-2025-FY-DART', 'SKH-2025-FY-DART', 'SAM-2025Q4-IR', 'SAM-2026Q1-IR',
        'SKH-2025Q4-IR', 'SKH-2026Q1-IR'}]
    target_ids = {row['doc_id'] for row in regular + ir}
    target_trials = [row for row in trials if row['doc_id'] in target_ids]
    success = sum(row['status'] == 'downloaded' for row in target_trials)
    matched = sum(row['dart_status'] == 'listed' for row in coverage)
    source_counts = Counter(row['source_id'] for row in manifest)
    summary = f'''# P01 데이터 가능성 조사 — 현재 수집 결과

기준일: {date.today().isoformat()}. 이 문서는 API·HTTP 수집과 제한적 텍스트 추출의 **관측 결과**다. P01의 표 의미 감사와 제3자 재현 검토는 아직 끝나지 않았다.

## 확보와 분모

- OpenDART `corpCode.xml` 및 `company.json`에서 삼성전자 `00126380` (`005930`), SK하이닉스 `00164779` (`000660`)을 확인했다. [entities.csv](entities.csv), [company_overview.csv](company_overview.csv).
- `list.json` 정기공시 목록 원시 응답의 관련 행은 22건이다. 대상 20개 분기 칸에는 정기보고서가 각각 1건씩 매칭됐다({matched}/20). 나머지 2건은 2023년 사업보고서로 접수일만 범위 안에 들어온 대상 외 문서다. [dart_filings.csv](dart_filings.csv), [coverage_matrix.csv](coverage_matrix.csv).
- 기본 대상 40건 중 정기보고서 ZIP {len(regular)}건과 IR PDF {len(ir)}건을 다운로드했다. 고유 문서 접근 시험 성공률은 {success}/{len(target_trials)}이다. 이 비율은 **이번에 시도한 기본 대상**에만 적용한다. [access_trials.csv](access_trials.csv), [document_manifest.csv](document_manifest.csv).
- SK하이닉스 공식 발표 HTML 2건은 별도의 보조 문서이며 기본 40건의 분모에 포함하지 않는다. 동일 발표의 IR PDF와 HTML은 exact duplicate가 아니다. [document_relations.csv](document_relations.csv).
- 첫 6건은 모두 텍스트층을 읽을 수 있었다({len(primary)}/6). 이는 텍스트 관측이며 **표 머리글·단위 보존 또는 전체 본문 파싱 성공률**은 아니다. [parser_trials.csv](parser_trials.csv).

## API별 의미

OpenDART `corpCode.xml`은 회사 고유번호와 종목코드의 공식 대응을 준다. `company.json`은 공식 회사명과 종목코드를 재확인한다. `list.json`은 접수번호·보고서명·접수일을 주므로 대상 회계기간을 보고서명에서 따로 매칭했다. `document.xml`은 접수번호별 원본 ZIP을 준다. ZIP 안의 DART 문서는 엄격한 XML 파싱에서 오류가 발생했고, 파일럿에서는 `BeautifulSoup/lxml`로 텍스트를 관측했다.

`corpCode.xml`의 명칭(삼성전자·SK하이닉스)과 `company.json`의 정식명칭(삼성전자(주)·에스케이하이닉스(주))은 표기가 다르다. [entities.csv](entities.csv)에 둘을 별도 열로 보존했다. 이 명칭 차이를 다른 회사로 처리하지 않는다. `company.json`의 IR URL 필드는 두 회사 모두 빈 값이었다.

삼성 IR은 공식 PDF의 파일 시그니처와 표지의 연도·분기를 확인해 10건을 받았다. 삼성 실적발표 목록 HTML은 자동 요청에서 403이었으나 PDF 직접 접근은 성공했다. SK하이닉스는 공식 사이트가 사용하는 공개 `board/list` 응답에서 10건의 제목·행사일·첨부 경로를 받았고, 첨부 PDF를 확인했다. 이 사이트 API는 외부용 개발가이드가 확인되지 않아 경로 안정성은 추후 재점검한다. [sk_ir_list.csv](sk_ir_list.csv).

## 아직 검증할 것

1. 각 첫 6건에서 문단 1개와 숫자표 1개를 원문 위치와 대조해 숫자·단위·기간·삼성 메모리/DS 범위를 감사한다. 현재 `extraction_audit.csv`와 전체 `blocks.jsonl`은 미작성이다.
2. DART XML의 표 셀·머리글 관계, PDF 표 좌표와 페이지 번호, HTML 보일러플레이트 제거를 검사한다. 나머지 34개 기본 문서는 다운로드까지만 검증했다.
3. 발표 행사일과 문서 공개시점을 구분한다. SK 사이트 API의 행사 시각은 [sk_ir_list.csv](sk_ir_list.csv)에 원표현으로 남겼다. 정확한 PDF 공개시각을 임의로 만들지 않았으므로 IR manifest의 발표일/시각은 미상이다.
4. 원문 저장·공유·재배포 조건과 API 요청 한도를 출처별로 다시 확인한다. [source_registry.csv](source_registry.csv)의 미확인 항목은 허용으로 간주하지 않는다.
5. 정정본·번역본·후속 Q&A를 추가 탐색하고, 다른 사람이 manifest만으로 원문과 숫자표를 재확인하는 P01-T11 인계를 실시한다.

로컬 원문은 Git에서 제외한 `artifacts/p0/raw/`에 보관했다. API 키는 `.env`에서만 읽고 산출물에는 쓰지 않았다.

## 재현 순서

저장소 루트에서 아래 순서로 실행한다. 첫 명령은 목록과 초기 시험 산출물을 새로 쓰므로 이후 명령까지 이어서 실행한다.

```powershell
python scripts/p01_collect.py
python scripts/p01_fetch_regular.py
python scripts/p01_fetch_samsung_ir.py
python scripts/p01_fetch_skh_ir.py
python scripts/p01_inspect.py
python scripts/p01_finalize.py
python scripts/p01_verify.py
```
'''
    if not (OUT / 'block_validation.json').is_file():
        (OUT / 'data_feasibility.md').write_text(summary, encoding='utf-8')
    (OUT / 'scope.md').write_text('''# P01 범위

기업: 삼성전자 메모리(DS·전사 문맥 보존), SK하이닉스 연결·제품 범위. 기간: 2024Q1~2026Q2, 기업당 10개 분기. 기본 자료형: IR PDF와 정기보고서. Q1/Q3 분기보고서, Q2 반기보고서, Q4 사업보고서. 최초 6건은 두 기업의 2025Q4·2026Q1 IR와 2025 사업보고서 각 1건이다. 책임 역할: A 삼성, B SK하이닉스, C 기준·통합. 실명 배정 미확인.

기본 대상: 40건. SK 공식 발표 HTML 2건은 보조. KRX 시세·ECOS·GDELT·SEC EDGAR·ISC·리노공업·비공식 뉴스는 이번 기본 대상에서 제외한다. 원문은 `artifacts/p0/raw/`, 수집 결과는 `artifacts/p0/`에 둔다. 개별 URL과 접수번호는 `document_manifest.csv`에서 확인한다.
''', encoding='utf-8')
    print('Finalized:', len(manifest), 'manifest rows;', source_counts,
          'primary access:', f'{success}/{len(target_trials)}',
          'initial text observed:', f'{len(primary)}/6')


if __name__ == '__main__':
    main()
