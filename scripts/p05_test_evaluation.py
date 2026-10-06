"""Check that corrupt predictions and incomplete runs cannot improve regression scores."""
from __future__ import annotations
import argparse
import copy
from pathlib import Path
from p05_common import *
from p05_compare_reference import compare
from p05_validate_predictions import ValidationContext, validate_run

def run(input_dir,run_dir,report):
    ctx=ValidationContext(input_dir);preds=rows(run_dir/'predictions.jsonl');results=rows(run_dir/'input_results.jsonl')
    refs=rows(P3/'reviewed_agent_claims.jsonl')+rows(P3/'reviewed_agent_relations.jsonl')
    source={e['evidence_id']:e for e in rows(P3/'evidence_index.jsonl')}
    maps=rows(input_dir/'evidence_map.jsonl');inputs=rows(input_dir/'extractor_inputs.jsonl');cases=[]
    numeric=next(p for p in preds if p['record_kind']=='numeric_claim')
    rel=next(p for p in preds if p['record_kind']=='reporting_relation')
    def check(name,fn):
        try: ok=bool(fn());error=None
        except Exception as exc: ok=False;error=type(exc).__name__+':'+str(exc)
        cases.append(dict(case_id=name,synthetic=True,passed=ok,error=error))
    def mutation(p,path,value):
        r=copy.deepcopy(p);t=r
        for k in path[:-1]:t=t[k]
        t[path[-1]]=value
        return r
    mutations=[('changed_numeric',numeric,['normalized','numeric_value'],'1','numeric_value'),
       ('changed_prediction_input_id',numeric,['input_id'],'missing','unknown_input_id'),
       ('missing_required_field',numeric,['rule_version'],None,'schema:'),
       ('double_million',numeric,['normalized','scale'],'1000000','unit_scale'),
       ('raw_sign_loss',numeric,['normalized','source_numeric_value'],'-64727','source_sign'),
       ('period_year_mutation',numeric,['normalized','temporal','reference_period','fiscal_year'],2025,'reporting_period'),
       ('future_dependency_missing',numeric,['normalized','availability_dependencies'],[],'availability_dependency'),
       ('retrospective_status_lost',numeric,['normalized','scope_status_as_of'],'supported','scope_cutoff_status'),
       ('invented_exact_time',numeric,['normalized','temporal','published_at'],'2024-07-30T00:00:00Z','schema:'),
       ('claim_external_verification',numeric,['normalized','evidence_status'],'externally_verified','schema:'),
       ('drop_unaudited',numeric,['raw','source_qualifier'],'company_reported','source_qualifier_preservation'),
       ('calibrated_probability_invention',numeric,['assessment','probability'],1.0,'schema:'),
       ('review_readiness_overclaim',numeric,['assessment','review_readiness'],'supported','schema:'),
       ('date_audit_overclaim',numeric,['normalized','temporal','date_conflict_status'],'none_observed','schema:'),
       ('shifted_numeric_span',numeric,['raw','value_span_start'],1,'value_span'),
       ('direction_reversed',rel,['normalized','subject_entity_id'],rel['normalized']['object_entity_id'],'relation_endpoints'),
       ('role_reversed',rel,['normalized','subject_role'],'reported_segment','relation_roles_direction'),
       ('effective_promoted_from_report',rel,['normalized','valid_from'],'2023-07-01','schema:'),
       ('wrong_source_hash',numeric,['provenance','source_sha256'],'0'*64,'prediction_source_hash'),
       ('missing_reason',numeric,['field_missing_reasons'],{},'missing_reason:')]
    for name,base,path,value,reason in mutations:
        check(name,lambda base=base,path=path,value=value,reason=reason: any(reason in e for e in ctx.check(mutation(base,path,value))))
    def comp(ps,rr=None,invalid=()):return compare(ps,rr or refs,inputs,maps,source,invalid)
    def bundle(result,kind='numeric_claim'):
        return next(m for m in result['metrics'] if m['record_kind']==kind and m['field']=='observed_bundle')
    check('baseline_39_valid',lambda: all(validate_run(ctx,preds,results)['checks'].values()))
    check('changed_number_scored_mismatch',lambda: bundle(comp([mutation(numeric,['normalized','numeric_value'],'1')]+preds[1:]))['numerator']==32)
    check('changed_reference_id_not_matching_feature',lambda: bundle(comp(preds,[{**r,'item_id':'opaque-'+str(i)} for i,r in enumerate(refs)]))['numerator']==33)
    check('missing_prediction_denominator_stays_33',lambda: bundle(comp(preds[1:]))['denominator']==33 and bundle(comp(preds[1:]))['numerator']==32)
    check('missing_input_terminal_detected',lambda: not validate_run(ctx,preds,results[1:])['checks']['all_inputs_have_terminal_result'])
    check('duplicate_candidate_tie_not_double_success',lambda: bundle(comp(preds+[copy.deepcopy(numeric)]))['numerator']==32)
    check('duplicate_terminal_detected',lambda: not validate_run(ctx,preds,results+[copy.deepcopy(results[0])])['checks']['unique_results'])
    check('unknown_id_cannot_count_success',lambda: bundle(comp([mutation(numeric,['input_id'],'unknown')]+preds[1:]))['numerator']==32)
    check('invalid_candidate_stays_in_denominator',lambda: bundle(comp(preds,invalid=[numeric['prediction_id']]))['numerator']==32)
    check('quarantined_candidate_stays_in_denominator',lambda: bundle(comp([mutation(numeric,['status'],'quarantined')]+preds[1:]))['numerator']==32)
    check('abstained_candidate_stays_in_denominator',lambda: bundle(comp([mutation(numeric,['status'],'abstained')]+preds[1:]))['numerator']==32)
    check('missing_all_denominator_preserved',lambda: bundle(comp([]))['denominator']==33 and bundle(comp([]))['numerator']==0)
    check('extra_candidate_truth_unassessed',lambda: comp(preds+[dict(numeric,prediction_id='extra',evidence_refs=['unknown'])])['extra_candidates'][0]['status']=='unmatched_candidate_truth_unassessed')
    check('zero_independent_denominator_null',lambda: all(m['value'] is None and m['denominator']==0 for m in comp(preds)['metrics'] if m['record_kind']=='independent'))
    check('unknowns_separate_from_observed',lambda: any(m['origin']=='state_only' for m in comp(preds)['metrics']))
    def duplicate_reference():
        try:comp(preds,refs+[copy.deepcopy(refs[0])])
        except ValueError:return True
        return False
    check('duplicate_reference_refuses_scoring',duplicate_reference)
    check('coherent_header_swap_rejected_by_original_binding',lambda: 'source_header_binding' in ctx.check_source(
        {**inputs[0],'evidence':[dict(e,header_refs=list(reversed(e['header_refs']))) if e['kind']=='numeric_value' else e for e in inputs[0]['evidence']]}))
    output=dict(checked_at=now(),synthetic=True,cases=cases,passed=sum(c['passed'] for c in cases),total=len(cases),
                code_sha256=code_hashes(),source_evaluation_samples=0)
    json_file(report,output)
    print(json.dumps(dict(passed=output['passed'],total=output['total'],failed=[c['case_id'] for c in cases if not c['passed']])))
    return 0 if output['passed']==output['total'] else 1

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--input-dir',type=Path,default=P4)
    p.add_argument('--run-dir',type=Path,required=True);p.add_argument('--report',type=Path,required=True)
    a=p.parse_args();raise SystemExit(run(a.input_dir,a.run_dir,a.report))
