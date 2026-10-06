"""Build the P04 contract and nonexpressive annotation packets, offline.

Only the two P03 release HTML revisions in the supplied manifest are parsed.
Original prose is never emitted. All outputs use exclusive creation.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import re
from decimal import Decimal
from pathlib import Path
from lxml import html
from p04_common import ROOT, OUT, SOURCE, REGISTRY, now, rows, sha, json_file, jsonl, write, require_stage

VERSION = '1.0.0-agent-pilot'
METRICS = {'Total revenue':'revenue','Operating income':'operating_income',
           'Net income':'net_income','Net cash from operations':'cfo',
           'Additions to property and equipment':'positive_cash_capex',
           'Total assets':'total_assets','Cash and cash equivalents':'cash_and_equivalents'}
SEGMENTS = {'Productivity and Business Processes':'US-MSFT-SEG-PBP',
            'Intelligent Cloud':'US-MSFT-SEG-IC','More Personal Computing':'US-MSFT-SEG-MPC'}

def schema_v1(base):
    s = copy.deepcopy(base)
    s['$id'] = 'urn:semi-auto-researching-corporate:us-equity:p04:1.0.0-agent-pilot'
    s['title'] = 'P04 agent pilot contract; human gold is absent'
    s['description'] = 'P02 v0.1 minimally extended for the observed P03 source cells and reporting membership.'
    s['properties']['schema_version'] = {'const':VERSION}
    st = {'type':'string','minLength':1}
    for name in ('guide_version','source_record_ref'):
        s['properties'][name] = st.copy(); s['required'].append(name)
    s['properties']['human_gold']={'const':False}; s['required'].append('human_gold')
    for name in ('event_normalized','relation_normalized'):
        d=s['$defs'][name]
        d['properties']['definition_version']=st.copy(); d['required'].append('definition_version')
        d['properties']['availability_dependencies']={'type':'array','items':{'type':'object','required':['record_id','available_at','availability_basis'],'properties':{'record_type':st,'record_id':st,'source_url':{'type':'string','format':'uri'},'published_date':{'type':'null'},'available_at':{'type':'string','format':'date-time'},'observed_at':{'type':'string','format':'date-time'},'availability_basis':{'const':'observed_conservative'},'reason':st},'additionalProperties':False}}
        d['required'].append('availability_dependencies')
    d=s['$defs']['event_normalized']
    for name in ('source_scale','source_numeric_value','sign_policy','occurrence_note'):
        d['properties'][name]=st.copy(); d['required'].append(name)
    s['$defs']['relation_normalized']['properties']['relation_type']['enum'].append('reports_segment')
    s['$defs']['relation_normalized'].setdefault('allOf',[]).append({'if':{'properties':{'relation_type':{'const':'reports_segment'}}},'then':{'properties':{'subject_role':{'const':'reporting_company'},'object_role':{'const':'reported_segment'},'direction':{'const':'subject_to_object'}}}})
    s['$defs']['provenance']['properties']['source_sha256']={'type':'string','pattern':'^[a-f0-9]{64}$'}
    s['$defs']['provenance']['required'].append('source_sha256')
    for name in ('source_parser_version','source_schema_version','source_normalization_revision_id'):
        s['$defs']['provenance']['properties'][name]=st.copy()
        s['$defs']['provenance']['required'].append(name)
    for name in ('source_evidence_status','source_period_start_derivation'):
        s['$defs']['raw']['properties'][name]=st.copy()
        s['$defs']['raw']['required'].append(name)
    s['$defs']['raw']['properties']['source_effective_period']={'anyOf':[{'type':'object','properties':{'start':{'type':'string','format':'date'},'end':{'type':'string','format':'date'}},'required':['start','end'],'additionalProperties':False},{'type':'null'}]}
    s['$defs']['raw']['required'].append('source_effective_period')
    return s

def period(f=None, unknown=False):
    if f is None:
        return dict(period_start=None,period_end=None,as_of_date=None,period_basis='unknown' if unknown else 'not_applicable',period_kind='unknown' if unknown else 'not_applicable',fiscal_year=None,fiscal_quarter=None,duration_days=None,missing_reason='not_disclosed' if unknown else 'not_applicable')
    instant=f['period_kind']=='instant'
    return dict(period_start=None if instant else f['period_start'],period_end=None if instant else f['period_end'],as_of_date=f['period_end'] if instant else None,period_basis='fiscal',period_kind=f['period_kind'],fiscal_year=f['fiscal_year'],fiscal_quarter=f['fiscal_quarter'],duration_days=None if instant else f['period_duration_days'],missing_reason=None)

def build(out=OUT):
    require_stage(1)
    output_names=['event_schema_v1.json','contract_records.jsonl','evidence_index.jsonl','source_packets.jsonl','annotation_reference.json','schema_migration.md','contract_build_manifest.json']
    for name in output_names:
        if (out/name).exists(): raise FileExistsError(f'Refusing to overwrite {out/name}')
    stamp=now()
    source_manifest=SOURCE/'document_manifest_v0_3.csv'
    docs={x['doc_id']:x for x in rows(source_manifest)}
    facts=rows(REGISTRY/'applied_002/normalized_claims.jsonl')
    relations=rows(REGISTRY/'business_relations.jsonl')
    links={x['item_id']:x for x in rows(OUT/'event_claim_links.csv')}
    catalog={x['metric_id']:x for x in rows(REGISTRY/'metric_catalog.csv')}
    trees={}
    for doc_id in {x['doc_id'] for x in facts}:
        d=docs[doc_id]; path=ROOT/d['storage_uri']
        assert sha(path)==d['sha256'], 'source revision changed'
        trees[doc_id]=html.fromstring(path.read_bytes())
    evidence={}

    def ev(f,xpath,kind,selected=None,start=None,end=None,headers=()):
        tree=trees[f['doc_id']]; found=tree.xpath(xpath)
        assert len(found)==1, 'ambiguous source location'
        original=found[0].text_content()
        if selected is None:
            selected=original.strip(); start=original.index(selected); end=start+len(selected)
        elif start is None:
            start=original.index(selected); end=start+len(selected)
        assert original[start:end]==selected
        if kind=='numeric_value': assert re.fullmatch(r'[\d,$().+\-]+',selected)
        elif kind=='unit': assert selected=='millions'
        elif kind=='row_label': assert ' '.join(selected.split()) in set(METRICS)|set(SEGMENTS)
        elif kind in ('period_header','year_header'):
            assert re.fullmatch(r'[\s\d,()/A-Za-z.\-]+',selected) and len(selected)<100
        key='EV-'+hashlib.sha256((f['revision_id']+'|'+xpath+'|'+str(start)+'|'+str(end)).encode()).hexdigest()[:20]
        item=dict(evidence_id=key,doc_id=f['doc_id'],revision_id=f['revision_id'],block_id=None,location_type='table_cell',location=xpath,location_status='verified',start=start,end=end,offset_unit='unicode_code_point',offset_interval='0-based-[start,end)',offset_mapping='identity',selected_text=selected,table_id=f['table_xpath'],row_index=f['table_row_index'] if kind in ('numeric_value','row_label') else None,col_index=f['table_col_index'] if kind=='numeric_value' else 0 if kind=='row_label' else None,header_refs=list(headers),note_refs=[])
        evidence[key]={**item,'evidence_kind':kind,'source_sha256':docs[f['doc_id']]['sha256']}
        return item

    def material(f):
        h=[ev(f,f[k+'_pointer'],k) for k in ('period_header','year_header')]
        h.append(ev(f,f['unit_header_pointer'],'unit','millions'))
        node=trees[f['doc_id']].xpath(f['evidence_pointer'])[0]
        row=node.getparent(); label=row.xpath('./th|./td')[0]
        label_ev=ev(f,label.getroottree().getpath(label),'row_label')
        value=ev(f,f['evidence_pointer'],'numeric_value',f['value_raw'],f['value_span_start'],f['value_span_end'],[x['evidence_id'] for x in h]+[label_ev['evidence_id']])
        return value,h,label_ev

    records=[]; packets=[]; facts_by_id={f['claim_id']:f for f in facts}
    for source in [*facts,*relations]:
        is_relation='relation_id' in source
        f=facts_by_id[source['claim_id']]
        d=docs[f['doc_id']]
        item_id=source['relation_id'] if is_relation else f['claim_id']; link=links[item_id]
        value,headers,label=material(f)
        evidence_items=[label,*headers] if is_relation else [value,label,*headers]
        raw_label=' '.join(label['selected_text'].split())
        t=dict(published_at=None,published_date=d['published_date'],time_precision='date',timezone=None,utc_offset=None,publication_evidence_refs=[d['doc_id']+':'+d['published_date_evidence']],reference_period=period(f),effective_period=period(unknown=is_relation),observed_at=d['observed_at'],available_at=None,availability_policy='date_only_boundary',availability_evidence_refs=[d['doc_id']+':publication_date'],date_conflict_status='none_observed')
        common=dict(company_id='US-MSFT',scope_id=f['scope_id'],modality='actual_reported',negation=False,conditions=[],temporal=t,evidence_status='company_reported',extraction_status='partial',field_missing_reasons={'published_at':'not_disclosed'},definition_version=f['definition_version'],availability_dependencies=copy.deepcopy(f['availability_dependencies']))
        if is_relation:
            normalized={**common,**{k:source[k] for k in ('relation_type','subject_entity_id','object_entity_id','subject_role','object_role','product_service_ids','valid_from','valid_to','speaker')},'direction':'subject_to_object','entity_refs':[source['subject_entity_id'],source['object_entity_id']],'prior_relation_id':None,'uncertainty_reason':'reporting_membership_only; effective business dates not disclosed in selected table'}
            normalized['field_missing_reasons'].update(valid_from='not_disclosed',valid_to='not_disclosed',effective_period='not_disclosed',prior_relation_id='not_yet_checked')
        else:
            normalized={**common,'event_type':'financial_result','product_id':None,'actor':'US-MSFT','entity_refs':['US-MSFT']+([f['scope_id']] if f['scope_id'] in SEGMENTS.values() else []),'relation_refs':[r['relation_id'] for r in relations if r['claim_id']==f['claim_id']], 'metric_id':f['metric_id'],'metric_mapping_candidates':[],'numeric_value':f['numeric_value'],'value_kind':'point','lower':None,'upper':None,'missing_reason':None,'direction':'not_applicable','canonical_unit':'USD','currency':'USD','scale':'1','accounting_basis':'GAAP','adjustment_definition':None,'consolidation':f['consolidation'],'financial_context':dict(statement_type=f['statement_type'],balance_or_flow=f['balance_or_flow'],period_duration=None if f['period_kind']=='instant' else f['period_duration_days'],note_refs=[],concept_ids=catalog[f['metric_id']]['concept_ids'].split(';'),adjustment_component_refs=[]),'comparison_basis':'none','denominator':None,'prior_claim_id':None,'prior_state_status':'not_yet_checked','source_scale':f['source_scale'],'source_numeric_value':f['source_numeric_value'],'sign_policy':f['sign_policy'],'occurrence_note':f['occurrence_note']}
            normalized['field_missing_reasons'].update(product_id='not_applicable',adjustment_definition='not_applicable',denominator='not_applicable',prior_claim_id='not_yet_checked')
            # P03 uses cash_flow_statement, while the preserved P02 enum is cash_flow.
            if normalized['financial_context']['statement_type']=='cash_flow_statement':
                normalized['financial_context']['statement_type']='cash_flow'
            # Preserve the parsed source sign before capex's positive-outflow mapping.
            normalized['source_numeric_value']=str(Decimal(f['value_raw'].replace(',','').replace('$','').replace('(','-').replace(')','')))
        ref=('artifacts/us_equity/p2/business_relations.jsonl#'+item_id) if is_relation else ('artifacts/us_equity/p2/applied_002/normalized_claims.jsonl#'+item_id)
        record=dict(schema_version=VERSION,record_kind='business_relation' if is_relation else 'event_claim',record_id='P04-'+item_id,record_revision_id='P04-'+item_id+'-R1',claim_id=f['claim_id'],claim_revision_id=f['claim_id']+'-p03-factual-reference-0.3',event_id=link['event_id'],event_family_id=link['event_family_id'],relation_id=source['relation_id'] if is_relation else None,relation_revision_id=source['relation_revision_id'] if is_relation else None,example_kind='source_supported',annotation_status='agent_draft',exposure_status='adaptation',registry_version='us-p2-0.1.0',model_version=None,run_id='p04-contract-20261006',supersedes_record_id=None,follow_up_of_family_id=None,guide_version='p04-annotation-guide-v1',source_record_ref=ref,human_gold=False,provenance=dict(doc_id=f['doc_id'],revision_id=f['revision_id'],source_id=d['source_id'],source_url=d['source_url'],final_url=d['final_url'],rights_basis_ref='artifacts/us_equity/p0/available_20261005/'+d['rights_basis_ref'],rights_check_status='verified_for_this_use',storage_policy='conditional',ai_input_policy='unresolved',external_transfer_policy='prohibited',source_sha256=d['sha256'],evidence=evidence_items),raw=dict(claim_text=None,action_raw=None,metric_raw=None if is_relation else raw_label,value_raw=None if is_relation else f['value_raw'],unit_raw=None if is_relation else 'millions',line_item_raw=raw_label,speaker_raw=None,time_raw=[h['selected_text'] for h in headers[:2]],source_effective_period=source['effective_period'] if is_relation else None),normalized=normalized,assessment=dict(assessment_id='ASSESS-P04-'+item_id,author_id='p04-contract-mapper',author_kind='agent_draft',created_at=stamp,as_of=stamp,review_readiness='needs_review',readiness_reasons=['independent_human_annotation_not_observed','selected_table_cells_only']+(['segment_definition_policy_unresolved'] if f['scope_id'] in SEGMENTS.values() else ['scope_corroboration_is_2026_current_only']),uncertainty_reason='Source table support is limited; no independent human review or full-body audit.',questions=[],business_financial_interpretation=None),derived=[])
        record['raw'].update(source_evidence_status=source['evidence_status'],source_period_start_derivation=f['period_start_derivation'])
        record['provenance'].update(source_parser_version=d['parser_version'],source_schema_version=f['schema_version'],source_normalization_revision_id=f['normalization_revision_id'])
        missing=record['normalized']['field_missing_reasons']
        missing['temporal.published_at']=missing.pop('published_at')
        missing.update({'temporal.available_at':'not_disclosed','temporal.timezone':'not_disclosed','temporal.utc_offset':'not_disclosed'})
        if 'effective_period' in missing: missing['temporal.effective_period']=missing.pop('effective_period')
        record['normalized']['temporal']['date_conflict_status']='not_yet_checked'
        if not is_relation:
            record['derived']=[dict(calculation_id='CALC-'+item_id,formula_id='positive_outflow_then_scale' if f['sign_policy']=='outflow_to_positive' else 'preserve_sign_then_scale',formula_version='1.0',input_refs=[value['evidence_id'],headers[2]['evidence_id']],output=f['numeric_value'],output_unit='USD',calculation_status='computed',missing_inputs=[],rounding_policy='exact_decimal_no_rounding',calculated_at=stamp,prepared_by='p04-contract-mapper',reviewed_by=None,model_output_seen_before_work=True)]
        records.append(record)
        raw_cell=trees[f['doc_id']].xpath(f['evidence_pointer'])[0].text_content()
        assert re.fullmatch(r'[\s\d,$().+\-]+',raw_cell)
        packets.append(dict(item_id=item_id,item_type=link['item_type'],source_claim_id=f['claim_id'],source_relation_id=source['relation_id'] if is_relation else None,source_record_ref=ref,doc_id=f['doc_id'],revision_id=f['revision_id'],source_sha256=d['sha256'],event_id=link['event_id'],event_family_id=link['event_family_id'],publication={k:t[k] for k in ('published_date','published_at','time_precision','observed_at')},raw=dict(value_cell=None if is_relation else raw_cell,metric_label='segment revenue' if raw_label in SEGMENTS else raw_label,scope_label=raw_label if raw_label in SEGMENTS else 'company financial statement total',period_header=headers[0]['selected_text'],year_header=headers[1]['selected_text'],unit_header=headers[2]['selected_text'],row_label=label['selected_text']),evidence_refs=[x['evidence_id'] for x in evidence_items],source_presentation_id=f['doc_id'],scope_dependency_refs=[x['record_id'] for x in f['availability_dependencies']],packet_policy='nonexpressive_raw_references_no_normalized_answers'))
    base=json.loads((ROOT/'artifacts/us_equity/p1/event_schema_v0.1.json').read_text(encoding='utf-8'))
    json_file(out/'event_schema_v1.json',schema_v1(base))
    jsonl(out/'contract_records.jsonl',records); jsonl(out/'evidence_index.jsonl',evidence.values()); jsonl(out/'source_packets.jsonl',packets)
    json_file(out/'annotation_reference.json',dict(version='p04-reference-1',company_id='US-MSFT',company_name='Microsoft Corporation',company_scope_id='US-MSFT-CONSOLIDATED',metric_label_to_id=METRICS,segment_label_to_entity_id=SEGMENTS,segment_table_metric_id='revenue',fiscal_calendar={'year_end_month':6,'year_end_day':30,'annual_start':'previous year July 1','Q4_start':'same year April 1'},scope_dependencies=[dict(record_id=x['doc_id'],published_date=x['published_date'] or None,observed_at=x['observed_at'],sha256=x['sha256'],use_policy='current-only scope corroboration; not available at release cutoff') for x in docs.values() if x['document_kind']!='earnings_press_release'],derived_rules=['USD millions multiply by 1000000 exactly','parentheses denote negative raw value','cash PP&E additions outflows map to positive cash capex by negation','instant uses as_of_date and null duration','segment presentation definition follows source release year, including comparative columns'],label_status='agent_reference_not_gold'))
    write(out/'schema_migration.md',f'''# P04 contract migration

P02 v0.1 schema hash `{sha(ROOT/'artifacts/us_equity/p1/event_schema_v0.1.json')}` is preserved. P04 `{VERSION}` retains raw/normalized/assessment/derived and adds explicit source hash, source record reference, guide version, false human_gold, definition_version and availability dependencies. reports_segment is a directed company → reported segment relation with fixed roles.

33 numeric source claims produce 33 event_claim records. Six reporting relations reference six of those same claim IDs and produce six distinct business_relation records. Thus records=39, unique source claims=33, families/events=2; record_id is the primary key, never claim_id alone.

Original values, signs and source scale are retained. Normalized monetary values use base USD scale=1. Derived calculation records disclose exact scale/sign conversion and prior model output exposure. Balance observations use as_of_date and null duration; source duration zero is not a zero-day flow. Evidence offsets are original DOM-cell Unicode code points, 0-based [start,end), with independent period/year/unit/row-header references.

Initial self-validation found eight cash-flow rows whose P03 cash_flow_statement value was outside the P02 cash_flow enum, and four capex rows whose upstream source_numeric_value had already been made positive. The initial artifacts are preserved in contract_revisions/initial. The mapper now uses cash_flow and parses source_numeric_value directly from the signed raw token; positive capex remains a separate derived/normalized value. All initial failures remain in contract_validation_initial.json.

Cross-review added raw.source_evidence_status to preserve company_reported_unaudited/company_reported_table, raw.source_period_start_derivation for header-derived calendar starts, source parser/schema/normalization revisions, and fully qualified temporal missing-reason paths. Normalized company_reported means source attribution only. date_conflict_status is not_yet_checked because manifest consistency does not constitute a full independent publication-date conflict audit. The earlier passing implementation is preserved in contract_revisions/before_cross_review.

Publication dates remain date-only, published_at/available_at/timezone/UTC offset are null. source publication refs use manifest locations; no exact time is invented. Annual-report scope support has only 2026 observation availability, recorded separately from release publication. The mapper assessment is current-as-of. Release-cutoff judgments must exclude that supplemental support.

P03 relation effective_period merely copied the financial reporting period. P04 moves it to temporal.reference_period and preserves the original in raw.source_effective_period. Effective business period, valid_from and valid_to remain unknown/not_disclosed. Reports_segment cannot establish business-effect magnitude, customer/supply relationships or segment policy details.

source_packets contains selected raw numeric/period/year/unit/standard-label references, with no mapped normalized answers. annotation_reference supplies common ID and calendar rules. These are existing adaptation documents, not blind test sources. Reserved FY2026 Q1 content is never read by this builder.

All 39 records are agent_draft; independent human annotation, human gold and full-body audit remain absent. Outputs are exclusively created; rerun into a fresh --output-dir.
''')
    json_file(out/'contract_build_manifest.json',dict(created_at=stamp,source_manifest=str(source_manifest.relative_to(ROOT)),source_manifest_sha256=sha(source_manifest),schema_version=VERSION,source_numeric_claims=len(facts),relation_records=len(relations),record_count=len(records),evidence_count=len(evidence),packet_count=len(packets),input_paths=[str(p.relative_to(ROOT)) for p in [REGISTRY/'applied_002/normalized_claims.jsonl',REGISTRY/'business_relations.jsonl',OUT/'event_claim_links.csv']],original_prose_exported=False,reserved_content_opened=False,outputs={n:sha(out/n) for n in output_names if n!='contract_build_manifest.json'}))
    return {'records':len(records),'evidence':len(evidence),'packets':len(packets)}

if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--output-dir',type=Path,default=OUT)
    print(json.dumps(build(parser.parse_args().output_dir)))
