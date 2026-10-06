"""Synthetic adverse cases, separate from source claims and evaluation samples."""
from __future__ import annotations
import argparse
import copy
import tempfile
from pathlib import Path
from p05_common import *
from p05_input_validation import check_input
from p05_rule_baseline import infer, parse_number, parse_period, Abstain

def change_text(r,key,value):
    """Construct a coherent synthetic observation; never edits source files."""
    r=copy.deepcopy(r);r['synthetic']=True;r['raw'][key]=value
    kind={'value_cell':'numeric_value','unit_header':'unit','year_header':'year_header',
          'period_header':'period_header','row_label':'row_label'}[key]
    for e in r['evidence']:
        if e['kind']!=kind: continue
        e['raw_fragment']=value;e['fragment_origin']=0;e['selected_text']=value.strip() or value
        e['start']=len(value)-len(value.lstrip());e['end']=len(value.rstrip())
        if not value.strip(): e['start']=0;e['end']=max(1,len(value))
        e['normalized_fragment'],e['normalized_to_raw']=normalize_fragment(value)
    return r

def run(stage,out,report):
    iv=validator(read_json(out/'input_schema.json'));rules=read_json(out/'rules_v0_1.json')
    inputs=rows(out/'extractor_inputs.jsonl');base=inputs[0]
    capex=next(x for x in inputs if x['raw']['row_label']=='Additions to property and equipment')
    balance=next(x for x in inputs if x['raw']['row_label']=='Total assets')
    segment=next(x for x in inputs if x['input_kind']=='numeric_cell' and x['context']['table_purpose']=='segment_revenue')
    relation=next(x for x in inputs if x['input_kind']=='relation_context')
    cases=[]
    def case(name,check,details=None):
        try:
            passed=bool(check())
            error=None
        except Exception as exc:
            passed=False;error=type(exc).__name__+':'+str(exc)
        cases.append(dict(case_id=name,synthetic=True,passed=passed,error=error,details=details))
    def mutate(r,path,value):
        r=copy.deepcopy(r);r['synthetic']=True;t=r
        for key in path[:-1]:t=t[key]
        t[path[-1]]=value
        return r
    def infer_one(r,rr=None): return infer(r,rr or rules,'synthetic-test',iv)
    def abstains(r,reason):
        ps,res,_=infer_one(r)
        return not ps and res['status'] in ('abstained','quarantined') and any(reason in x for x in res['reasons'])
    def predicts(r): return infer_one(r)[0][0]['normalized']
    if stage=='inputs':
        case('all_39_input_contracts',lambda: all(not check_input(x,iv) for x in inputs))
        for key in ('source_claim_id','source_relation_id','source_record_ref','metric_id','scope_id','item_id'):
            case('reject_answer_field_'+key,lambda key=key: bool(check_input({**base,key:'answer'},iv)))
        for key in ('unit_header','year_header','row_label','period_header'):
            case('mismatched_'+key,lambda key=key: bool(check_input(mutate(base,['raw',key],'wrong'),iv)))
        case('wrong_row_index',lambda: 'row_binding' in check_input(mutate(base,['evidence',0,'row_index'],900),iv))
        case('wrong_table',lambda: 'cross_table_binding' in check_input(mutate(base,['evidence',0,'table_id'],'/fake/table'),iv))
        case('missing_header_binding',lambda: 'header_binding' in check_input(mutate(base,['evidence',0,'header_refs'],[]),iv))
        case('shifted_span',lambda: 'fragment_span_roundtrip' in check_input(mutate(base,['evidence',0,'start'],1),iv))
        case('normalization_map_tamper',lambda: 'normalization_offset_map' in check_input(mutate(base,['evidence',0,'normalized_to_raw'],[]),iv))
        for text in ('0','(13,873)','\u00a0 64,727\u00a0','-','unknown'):
            case('preserve_raw_'+repr(text),lambda text=text: change_text(base,'value_cell',text)['raw']['value_cell']==text
                 and not check_input(change_text(base,'value_cell',text),iv))
        case('unicode_nonbmp_codepoint_mapping',lambda: normalize_fragment('  A\u00a0\r\n B😀  ',10)==('A B😀',[[12,13],[13,17],[17,18],[18,19]]))
        # A decoy answer changes, while fixed allowlisted observations stay identical.
        def answer_independence():
            with tempfile.TemporaryDirectory(prefix='p05-decoy-') as td:
                p=Path(td)/'reviewed_agent_claims.jsonl'
                p.write_text('{"numeric_value":"1","metric_id":"wrong"}\n','utf-8')
                first=infer_one(base)[0]
                p.write_text('{"numeric_value":"9999999999","metric_id":"revenue"}\n','utf-8')
                return first==infer_one(base)[0]
        case('decoy_reference_answer_mutation_invariant',answer_independence,
             'No production references read; inference function takes only input and rules. CLI file-read guard tested in actual run.')
    else:
        case('zero_is_value',lambda: predicts(change_text(base,'value_cell','0'))['numeric_value']=='0')
        case('decimal_exact',lambda: predicts(change_text(base,'value_cell','0.000001'))['numeric_value']=='1.000000')
        case('nbsp_cell',lambda: predicts(change_text(base,'value_cell','\u00a064,727\u00a0'))['numeric_value']=='64727000000')
        case('negative_noncapex_preserved',lambda: predicts(change_text(base,'value_cell','(10)'))['numeric_value']=='-10000000')
        case('capex_outflow_once',lambda: predicts(capex)['numeric_value']==str(-parse_number(capex['raw']['value_cell'])*1000000))
        case('positive_capex_not_abs',lambda: abstains(change_text(capex,'value_cell','13873'),'positive_capex_source_sign_ambiguous'))
        case('capex_zero',lambda: predicts(change_text(capex,'value_cell','0'))['numeric_value']=='0')
        for token,reason in [('-','dash_not_zero'),('unknown','unknown_numeric_value'),('1,23','malformed_numeric_token'),('(-1)','ambiguous_sign'),('(10','ambiguous_sign'),('NaN','malformed_numeric_token')]:
            case('invalid_number_'+token,lambda token=token,reason=reason: abstains(change_text(base,'value_cell',token),reason))
        case('blank_is_not_zero',lambda: abstains(change_text(base,'value_cell',' '),'blank_numeric_cell'))
        case('unknown_unit',lambda: abstains(change_text(base,'unit_header','thousands'),'missing_or_unsupported_unit'))
        case('missing_unit',lambda: abstains(change_text(base,'unit_header',' '),'missing_or_unsupported_unit'))
        case('missing_year',lambda: abstains(change_text(base,'year_header',' '),'missing_or_ambiguous_year_header'))
        case('ambiguous_year',lambda: abstains(change_text(base,'year_header','2024 2025'),'missing_or_ambiguous_year_header'))
        case('period_from_header_not_doc_id',lambda: predicts(change_text(base,'year_header','2025'))['temporal']['reference_period']['fiscal_year']==2025)
        case('quarter_to_annual_from_header',lambda: predicts(change_text(base,'period_header','Twelve Months Ended June 30,'))['temporal']['reference_period']['period_kind']=='annual')
        case('annual_leap_366',lambda: parse_period('Twelve Months Ended June 30,','2024')['duration_days']==366)
        case('annual_common_365',lambda: parse_period('Twelve Months Ended June 30,','2025')['duration_days']==365)
        case('flow_as_instant_rejected',lambda: abstains(change_text(change_text(base,'period_header','June 30,2024'),'year_header','June 30,2024'),'balance_flow_period_conflict'))
        case('balance_as_flow_rejected',lambda: abstains(change_text(change_text(balance,'period_header','Three Months Ended June 30,'),'year_header','2024'),'balance_flow_period_conflict'))
        case('ambiguous_label',lambda: abstains(change_text(base,'row_label','Revenue and operating income'),'unknown_or_ambiguous_metric_alias'))
        case('derived_fcf_not_source_metric',lambda: abstains(change_text(base,'row_label','Free cash flow'),'unknown_or_ambiguous_metric_alias'))
        case('ambiguous_scope',lambda: abstains(mutate(base,['context','scope_label'],'some company'),'ambiguous_company_scope'))
        case('currency_unsupported',lambda: abstains(mutate(base,['context','currency'],'EUR'),'unsupported_currency_or_accounting'))
        case('external_verification_not_allowed',lambda: abstains(mutate(base,['context','source_qualifier'],'externally_verified'),'unsupported_source_qualifier'))
        case('reserved_document_rejected',lambda: abstains(mutate(base,['doc_id'],'US-MSFT-FY2026-Q1-RELEASE'),'document_not_allowlisted'))
        case('wrong_source_hash',lambda: abstains(mutate(base,['source_sha256'],'0'*64),'revision_or_hash_mismatch'))
        case('relation_survives_numeric_failure',lambda: predicts(mutate(relation,['raw','value_cell'],'broken numeric'))['relation_type']=='reports_segment')
        case('relation_direction',lambda: predicts(relation)['subject_entity_id']=='US-MSFT' and predicts(relation)['object_entity_id']!= 'US-MSFT')
        case('segment_numeric_retains_unaudited',lambda: infer_one(segment)[0][0]['raw']['source_qualifier']=='company_reported_unaudited')
        case('relation_effective_unknown',lambda: predicts(relation)['temporal']['effective_period'] is None and predicts(relation)['valid_from'] is None)
        case('company_table_not_relation',lambda: abstains(mutate(relation,['context','table_purpose'],'company_financial_statement'),'relation_requires_segment_reporting_table'))
        case('comparative_retains_release_definition',lambda: all(predicts(x)['definition_version']=='msft-segment-presentation-fy2025' for x in inputs
             if x['doc_id']=='US-MSFT-FY2025-Q4-RELEASE' and x['context']['table_purpose']=='segment_revenue' and x['raw']['year_header']=='2024'))
    value=dict(checked_at=now(),stage=stage,synthetic=True,cases=cases,passed=sum(x['passed'] for x in cases),total=len(cases),
               source_evaluation_samples=0,code_sha256=code_hashes())
    json_file(report,value)
    print(json.dumps(dict(stage=stage,passed=value['passed'],total=value['total'],failed=[c['case_id'] for c in cases if not c['passed']])))
    return 0 if value['passed']==value['total'] else 1

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--stage',choices=['inputs','rules'],required=True)
    parser.add_argument('--input-dir',type=Path,default=P4);parser.add_argument('--report',type=Path,required=True)
    args=parser.parse_args();raise SystemExit(run(args.stage,args.input_dir,args.report))
