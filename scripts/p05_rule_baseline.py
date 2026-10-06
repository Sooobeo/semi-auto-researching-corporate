"""M0 selected-cell inference. No P04 answers, private HTML, or network access."""
from __future__ import annotations
import argparse
import re
import sys
import time
import tracemalloc
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from p05_common import *
from p05_input_validation import check_input

class Abstain(ValueError):
    pass

def parse_number(raw):
    token=raw.strip()
    if not token: raise Abstain('blank_numeric_cell')
    if token in ('-','—','–'): raise Abstain('dash_not_zero')
    if token.lower() in ('unknown','n/a','null'): raise Abstain('unknown_numeric_value')
    if not re.fullmatch(r'\(?-?\$?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?\)?',token):
        raise Abstain('malformed_numeric_token')
    paren=token.startswith('(')
    if paren!=token.endswith(')') or (paren and '-' in token): raise Abstain('ambiguous_sign')
    value=Decimal(token.strip('()').replace(',','').replace('$',''))
    return -value if paren else value

def parse_period(period_header, year_header):
    ph=' '.join(period_header.split()); yh=' '.join(year_header.split())
    years=re.findall(r'(?<!\d)20\d{2}(?!\d)',yh)
    if len(years)!=1: raise Abstain('missing_or_ambiguous_year_header')
    year=int(years[0]); end=date(year,6,30)
    match=re.fullmatch(r'(Three|Twelve) Months Ended June 30,?',ph)
    if match:
        if not re.fullmatch(r'20\d{2}',yh): raise Abstain('unsupported_duration_year_header')
        quarter=match[1]=='Three'; start=date(year if quarter else year-1,4 if quarter else 7,1)
        return dict(period_start=start.isoformat(),period_end=end.isoformat(),as_of_date=None,
                    period_kind='quarter' if quarter else 'annual',fiscal_year=year,fiscal_quarter=4 if quarter else None,
                    duration_days=(end-start).days+1,period_basis='fiscal')
    instant=re.fullmatch(r'June 30,\s*(20\d{2})',ph)
    if not instant or int(instant[1])!=year: raise Abstain('unsupported_or_conflicting_period_header')
    return dict(period_start=None,period_end=None,as_of_date=end.isoformat(),period_kind='instant',
                fiscal_year=year,fiscal_quarter=None,duration_days=None,period_basis='fiscal')

def infer(r, rules, run_id, input_validator):
    errors=check_input(r,input_validator)
    result=dict(input_id=r.get('input_id'),run_id=run_id,status='quarantined' if errors else 'predicted',
                prediction_ids=[],candidate_count=0,failure_stage='input_contract' if errors else None,
                reasons=errors,attempts=1,synthetic=r.get('synthetic',False))
    if errors: return [],result,[]
    try:
        doc=rules['documents'].get(r['doc_id'])
        if doc is None: raise Abstain('document_not_allowlisted')
        if r['revision_id']!=doc['revision_id'] or r['source_sha256']!=doc['source_sha256']:
            result.update(status='quarantined',failure_stage='source_identity',reasons=['revision_or_hash_mismatch'])
            return [],result,[]
        if r['publication']['published_date']!=doc['published_date'] or r['publication']['observed_at']!=doc['observed_at']:
            result.update(status='quarantined',failure_stage='publication',reasons=['publication_metadata_mismatch'])
            return [],result,[]
        raw=r['raw']; ctx=r['context']; label=' '.join(raw['row_label'].split())
        if ctx['company_id']!=rules['company_id'] or ctx['company_name']!=rules['company_name']:
            raise Abstain('company_context_mismatch')
        segment=ctx['table_purpose']=='segment_revenue'
        relation=r['input_kind']=='relation_context'
        if segment:
            scope=rules['segment_labels'].get(label)
            if scope is None or ctx['scope_label']!=label: raise Abstain('ambiguous_segment_alias_or_scope')
            definition=doc['segment_definition']
            if not definition: raise Abstain('missing_presentation_definition')
            metric=dict(metric_id='revenue',balance_or_flow='flow',statement_type='segment_revenue',sign_policy='preserve')
            dependencies=[]; scope_status='reported_segment_in_selected_table'
        else:
            if relation: raise Abstain('relation_requires_segment_reporting_table')
            if ctx['scope_label']!='company financial statement total': raise Abstain('ambiguous_company_scope')
            metric=rules['metric_labels'].get(label)
            if not isinstance(metric,dict): raise Abstain('unknown_or_ambiguous_metric_alias')
            scope=rules['company_scope_id'];definition='us-financial-0.1'
            dependencies=rules['scope_dependencies'];scope_status='unresolved_retrospective_dependency'
        period=parse_period(raw['period_header'],raw['year_header'])
        if (period['period_kind']=='instant')!=(metric['balance_or_flow']=='balance'):
            raise Abstain('balance_flow_period_conflict')
        if segment and period['period_kind']!='annual': raise Abstain('unsupported_segment_table_period')
        expected_qualifier='company_reported_table' if relation else 'company_reported_unaudited'
        if ctx['source_qualifier']!=expected_qualifier: raise Abstain('unsupported_source_qualifier')
        evid=[e['evidence_id'] for e in r['evidence']]
        n=dict(company_id=rules['company_id'],scope_id=scope,definition_version=definition,
               modality='actual_reported',evidence_status='company_reported',
               temporal=dict(**r['publication'],timezone=None,available_at=None,date_conflict_status='not_yet_checked',
                             reference_period=period,effective_period=None),scope_status_as_of=scope_status,
               availability_dependencies=dependencies,
               **{k:None for k in ('metric_id','numeric_value','currency','canonical_unit','scale','source_scale',
                  'source_numeric_value','sign_policy','balance_or_flow','statement_type','accounting_basis',
                  'relation_type','subject_entity_id','object_entity_id','subject_role','object_role','direction','valid_from','valid_to')},
               negation=False,conditions=[])
        derived=[]; value_raw=None; span_start=None; span_end=None
        if relation:
            n.update(relation_type='reports_segment',subject_entity_id=rules['company_id'],object_entity_id=scope,
                     subject_role='reporting_company',object_role='reported_segment',direction='subject_to_object')
        else:
            if ctx['currency']!='USD' or ctx['accounting_basis']!='GAAP': raise Abstain('unsupported_currency_or_accounting')
            source_scale=rules['units'].get(raw['unit_header'].strip())
            if source_scale is None: raise Abstain('missing_or_unsupported_unit')
            value_raw=raw['value_cell'].strip(); signed=parse_number(raw['value_cell'])
            value=signed
            if metric['sign_policy']=='outflow_to_positive':
                if signed>0: raise Abstain('positive_capex_source_sign_ambiguous')
                value=-signed
            value=value*Decimal(source_scale)
            n.update(**metric,numeric_value=format(value,'f'),currency='USD',canonical_unit='USD',scale='1',
                     source_scale=source_scale,source_numeric_value=format(signed,'f'),accounting_basis=ctx['accounting_basis'])
            ve=next(e for e in r['evidence'] if e['kind']=='numeric_value')
            span_start=raw['value_cell'].index(value_raw);span_end=span_start+len(value_raw)
            derived.append(dict(formula_id=metric['sign_policy']+'_then_scale',input_refs=[ve['evidence_id'],next(e['evidence_id'] for e in r['evidence'] if e['kind']=='unit')],
                                output=n['numeric_value'],rounding_policy='exact_decimal_no_rounding',origin='derived'))
        if period['period_start']:
            derived.append(dict(formula_id='calendar_months_from_three_or_twelve_month_header',
                                input_refs=[e['evidence_id'] for e in r['evidence'] if e['kind'] in ('period_header','year_header')],
                                output=period['period_start'],rounding_policy='not_applicable',origin='derived'))
        missing={'normalized.temporal.published_at':'not_disclosed','normalized.temporal.timezone':'not_disclosed',
                 'normalized.temporal.available_at':'date_only_exact_cutoff_unknown',
                 'assessment.probability':'not_calibrated','normalized.temporal.effective_period':'not_disclosed' if relation else 'not_applicable',
                 'normalized.valid_from':'not_disclosed' if relation else 'not_applicable',
                 'normalized.valid_to':'not_disclosed' if relation else 'not_applicable'}
        if relation:
            for key in ('metric_id','numeric_value','currency','canonical_unit','scale','source_scale','source_numeric_value','sign_policy','balance_or_flow','statement_type','accounting_basis'):
                missing['normalized.'+key]='not_applicable_to_reporting_relation'
        else:
            for key in ('relation_type','subject_entity_id','object_entity_id','subject_role','object_role','direction'):
                missing['normalized.'+key]='not_applicable_to_numeric_claim'
        pid=opaque('P-', [run_id,r['input_id'],'relation' if relation else 'numeric'])
        prediction=dict(schema_version=SCHEMA_VERSION,registry_version=rules['registry_version'],rule_version=rules['rule_version'],
                  prediction_id=pid,run_id=run_id,input_id=r['input_id'],doc_id=r['doc_id'],revision_id=r['revision_id'],
                  candidate_claim_id=None if relation else opaque('CC-',[run_id,r['input_id']]),
                  candidate_relation_id=opaque('CR-',[run_id,r['input_id']]) if relation else None,
                  record_kind='reporting_relation' if relation else 'numeric_claim',input_mode=r['input_mode'],
                  status='predicted',synthetic=r['synthetic'],
                  raw=dict(value_raw=value_raw,value_cell=raw['value_cell'],row_label=raw['row_label'],
                           period_header=raw['period_header'],year_header=raw['year_header'],unit_header=raw['unit_header'],
                           source_qualifier=ctx['source_qualifier'],value_span_start=span_start,value_span_end=span_end),
                  normalized=n,assessment=dict(review_readiness='needs_review',
                       reasons=['selected_cells_only','shared_adaptation_context','no_independent_human_review',
                                'actual_business_validity_unknown' if relation else 'prior_not_checked',
                                'segment_definition_policy_unresolved' if segment else 'retrospective_scope_dependency'],
                       rule_signal=['exact_label','explicit_header','reporting_table' if relation else 'decimal_scale'],
                       score_type='uncalibrated_rule',probability=None),derived=derived,
                  provenance=dict(source_sha256=r['source_sha256'],source_url=doc['source_url'],rights_basis_ref=doc['rights_basis_ref'],
                                  context_origin='curator_provided',context_provenance_ref=ctx['context_provenance_ref'],
                                  exposure='adaptation',leakage_group=rules['leakage_group'],historical_blind=False,
                                  source_parser_version=doc['source_parser_version']),evidence_refs=evid,field_missing_reasons=missing)
        result.update(prediction_ids=[pid],candidate_count=1)
        return [prediction],result,[dict(input_id=r['input_id'],prediction_id=pid,raw=value_raw,
                    source_numeric_value=n['source_numeric_value'],source_scale=n['source_scale'],
                    numeric_value=n['numeric_value'],sign_policy=n['sign_policy'],reference_period=period,
                    period_start_origin='derived' if period['period_start'] else 'not_applicable')]
    except Abstain as exc:
        result.update(status='abstained',failure_stage='semantic_mapping',reasons=[str(exc)])
        return [],result,[]

def extract_batch(inputs,rules,run_id,input_validator,prediction_validator):
    predictions=[];results=[];audits=[]
    for r in inputs:
        try:
            ps,res,au=infer(r,rules,run_id,input_validator)
            for p in ps:
                errors=list(prediction_validator.iter_errors(p))
                if errors:
                    p['status']='quarantined'
                    res.update(status='quarantined',failure_stage='output_schema',reasons=['schema:'+str(e.json_path) for e in errors])
            predictions.extend(ps);results.append(res);audits.extend(au)
        except Exception as exc:
            # Do not include source text or full exception payload in public logs.
            results.append(dict(input_id=r.get('input_id'),run_id=run_id,status='failed',prediction_ids=[],candidate_count=0,
                                failure_stage='extract',reasons=[type(exc).__name__],attempts=1,synthetic=r.get('synthetic',False)))
    return predictions,results,audits

def execute(input_dir,output_dir,run_id):
    if output_dir.exists(): raise FileExistsError('Use a fresh run directory')
    require_stage(2,input_dir)
    start=time.perf_counter();cpu_start=time.process_time();stamp=now()
    rules=read_json(input_dir/'rules_v0_1.json')
    iv=validator(read_json(input_dir/'input_schema.json'));pv=validator(read_json(input_dir/'prediction_schema.json'))
    paths=[input_dir/n for n in ('rules_v0_1.json','input_schema.json','prediction_schema.json','extractor_inputs.jsonl','requirements.lock','environment_manifest.json')]
    dependencies=hashes(paths); codes=code_hashes(); inputs=rows(input_dir/'extractor_inputs.jsonl')
    if len({r['input_id'] for r in inputs})!=len(inputs): raise ValueError('Duplicate input IDs')
    # Hard deny inference-time reads outside the frozen public input files.
    allowed={str(p.resolve()).lower() for p in paths}; reads=[]; blocked=[]
    guard={'active':True}
    def audit(event,args):
        if not guard['active']: return
        if event.startswith('socket.') or event.startswith('urllib.'):
            blocked.append(event);raise PermissionError('Offline extractor')
        if event=='open' and isinstance(args[0],(str,bytes)):
            path=str(Path(os.fsdecode(args[0])).resolve()).lower()
            if path not in allowed:
                blocked.append('file_read_outside_allowlist');raise PermissionError('Extractor file access denied')
            reads.append(path)
    sys.addaudithook(audit)
    tracemalloc.start(); inference_start=time.perf_counter()
    try:
        predictions,results,audits=extract_batch(inputs,rules,run_id,iv,pv)
    finally:
        guard['active']=False
    elapsed=time.perf_counter()-inference_start;_,peak=tracemalloc.get_traced_memory();tracemalloc.stop()
    jsonl(output_dir/'predictions.jsonl',predictions);jsonl(output_dir/'input_results.jsonl',results)
    jsonl(output_dir/'normalization_audit.jsonl',audits)
    json_file(output_dir/'run_manifest.json',dict(run_id=run_id,started_at=stamp,completed_at=now(),
            input_count=len(inputs),candidate_count=len(predictions),terminal_results=len(results),
            status_counts=dict(__import__('collections').Counter(r['status'] for r in results)),
            attempts=len(inputs),external_calls=0,network_disabled=True,reference_read_at=None,
            reference_access='not_read_by_extractor',inference_file_reads=reads,blocked_accesses=blocked,
            input_mode='preselected_cells',exposure='adaptation',human_gold=0,independent_evaluation='not_evaluated',
            code_sha256=codes,input_schema_registry_dependency_hashes=dependencies,
            output_hashes=hashes([output_dir/n for n in ('predictions.jsonl','input_results.jsonl','normalization_audit.jsonl')]),
            initialization_seconds=inference_start-start,inference_seconds=elapsed,
            total_seconds=time.perf_counter()-start,cpu_seconds=time.process_time()-cpu_start,
            peak_python_allocation_bytes=peak,resource_limitations='Python allocations only; OS peak RSS not measured',
            random_seed=None,seed_reason='deterministic_no_random_generator'))
    print(json.dumps(dict(run_id=run_id,inputs=len(inputs),candidates=len(predictions),statuses=[r['status'] for r in results if r['status']!='predicted'])))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--input-dir',type=Path,default=P4)
    parser.add_argument('--output-dir',type=Path,required=True);parser.add_argument('--run-id',required=True)
    args=parser.parse_args();execute(args.input_dir,args.output_dir,args.run_id)
