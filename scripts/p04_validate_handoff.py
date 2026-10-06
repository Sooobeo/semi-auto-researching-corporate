"""Validate the two deliberately different numeric representations at handoff."""
from __future__ import annotations
import argparse
import copy
from decimal import Decimal, InvalidOperation
from p04_common import *

def check(records, contracts, annotations, evidence, docs, metrics, entities, scopes):
    errors=[]
    indexed={r['relation_id'] or r['claim_id']:r for r in contracts}
    if len(records)!=len(indexed) or len({r['item_id'] for r in records})!=len(records):errors.append('item_cardinality')
    for r in records:
        item=r['item_id']; f=r['facts']; c=indexed.get(item)
        def fail(name):errors.append(item+':'+name)
        if c is None:fail('unknown_item');continue
        n=c['normalized']; d=docs.get(f.get('doc_id'))
        if r.get('human_gold') is not False or r.get('status')!='reviewed_agent_draft':fail('human_gold_overclaim')
        if r.get('split')!='adaptation':fail('development_exposure')
        if not d or r['provenance']['doc_sha256']!=d['sha256']:fail('document_provenance')
        if f['company_id'] not in entities or f['scope_id'] not in scopes:fail('registry_entity')
        if f['source_claim_id']!=c['claim_id'] or f['event_id']!=c['event_id'] or f['event_family_id']!=c['event_family_id']:fail('source_identity')
        if set(r['evidence_refs'])!={e['evidence_id'] for e in c['provenance']['evidence']} or not set(r['evidence_refs'])<=evidence:fail('evidence_link')
        ids=r['source_annotation_ids']
        if len(ids)!=2 or any(i not in annotations or annotations[i]['item_id']!=item or annotations[i]['facts']!=f for i in ids):fail('original_annotation_link')
        if f.get('published_at') is not None or f.get('time_precision')!='date' or (d and f['published_date']!=d['published_date']):fail('publication_precision')
        if r['record_kind']=='numeric_claim':
            if f['metric_id'] not in metrics or f['metric_id']!=n['metric_id'] or f['definition_version']!=n['definition_version']:fail('registry_metric_definition')
            try:
                value=Decimal(f['numeric_value']); scale=Decimal(f['scale']); base=Decimal(f['numeric_value_base_units'])
                target=Decimal(n['numeric_value'])
                if value*scale!=base or base!=target or scale!=Decimal(n['source_scale']) or Decimal(n['scale'])!=1:fail('numeric_representation')
                raw=Decimal(f['value_raw'].replace(',','').replace('(','-').replace(')','').replace('$','').strip())
                if value!=(abs(raw) if f['sign_policy']=='outflow_to_positive' else raw):fail('raw_sign_policy')
            except (InvalidOperation,KeyError):fail('numeric_parse')
            if f['currency']!='USD' or f['canonical_unit']!='USD':fail('unit_currency')
        elif r['record_kind']=='reporting_relation':
            if f['source_relation_id']!=c['relation_id'] or f['relation_type']!='reports_segment':fail('relation_identity')
            if f['subject_entity_id']!='US-MSFT' or f['object_entity_id']!=n['object_entity_id'] or f['direction']!='subject_to_object':fail('relation_direction')
            if any(f[x] is not None for x in ['effective_period_start','effective_period_end','valid_from','valid_to']):fail('invented_relation_validity')
        else:fail('unknown_record_kind')
    return errors

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--report',type=Path,required=True);args=parser.parse_args()
    if args.report.exists():raise FileExistsError(args.report)
    require_stage(4)
    data=rows(OUT/'reviewed_agent_claims.jsonl')+rows(OUT/'reviewed_agent_relations.jsonl')
    context=(rows(OUT/'contract_records.jsonl'),{a['annotation_id']:a for a in rows(OUT/'annotations_raw.jsonl')},
        {e['evidence_id'] for e in rows(OUT/'evidence_index.jsonl')},{d['doc_id']:d for d in rows(SOURCE/'document_manifest_v0_3.csv')},
        {m['metric_id'] for m in rows(REGISTRY/'metric_catalog.csv')},{e['entity_id'] for e in rows(REGISTRY/'entity_catalog.csv')},
        {e['scope_id'] for e in rows(REGISTRY/'entity_catalog.csv')})
    errors=check(data,*context);tests=[]
    def case(name,index,path,value,expected):
        altered=copy.deepcopy(data);node=altered[index]
        for key in path[:-1]:node=node[key]
        node[path[-1]]=value; found=check(altered,*context)
        tests.append({'case':name,'passed':any(expected in e for e in found),'expected':expected})
    case('double_million',0,['facts','scale'],'1000000000000','numeric_representation')
    case('base_value_replaced_with_source_value',0,['facts','numeric_value_base_units'],data[0]['facts']['numeric_value'],'numeric_representation')
    case('base_value_used_as_source_value',0,['facts','numeric_value'],data[0]['facts']['numeric_value_base_units'],'numeric_representation')
    cap=next(i for i,r in enumerate(data) if r['facts'].get('sign_policy')=='outflow_to_positive')
    case('cash_outflow_sign_lost',cap,['facts','sign_policy'],'preserve','raw_sign_policy')
    case('wrong_source_claim',33,['facts','source_claim_id'],data[0]['item_id'],'source_identity')
    case('reverse_relation',33,['facts','subject_entity_id'],data[33]['facts']['object_entity_id'],'relation_direction')
    case('invent_validity',33,['facts','valid_from'],'2023-07-01','invented_relation_validity')
    case('missing_evidence',0,['evidence_refs'],[],'evidence_link')
    case('fake_human_gold',0,['human_gold'],True,'human_gold_overclaim')
    case('exposed_test',0,['split'],'test','development_exposure')
    case('invent_exact_time',0,['facts','published_at'],'2024-07-30T00:00:00Z','publication_precision')
    case('wrong_original_annotation',0,['source_annotation_ids'],data[1]['source_annotation_ids'],'original_annotation_link')
    case('company_id_used_as_scope',0,['facts','scope_id'],'US-MSFT','registry_entity')
    report={'checked_at':now(),'status':'passed_with_explicit_limitations' if not errors and all(t['passed'] for t in tests) else 'failed',
        'records':len(data),'numeric_records':33,'relation_records':6,'errors':errors,'negative_cases':tests,
        'code_sha256':sha(__file__),'reserved_content_read':False,'human_gold':0,
        'scope':'Contract-to-reviewed adapter, IDs, units/sign, provenance, registry, exposure and absent-human-gold checks; not a new source truth audit.'}
    json_file(args.report,report);print(json.dumps({'status':report['status'],'records':len(data),'errors':len(errors),'negative_cases_passed':sum(t['passed'] for t in tests)}))
    if report['status']=='failed':raise SystemExit(1)

if __name__=='__main__':main()
