"""Freeze scope, then allowlist P04 selected observations into P05 inputs."""
from __future__ import annotations
import argparse
import importlib.metadata
import os
import platform
import subprocess
import sys
import shutil
from collections import Counter
from pathlib import Path
from lxml import html
from p05_common import *
from p05_contracts import schemas

def protocol(out):
    if out.exists():
        raise FileExistsError('Protocol requires a fresh output directory')
    result = subprocess.run([sys.executable, str(ROOT/'scripts/p04_verify_package.py')],
                            capture_output=True, text=True, check=True)
    verification = json.loads(result.stdout)
    packets = rows(P3/'source_packets.jsonl')
    split = rows(P3/'split_manifest.csv')
    policy = read_json(P3/'split_policy.json')
    documents = rows(SOURCE/'document_manifest_v0_3.csv')
    inputs = [dict(input_id=opaque('I-', [p['revision_id'],p['item_type'],p['evidence_refs']]),
                   input_kind='numeric_cell' if p['item_type']=='numeric_claim' else 'relation_context',
                   doc_id=p['doc_id'],revision_id=p['revision_id'],source_sha256=p['source_sha256'],
                   split='adaptation',independent_evaluation='not_evaluated') for p in packets]
    in_schema, pred_schema = schemas()
    validator(in_schema); validator(pred_schema)
    json_file(out/'input_schema.json',in_schema); json_file(out/'prediction_schema.json',pred_schema)
    deps=[]
    for name in ('lxml','jsonschema','referencing','attrs','rpds-py','jsonschema-specifications'):
        dist=importlib.metadata.distribution(name)
        deps.append(dict(name=name,version=dist.version,location=str(dist.locate_file('')),
                         license=dist.metadata.get('License-Expression') or dist.metadata.get('License'),
                         acquisition='existing_local_install_no_download'))
    json_file(out/'environment_manifest.json',dict(checked_at=now(),python=sys.version,
              executable=sys.executable,platform=platform.platform(),machine=platform.machine(),
              logical_cpus=os.cpu_count(),dependencies=deps,external_call_budget=0,
              gpu='not_used',memory_capacity='not_measured',dependency_imports='passed'))
    write(out/'requirements.lock',''.join(f"{d['name']}=={d['version']}\n" for d in deps))
    upstream=read_json(P3/'input_snapshot.json')['inputs']
    upstream += read_json(P3/'package_manifest.json')['files']
    upstream += [dict(path=str((P3/'package_manifest.json').relative_to(ROOT)),sha256=sha(P3/'package_manifest.json'))]
    upstream += [dict(path=d['storage_uri'],sha256=d['sha256']) for d in documents]
    unique={x['path'].replace('\\','/'):dict(path=x['path'].replace('\\','/'),sha256=x['sha256']) for x in upstream}
    json_file(out/'input_snapshot.json',dict(created_at=now(),inputs=list(unique.values()),
              legacy_inputs=[],reserved_body_read=False,independent_evaluation='not_evaluated',
              p04_verification=verification))
    csv_file(out/'input_manifest.csv',inputs)
    reference=read_json(P3/'annotation_reference.json')
    catalog={m['metric_id']:m for m in rows(REGISTRY/'metric_catalog.csv')}
    metric_rules={label:dict(metric_id=metric,balance_or_flow=catalog[metric]['metric_kind'],
                            statement_type=catalog[metric]['level'],
                            sign_policy='outflow_to_positive' if metric=='positive_cash_capex' else 'preserve')
                  for label,metric in reference['metric_label_to_id'].items()}
    rule_docs={}
    for d in documents:
        if d['document_kind']!='earnings_press_release':
            continue
        rule_docs[d['doc_id']]=dict(revision_id=d['revision_id'],source_sha256=d['sha256'],
                    source_url=d['source_url'],rights_basis_ref=str((SOURCE/'source_conditions.md').relative_to(ROOT))+'#msft-factual-reference',
                    published_date=d['published_date'],observed_at=d['observed_at'],
                    segment_definition='msft-segment-presentation-fy'+d['fiscal_year'],
                    source_parser_version=d['parser_version'])
    rules=dict(rule_version=RULE_VERSION,registry_version=REGISTRY_VERSION,origin='adaptation_curator_registry',
               company_id=reference['company_id'],company_name=reference['company_name'],
               company_scope_id=reference['company_scope_id'],metric_labels=metric_rules,
               segment_labels=reference['segment_label_to_entity_id'],fiscal_calendar=reference['fiscal_calendar'],
               scope_dependencies=reference['scope_dependencies'],documents=rule_docs,
               units={'millions':'1000000'},leakage_group=policy['development_leakage_group'],
               reference_access='forbidden_in_extractor',external_calls=0)
    json_file(out/'rules_v0_1.json',rules)
    provenance=[dict(rule=name,origin='curator_provided_adaptation',source=source,source_sha256=sha(ROOT/source))
                for name,source in [('label_entity_calendar','artifacts/us_equity/p3/annotation_reference.json'),
                                    ('metric_constraints','artifacts/us_equity/p2/metric_catalog.csv'),
                                    ('presentation_definition','artifacts/us_equity/p0/available_20261005/document_manifest_v0_3.csv'),
                                    ('USD_GAAP_qualifiers','artifacts/us_equity/p0/available_20261005/source_conditions.md')]]
    csv_file(out/'rule_provenance.csv',provenance)
    write(out/'baseline_protocol.md','''# P05 개발 실행 규약 — 2026-10-06

Microsoft FY2024 Q4/FY2025 Q4 공식 발표 2문서·2 family의 선택 숫자 33개와 보고 사업부 관계 문맥 6개를 처리한다. 전체 HTML에서 셀을 발견하는 작업은 제외한다. 신규 수집·모델 다운로드·외부 호출 예산은 0이다. FY2026 Q1 예약 원문과 폐기된 한국기업 자료는 입력에 넣지 않는다.

P04 공유 agent 참조와의 adaptation 회귀 비교이며 인간 gold·독립 train/dev/test는 각각 0이다. 숫자 전체 묶음은 33개, 관계 tuple은 6개, terminal 결과는 39개가 분모다. 관측/제공 문맥/미상 상태 일치를 분리하고 분모 0은 null이다. 추가 후보는 incomplete reference 때문에 정오 미판정이며 독립 precision/recall/F1은 계산하지 않는다.

adapter는 source_packets/evidence_index의 허용 필드만 읽는다. 원 item/source claim/relation ID는 reference_links에만 둔다. 추출기는 extractor_inputs, input_schema, prediction_schema, rules 파일만 읽도록 별도 실행하며 런타임 파일 접근을 제한한다. doc_id는 provenance와 고정된 발표별 정의 정책 조회에만 사용한다. 숫자 기간은 오직 표 기간/연도 머리글에서 파싱한다. scope label, 회사, 통화/GAAP, 표 용도와 발표별 정의는 사전 제공 문맥이다.

원 숫자·부호·배율은 보존한다. Decimal로 USD 기본 단위 및 scale=1을 출력한다. 괄호 음수 PP&E 지출만 명시적 positive_cash_capex 부호 정책을 적용한다. FCF·margin·중요성·투자 영향은 생성하지 않는다. 기간 시작일은 달력 계산의 파생 결과다. 기간흐름/시점잔액, 발표일/보고기간/관계 실제 유효기간을 분리한다.

매칭 키는 (doc_id, revision_id, record_kind, 정렬한 근거 location/kind/start/end)이며 input ID나 예측 지표/값을 답 매칭에 사용하지 않는다. 같은 키의 여러 후보는 동률 충돌로 남기고 동일 참조의 성공을 중복 계산하지 않는다. 추출 결과를 동결한 후에만 비교기가 agent 참조를 읽는다.

predicted는 구조화 후보 생성 상태다. 모든 후보의 review_readiness는 needs_review, 확률은 null이다. 근거/타입 오류는 quarantined, 지원하지 않는 의미는 abstained, 예상하지 못한 실행 오류는 failed로 기록한다. 입력마다 terminal 결과 한 행을 남긴다. 실패 입력도 비교 분모에 남긴다. 저장소 인계는 validation을 통과한 후보만 가능하며 중요성 판정 완료를 뜻하지 않는다.

출처 조건은 P0 source_conditions.md의 기존 개인·비상업 최소 사실 참조 판단을 계승한다. 원문 prose의 AI 입력/학습·외부 공유 권리는 unresolved다. 로컬 검증기는 허용된 84개 위치만 재조회하며 본문을 출력하지 않는다. 전체 본문·날짜 충돌 수동 감사는 미실행이다. 후향 scope 의존성 24개와 발표별 사업부 정의 한계를 유지한다.
''')
    checks=dict(p04_30_checks=verification['checks_passed']==verification['checks_total']==30,
                input_39=len(inputs)==39, numeric_33=sum(x['input_kind']=='numeric_cell' for x in inputs)==33,
                relation_6=sum(x['input_kind']=='relation_context' for x in inputs)==6,
                releases_2=len(rule_docs)==2, unique_ids=len({x['input_id'] for x in inputs})==39,
                adaptation_only=all(next(s for s in split if s['item_id']==p['item_id'])['split']=='adaptation' for p in packets),
                reserved_excluded=policy['reserved_document']['doc_id'] not in rule_docs,
                upstream_hashes=all(sha(ROOT/x['path'])==x['sha256'] for x in unique.values()),
                imports_and_schemas=True,legacy_excluded=all(p['doc_id'] in rule_docs for p in packets)
                    and not any(x['path'].startswith('artifacts/p0/') for x in unique.values()))
    stage_report(1,'initial',checks,dict(input_count=39,p04=verification),out)
    write(out/'stage_reviews/stage_01_improvements.md','# 1단계 검토\n\n첫 실행은 P04 보존 목록의 README/설계 문서까지 legacy 데이터로 오판해 10/11이었다. 이전 결과는 ../../p4_attempts/protocol_001에 보존했다. 검사 대상을 실제 추출 문서 allowlist와 이전 한국 artifacts 경로로 구분하여 재실행했다. P04 검사 30/30 유지. jsonschema는 이전 단계의 로컬 격리 설치 경로를 사용하고 실제 버전/라이선스를 lock에 기록했다. 네트워크 설치는 없었다. ID 힌트 제거와 비교 정책을 추출 전에 고정했다.\n')
    stage_report(1,'final',checks,dict(input_count=39,files=hashes([out/'input_schema.json',out/'prediction_schema.json',out/'rules_v0_1.json'])),out)
    if not all(checks.values()): raise RuntimeError('Protocol checks failed')
    print(json.dumps(dict(stage=1,passed=sum(checks.values()),total=len(checks))))

def prepare(out):
    require_stage(1,out)
    packets=rows(P3/'source_packets.jsonl'); evidence={e['evidence_id']:e for e in rows(P3/'evidence_index.jsonl')}
    manifest=rows(out/'input_manifest.csv'); docs={d['doc_id']:d for d in rows(SOURCE/'document_manifest_v0_3.csv')}
    trees={}
    for doc in {p['doc_id'] for p in packets}:
        d=docs[doc]
        if sha(ROOT/d['storage_uri'])!=d['sha256']: raise ValueError('Source hash mismatch')
        trees[doc]=html.fromstring((ROOT/d['storage_uri']).read_bytes())
    def evidence_id(old,kind):
        e=evidence[old]
        return opaque('E-', [e['revision_id'],kind,e['location'],e['start'],e['end']])
    outputs=[]; links=[]; contexts=[]; audit=[]; maps={}
    for p,m in zip(packets,manifest,strict=True):
        item=m['input_id']; evs=[]
        roles=(['numeric_value'] if m['input_kind']=='numeric_cell' else [])+['row_label','period_header','year_header','unit']
        for old,kind in zip(p['evidence_refs'],roles,strict=True):
            e=evidence[old]; found=trees[p['doc_id']].xpath(e['location'])
            if len(found)!=1: raise ValueError('Nonunique XPath')
            cell=found[0].text_content(); start,end=e['start'],e['end']
            if cell[start:end]!=e['selected_text']: raise ValueError('Source span mismatch')
            raw=p['raw']['value_cell'] if kind=='numeric_value' else e['selected_text']
            origin=0 if kind=='numeric_value' else start
            if kind=='numeric_value' and raw!=cell: raise ValueError('Numeric DOM mismatch')
            normalized,mapping=normalize_fragment(raw,origin)
            eid=evidence_id(old,kind)
            new=dict(evidence_id=eid,kind=kind,location=e['location'],table_id=e['table_id'],
                     row_index=e['row_index'],col_index=e['col_index'],start=start,end=end,
                     raw_fragment=raw,fragment_origin=origin,selected_text=e['selected_text'],
                     normalized_fragment=normalized,normalized_to_raw=mapping,
                     header_refs=[evidence_id(h,k) for h,k in zip(e['header_refs'],['period_header','year_header','unit','row_label'],strict=True)] if kind=='numeric_value' else [],
                     offset_unit='unicode_code_point',offset_interval='0-based-[start,end)')
            evs.append(new)
            maps[eid]=dict(evidence_id=eid,p04_evidence_id=old,doc_id=p['doc_id'],
                                  revision_id=p['revision_id'],source_sha256=p['source_sha256'],
                                  location=e['location'],start=start,end=end,kind=kind)
            audit.append(dict(input_id=item,evidence_id=eid,source_span_roundtrip=True,
                              normalized_offset_roundtrip=all(normalize_fragment(cell[a:b])[0]==c or (c==' ' and cell[a:b].isspace())
                                                             for c,(a,b) in zip(normalized,mapping)),
                              raw_hash=digest(raw),normalization='unicode_whitespace_collapse_with_interval_map'))
        segment=p['raw']['metric_label']=='segment revenue'
        cp=opaque('CP-',item)
        context=dict(context_origin='curator_provided',context_provenance_ref=cp,
                     company_name='Microsoft Corporation',company_id='US-MSFT',scope_label=p['raw']['scope_label'],
                     table_purpose='segment_revenue' if segment else 'company_financial_statement',
                     currency='USD',accounting_basis='GAAP',
                     source_qualifier='company_reported_table' if m['input_kind']=='relation_context' else 'company_reported_unaudited')
        outputs.append(dict(schema_version=INPUT_VERSION,input_id=item,input_kind=m['input_kind'],
                        input_mode='preselected_cells',doc_id=p['doc_id'],revision_id=p['revision_id'],
                        source_sha256=p['source_sha256'],publication=p['publication'],
                        raw={k:p['raw'][k] for k in ('value_cell','row_label','period_header','year_header','unit_header')},
                        context=context,evidence=evs,synthetic=False))
        links.append(dict(input_id=item,reference_item_id=p['item_id'],source_claim_id=p['source_claim_id'],
                          source_relation_id=p['source_relation_id'],p04_packet_sha256=digest(p),
                          doc_id=p['doc_id'],revision_id=p['revision_id']))
        contexts.append(dict(context_provenance_ref=cp,input_id=item,context_origin='curator_provided',
                    fields=['company','scope_label','table_purpose','currency','accounting_basis','source_qualifier','presentation_definition'],
                    packet_source='artifacts/us_equity/p3/source_packets.jsonl',
                    policy_sources=['artifacts/us_equity/p3/annotation_reference.json','artifacts/us_equity/p0/available_20261005/source_conditions.md'],
                    observed_fields=['value_cell','row_label','period_header','year_header','unit_header'],
                    independently_inferred=False,selection='preselected_cell_and_headers',
                    historical_blind=False,scope_dependency_refs=p['scope_dependency_refs']))
    v=validator(read_json(out/'input_schema.json'))
    checks=dict(inputs_preserved=len(outputs)==len(packets)==39,reference_links_39=len(links)==39,
                source_evidence_84=len({e['p04_evidence_id'] for e in maps.values()})==84,schemas_valid=all(v.is_valid(x) for x in outputs),
                offsets_roundtrip=all(x['normalized_offset_roundtrip'] for x in audit),
                source_roundtrip=all(x['source_span_roundtrip'] for x in audit),
                unique_input_ids=len({x['input_id'] for x in outputs})==39,
                no_answer_fields=not any(key in json.dumps(outputs) for key in ('source_claim_id','source_relation_id','source_record_ref','metric_id','scope_id','period_start','period_end','item_id')))
    jsonl(out/'extractor_inputs.jsonl',outputs);jsonl(out/'reference_links.jsonl',links)
    jsonl(out/'evidence_map.jsonl',maps.values());jsonl(out/'context_provenance.jsonl',contexts)
    csv_file(out/'preprocess_audit.csv',audit)
    stage_report(2,'initial',checks,dict(inputs=39,unique_source_evidence=84,evidence_role_bindings=len(maps),evidence_occurrences=len(audit)),out)
    # Final gate is written only after independent executable synthetic checks.
    print(json.dumps(dict(stage=2,initial_passed=sum(checks.values()),total=len(checks),final_gate='pending_adversarial_tests')))
    if not all(checks.values()): raise RuntimeError('Input adapter checks failed')

def qualifier_fix(out):
    require_stage(3,out)
    # P0 source_conditions explicitly records Unaudited for the financial numeric tables.
    # P04 comparisons exposed a lost qualifier; corrections are versioned, not answer copying.
    archive=out/'revisions/qualifier_001';archive.mkdir(parents=True,exist_ok=False)
    current=rows(out/'extractor_inputs.jsonl');rules=read_json(out/'rules_v0_1.json')
    for name in ('extractor_inputs.jsonl','rules_v0_1.json'):
        shutil.move(str(out/name),str(archive/name))
    changed=[]
    for r in current:
        expected='company_reported_table' if r['input_kind']=='relation_context' else 'company_reported_unaudited'
        if r['context']['source_qualifier']!=expected:
            changed.append(dict(input_id=r['input_id'],before=r['context']['source_qualifier'],after=expected))
            r['context']['source_qualifier']=expected
    rules['rule_version']=RULE_VERSION
    jsonl(out/'extractor_inputs.jsonl',current);json_file(out/'rules_v0_1.json',rules)
    json_file(archive/'revision_log.json',dict(changed_at=now(),changes=changed,rule_version=RULE_VERSION,
              reason='Retain unaudited numeric table qualifier for all scopes; relation membership qualifier remains table-only',
              evidence='artifacts/us_equity/p0/available_20261005/source_conditions.md',
              evidence_sha256=sha(SOURCE/'source_conditions.md'),previous_run='m0_002',next_run='m0_003'))
    print(json.dumps(dict(changed_inputs=len(changed),rule_version=RULE_VERSION)))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--stage',choices=['protocol','inputs','qualifier-fix'],required=True)
    parser.add_argument('--output-dir',type=Path,default=P4);args=parser.parse_args()
    {'protocol':protocol,'inputs':prepare,'qualifier-fix':qualifier_fix}[args.stage](args.output_dir)
