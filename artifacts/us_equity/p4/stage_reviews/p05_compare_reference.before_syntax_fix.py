"""One-to-one comparison with shared agent references AFTER prediction freeze."""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path
from p05_common import *

def location_key(doc,revision,kind,evidence):
    return (doc,revision,kind,tuple(sorted((e['kind'],e['location'],e['start'],e['end']) for e in evidence)))

def reference_fields(ref):
    f=ref['facts'];relation=ref['record_kind']=='reporting_relation'
    common={k:f[k] for k in ('company_id','scope_id','modality','published_date','published_at','time_precision','scope_status_as_of')}
    common['source_qualifier']=f['evidence_status']
    if relation:
        common.update({k:f[k] for k in ('relation_type','subject_entity_id','object_entity_id','subject_role','object_role','direction','negation',
                     'reference_period_start','reference_period_end','effective_period_start','effective_period_end','valid_from','valid_to')})
    else:
        common.update({k:f[k] for k in ('metric_id','definition_version','currency','canonical_unit','sign_policy','balance_or_flow','accounting_basis',
                     'period_start','period_end','as_of_date','duration_days','fiscal_year','fiscal_quarter','value_span_start','value_span_end')})
        base=Decimal(f['numeric_value'])*Decimal(f['scale'])
        if base!=Decimal(f['numeric_value_base_units']):raise ValueError('Reference base/source scale inconsistency')
        common.update(numeric_value=format(base,'f'),source_scale=f['scale'],scale='1',
                      period_kind='instant' if f['period_kind']=='instant' else 'quarter' if f['fiscal_quarter'] else 'annual')
    return common

def prediction_fields(p):
    n=p['normalized'];t=n['temporal'];per=t['reference_period'];rel=p['record_kind']=='reporting_relation'
    f={**n,**{k:t[k] for k in ('published_date','published_at','time_precision')},source_qualifier=p['raw']['source_qualifier']}
    if rel:
        f.update(reference_period_start=per['period_start'],reference_period_end=per['period_end'],
                 effective_period_start=None if t['effective_period'] is None else t['effective_period'].get('period_start'),
                 effective_period_end=None if t['effective_period'] is None else t['effective_period'].get('period_end'))
    else:
        f.update(per);f.update({k:p['raw'][k] for k in ('value_span_start','value_span_end')})
    return f

PROVIDED={'company_id','scope_id','definition_version','currency','canonical_unit','accounting_basis','source_qualifier',
          'published_date','published_at','time_precision','scope_status_as_of','modality'}

def state_only(value):
    return value is None or (isinstance(value,str) and (value in ('unknown','not_applicable') or value.startswith('unresolved')))

def compare(predictions,references,inputs,evidence_map,source_evidence,invalid_ids=()):
    inp={x['input_id']:x for x in inputs}; em={e['evidence_id']:e for e in evidence_map}
    buckets=defaultdict(list);extra=[];key_errors=[]
    for p in predictions:
        try:
            ev=[em[e] for e in p['evidence_refs']]
            key=location_key(p['doc_id'],p['revision_id'],p['record_kind'],ev)
            buckets[key].append(p)
        except (KeyError,TypeError): key_errors.append(p.get('prediction_id'))
    matches=[];fields=defaultdict(lambda:Counter());matched_ids=set();reference_keys=[]
    for ref in references:
        roles=(['numeric_value'] if ref['record_kind']=='numeric_claim' else [])+['row_label','period_header','year_header','unit']
        ev=[dict(kind=role,**{k:source_evidence[e][k] for k in ('location','start','end')}) for e,role in zip(ref['evidence_refs'],roles,strict=True)]
        key=location_key(ref['facts']['doc_id'],ref['facts']['revision_id'],ref['record_kind'],ev);reference_keys.append(key)
        candidates=buckets.get(key,[]); status='matched' if len(candidates)==1 else 'missing' if not candidates else 'tie_conflict'
        p=candidates[0] if len(candidates)==1 else None
        if p:matched_ids.add(p['prediction_id'])
        valid=p is not None and p.get('status')=='predicted' and p['prediction_id'] not in invalid_ids and p.get('input_id') in inp
        expected=reference_fields(ref)
        try:actual=prediction_fields(p) if p else {}
        except (KeyError,TypeError):actual={};valid=False
        details=[];known_matches=[];all_matches=[]
        for field,wanted in expected.items():
            state=state_only(wanted);origin='state_only' if state else 'curator_provided' if field in PROVIDED else 'observed_or_rule_derived'
            same=valid and field in actual and actual[field]==wanted
            metric=fields[(ref['record_kind'],field,origin)];metric['denominator']+=1;metric['matched']+=int(same)
            metric['missing_prediction']+=int(p is None);metric['invalid_prediction']+=int(p is not None and not valid)
            if not state:known_matches.append(same)
            all_matches.append(same)
            details.append(dict(field=field,origin=origin,expected=wanted,predicted=actual.get(field),matched=same))
        matches.append(dict(reference_item_id=ref['item_id'],record_kind=ref['record_kind'],match_status=status,
                            prediction_id=p['prediction_id'] if p else None,candidate_ids=[x['prediction_id'] for x in candidates],
                            prediction_valid=valid,observed_bundle_match=bool(known_matches) and all(known_matches),
                            including_state_match=all(all_matches),fields=details))
    for p in predictions:
        if p['prediction_id'] not in matched_ids:
            extra.append(dict(prediction_id=p['prediction_id'],status='unmatched_candidate_truth_unassessed',
                              reason='incomplete_reference_or_tie_or_invalid_key'))
    metrics=[]
    for (kind,field,origin),counts in sorted(fields.items()):
        d=counts['denominator'];m=counts['matched']
        metrics.append(dict(record_kind=kind,field=field,origin=origin,numerator=m,denominator=d,
                            value=m/d if d else None,interpretation='shared_agent_adaptation_regression'))
    for kind in ('numeric_claim','reporting_relation'):
        group=[m for m in matches if m['record_kind']==kind]
        metrics.append(dict(record_kind=kind,field='observed_bundle',origin='mixed_observed_and_provided',
                    numerator=sum(m['observed_bundle_match'] for m in group),denominator=len(group),
                    value=sum(m['observed_bundle_match'] for m in group)/len(group) if group else None,
                    interpretation='conditional_preselected_cells_not_independent_accuracy'))
    for field in ('precision','recall','F1','relevance','NER','importance','calibrated_probability'):
        metrics.append(dict(record_kind='independent',field=field,origin='not_evaluated',numerator=None,denominator=0,value=None,
                            interpretation='no_independent_gold_or_test'))
    # Character overlap is conditional on matched original DOM cells, not sentence/document spans.
    overlap=0;ref_chars=0;pred_chars=0;exact=0;numeric_count=0
    bypred={p['prediction_id']:p for p in predictions}
    for m,ref in zip(matches,references,strict=True):
        if ref['record_kind']!='numeric_claim':continue
        numeric_count+=1;f=ref['facts'];a=f['value_span_start'];b=f['value_span_end'];ref_chars+=b-a
        if not m['prediction_valid']:continue
        raw=bypred[m['prediction_id']]['raw'];c=raw['value_span_start'];d=raw['value_span_end']
        pred_chars+=d-c;overlap+=max(0,min(b,d)-max(a,c));exact+=int((a,b)==(c,d))
    metrics.append(dict(record_kind='numeric_claim',field='span_exact',origin='observed',numerator=exact,denominator=numeric_count,
                        value=exact/numeric_count if numeric_count else None,interpretation='same_selected_DOM_cell_codepoints'))
    span=dict(intersection_codepoints=overlap,reference_codepoints=ref_chars,predicted_codepoints=pred_chars,
              overlap_f1=2*overlap/(ref_chars+pred_chars) if ref_chars+pred_chars else None)
    return dict(matches=matches,metrics=metrics,extra_candidates=extra,key_errors=key_errors,span=span,
                reference_keys_unique=len(reference_keys)==len(set(reference_keys)))

def execute(input_dir,run_dir):
    require_stage(3,input_dir)
    manifest=read_json(run_dir/'run_manifest.json')
    if not all(sha(ROOT/p)==h for p,h in manifest['output_hashes'].items()): raise ValueError('Prediction freeze changed')
    opened=now();refs=rows(P3/'reviewed_agent_claims.jsonl')+rows(P3/'reviewed_agent_relations.jsonl')
    preds=rows(run_dir/'predictions.jsonl');validation=read_json(run_dir/'validation_report.json')
    evidence={e['evidence_id']:e for e in rows(P3/'evidence_index.jsonl')}
    result=compare(preds,refs,rows(input_dir/'extractor_inputs.jsonl'),rows(input_dir/'evidence_map.jsonl'),evidence,
                   [f['prediction_id'] for f in validation['findings']])
    jsonl(run_dir/'reference_match_results.jsonl',result['matches']);csv_file(run_dir/'metrics.csv',result['metrics'])
    errors=[dict(reference_item_id=m['reference_item_id'],prediction_id=m['prediction_id'],field=d['field'],
                 error_type=m['match_status'] if m['match_status']!='matched' else 'field_mismatch',
                 expected=json.dumps(d['expected']),actual=json.dumps(d['predicted']))
            for m in result['matches'] for d in m['fields'] if not d['matched']]
    csv_file(run_dir/'error_analysis.csv',errors,['reference_item_id','prediction_id','field','error_type','expected','actual'])
    jsonl(run_dir/'unmatched_candidates.jsonl',result['extra_candidates'])
    json_file(run_dir/'comparison_manifest.json',dict(compared_at=now(),reference_read_at=opened,
            predictions_frozen_at=manifest['completed_at'],prediction_sha256=sha(run_dir/'predictions.jsonl'),
            reference_hashes=hashes([P3/'reviewed_agent_claims.jsonl',P3/'reviewed_agent_relations.jsonl',P3/'evidence_index.jsonl']),
            reference_count=len(refs),candidate_count=len(preds),matching_status=dict(Counter(m['match_status'] for m in result['matches'])),
            reference_keys_unique=result['reference_keys_unique'],unmatched_candidate_count=len(result['extra_candidates']),
            field_errors=len(errors),span=result['span'],independent_evaluation='not_evaluated',code_sha256=code_hashes()))
    print(json.dumps(dict(references=len(refs),candidates=len(preds),field_errors=len(errors),span=result['span'])))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--input-dir',type=Path,default=P4);p.add_argument('--run-dir',type=Path,required=True)
    a=p.parse_args();execute(a.input_dir,a.run_dir)
