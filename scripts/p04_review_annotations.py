"""Audit annotation structure and source fidelity before comparing annotators."""
from __future__ import annotations
import argparse
from datetime import datetime
from decimal import Decimal
from p04_common import *
from p04_annotation_validation_v1_2 import validate_annotation, validate_assessment

def projection(record, evidence):
    n=record['normalized']; t=n['temporal']; period=t['reference_period']
    result={'source_claim_id':record['claim_id'],'doc_id':record['provenance']['doc_id'],
        'revision_id':record['provenance']['revision_id'],'event_id':record['event_id'],
        'event_family_id':record['event_family_id'],'company_id':n['company_id'],'scope_id':n['scope_id'],
        'modality':n['modality'],'published_date':t['published_date'],'published_at':None,'time_precision':'date',
        'evidence_status':record['raw']['source_evidence_status'],'speaker':'Microsoft Corporation',
        'scope_status_as_of':'unresolved_retrospective_dependency' if n['scope_id']=='US-MSFT-CONSOLIDATED' else 'reported_segment_in_selected_table'}
    if record['record_kind']=='event_claim':
        value=next(e for e in record['provenance']['evidence'] if evidence[e['evidence_id']]['evidence_kind']=='numeric_value')
        result.update(metric_id=n['metric_id'],definition_version=n['definition_version'],
            value_raw=record['raw']['value_raw'],numeric_value=str(Decimal(n['numeric_value'])/Decimal(n['source_scale'])),
            scale=n['source_scale'],numeric_value_base_units=n['numeric_value'],currency=n['currency'],
            canonical_unit=n['canonical_unit'],sign_policy=n['sign_policy'],
            period_start=period['period_start'],period_end=period['period_end'],as_of_date=period['as_of_date'],
            period_kind='instant' if period['period_kind']=='instant' else 'duration',duration_days=period['duration_days'],
            fiscal_year=period['fiscal_year'],fiscal_quarter=period['fiscal_quarter'],
            balance_or_flow=n['financial_context']['balance_or_flow'],value_span_start=value['start'],value_span_end=value['end'],
            accounting_basis=n['accounting_basis'],period_start_derivation=record['raw']['source_period_start_derivation'])
    else:
        result.update(source_relation_id=record['relation_id'],relation_type=n['relation_type'],
            subject_entity_id=n['subject_entity_id'],object_entity_id=n['object_entity_id'],
            subject_role=n['subject_role'],object_role=n['object_role'],direction=n['direction'],negation=n['negation'],
            conditions=n['conditions'],reference_period_start=period['period_start'],reference_period_end=period['period_end'],
            effective_period_start=None,effective_period_end=None,valid_from=None,valid_to=None)
    return result

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--phase',choices=['practice','main'],required=True)
    parser.add_argument('--report',type=Path,required=True); args=parser.parse_args()
    require_stage(2)
    contract=json.loads((OUT/'annotation_output_contract_v1_2.json').read_text(encoding='utf-8'))
    packets={p['item_id']:p for p in rows(OUT/'source_packets.jsonl')}
    evidence={e['evidence_id']:e for e in rows(OUT/'evidence_index.jsonl')}
    records=rows(OUT/'contract_records.jsonl')
    expected={r['relation_id'] or r['claim_id']:projection(r,evidence) for r in records}
    wanted=set(json.loads((OUT/'practice_selection.json').read_text(encoding='utf-8'))['item_ids']) if args.phase=='practice' else set(packets)
    findings=[]; summaries=[]; inputs=[]
    for suffix,actor in [('a','AGENT-A'),('b','AGENT-B')]:
        directory=OUT/f'reviewer_{suffix}'
        suffix_name='_v1_2' if args.phase=='practice' else ''
        ap=directory/f'{args.phase}_annotations{suffix_name}.jsonl'; sp=directory/f'{args.phase}_assessments{suffix_name}.jsonl'
        annotation=rows(ap); assessments=rows(sp); inputs += [ap,sp]
        ann_ids={r['annotation_id']:r for r in annotation}
        checks={'item_coverage':{r['item_id'] for r in annotation}==wanted,
            'unique_annotation_ids':len(ann_ids)==len(annotation),
            'one_annotation_per_item':len(annotation)==len(wanted),
            'assessments_same_count':len(assessments)==len(annotation),
            'assessment_annotation_links':{r['annotation_id'] for r in assessments}==set(ann_ids),
            'correct_actor':all(r['annotator_id']==actor for r in annotation+assessments)}
        for row in annotation:
            errors=validate_annotation(row,packets,contract)
            if not errors:
                mismatch=[k for k,v in expected[row['item_id']].items() if row['facts'][k]!=v]
                errors += ['source_fidelity:'+k for k in mismatch]
            try:
                if datetime.fromisoformat(row['started_at'])>datetime.fromisoformat(row['completed_at']):
                    errors.append('completed_before_started')
            except (TypeError,ValueError): errors.append('invalid_execution_timestamp')
            if errors: findings.append({'actor':actor,'annotation_id':row['annotation_id'],'errors':errors})
        for row in assessments:
            errors=validate_assessment(row,ann_ids,contract)
            parent=ann_ids.get(row['annotation_id'])
            if parent and (parent['item_id']!=row['item_id'] or parent['facts']['published_date']!=row['as_of_date']):
                errors.append('assessment_item_or_cutoff_mismatch')
            if errors:findings.append({'actor':actor,'assessment_id':row['assessment_id'],'errors':errors})
        summaries.append({'annotator_id':actor,'annotations':len(annotation),'assessments':len(assessments),'checks':checks})
    passed=not findings and all(all(s['checks'].values()) for s in summaries)
    result={'phase':args.phase,'checked_at':now(),'status':'passed' if passed else 'needs_improvement',
        'summaries':summaries,'findings':findings,'source_fidelity_basis':'stage2_source_verified_contract_projection',
        'does_not_measure_extraction_accuracy_or_human_agreement':True,
        'inputs':[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)} for p in inputs]}
    json_file(args.report,result)
    print(json.dumps({'phase':args.phase,'status':result['status'],'findings':findings,'counts':summaries}))
    if not passed: raise SystemExit(1)

if __name__=='__main__':main()
