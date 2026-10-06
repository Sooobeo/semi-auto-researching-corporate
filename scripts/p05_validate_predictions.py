"""Offline source-location and candidate verification; never prints source prose."""
from __future__ import annotations
import argparse
from decimal import Decimal
from pathlib import Path
from lxml import html
from p05_common import *
from p05_input_validation import check_input
from p05_rule_baseline import parse_number, parse_period

class ValidationContext:
    def __init__(self,input_dir=P4):
        self.out=input_dir
        self.inputs={r['input_id']:r for r in rows(input_dir/'extractor_inputs.jsonl')}
        self.rules=read_json(input_dir/'rules_v0_1.json')
        self.iv=validator(read_json(input_dir/'input_schema.json'))
        self.pv=validator(read_json(input_dir/'prediction_schema.json'))
        self.maps={r['evidence_id']:r for r in rows(input_dir/'evidence_map.jsonl')}
        self.source_evidence={r['evidence_id']:r for r in rows(P3/'evidence_index.jsonl')}
        docs={d['doc_id']:d for d in rows(SOURCE/'document_manifest_v0_3.csv')}
        self.trees={};self.source_hashes={}
        for doc in self.rules['documents']:
            d=docs[doc];path=ROOT/d['storage_uri']
            self.source_hashes[doc]=sha(path)
            self.trees[doc]=html.fromstring(path.read_bytes())
        self.input_errors={k:self.check_source(v) for k,v in self.inputs.items()}

    def check_source(self,r):
        errors=check_input(r,self.iv)
        if errors: return errors
        if r['doc_id'] not in self.trees: return ['source_not_allowlisted']
        if self.source_hashes[r['doc_id']]!=r['source_sha256']:errors.append('source_hash')
        for e in r['evidence']:
            m=self.maps.get(e['evidence_id'])
            if not m:
                errors.append('unknown_evidence');continue
            old=self.source_evidence[m['p04_evidence_id']]
            if any(e[k]!=m[k] for k in ('location','start','end','kind')):errors.append('evidence_map_mismatch')
            if m['doc_id']!=r['doc_id'] or m['revision_id']!=r['revision_id']:errors.append('evidence_document_mismatch')
            for k in ('location','start','end','selected_text','table_id','row_index','col_index'):
                if e[k]!=old[k]:errors.append('source_evidence_'+k)
            found=self.trees[r['doc_id']].xpath(e['location'])
            if len(found)!=1:errors.append('source_xpath');continue
            text=found[0].text_content()
            if text[e['start']:e['end']]!=e['selected_text']:errors.append('source_span_roundtrip')
            if e['kind']=='numeric_value':
                if text!=r['raw']['value_cell']:errors.append('source_numeric_cell')
                actual=[self.maps[h]['p04_evidence_id'] for h in e['header_refs'] if h in self.maps]
                if actual!=old['header_refs']:errors.append('source_header_binding')
        return sorted(set(errors))

    def check(self,p):
        errors=['schema:'+e.json_path for e in self.pv.iter_errors(p)]
        if errors:return sorted(set(errors))
        r=self.inputs.get(p['input_id'])
        if not r:return ['unknown_input_id']
        errors+=self.input_errors[p['input_id']]
        def check(ok,code):
            if not ok:errors.append(code)
        n=p['normalized'];raw=p['raw'];rules=self.rules;ctx=r['context'];relation=r['input_kind']=='relation_context'
        doc=rules['documents'][r['doc_id']]
        check(p['status']=='predicted','candidate_not_predicted')
        check(p['record_kind']==('reporting_relation' if relation else 'numeric_claim'),'record_kind')
        check(p['doc_id']==r['doc_id'] and p['revision_id']==r['revision_id'],'prediction_source_identity')
        check(p['synthetic']==r['synthetic'],'synthetic_status')
        check(p['registry_version']==rules['registry_version'] and p['rule_version']==rules['rule_version'],'version_mismatch')
        check(p['provenance']['source_sha256']==r['source_sha256'],'prediction_source_hash')
        check(p['provenance']['source_url']==doc['source_url'] and p['provenance']['rights_basis_ref']==doc['rights_basis_ref'],'source_provenance')
        check(p['provenance']['context_provenance_ref']==ctx['context_provenance_ref'],'context_provenance')
        check(p['provenance']['leakage_group']==rules['leakage_group'],'exposure_group')
        check(p['evidence_refs']==[e['evidence_id'] for e in r['evidence']],'prediction_evidence_refs')
        check(all(raw[k]==r['raw'][k] for k in ('value_cell','row_label','period_header','year_header','unit_header')),'raw_preservation')
        check(raw['source_qualifier']==ctx['source_qualifier'],'source_qualifier_preservation')
        check(n['company_id']==rules['company_id'],'company_id')
        segment=ctx['table_purpose']=='segment_revenue';label=' '.join(r['raw']['row_label'].split())
        scope=rules['segment_labels'].get(label) if segment else rules['company_scope_id']
        check(n['scope_id']==scope,'scope_mapping')
        check(n['definition_version']==(doc['segment_definition'] if segment else 'us-financial-0.1'),'presentation_definition')
        check(n['availability_dependencies']==([] if segment else rules['scope_dependencies']),'availability_dependency')
        check(n['scope_status_as_of']==('reported_segment_in_selected_table' if segment else 'unresolved_retrospective_dependency'),'scope_cutoff_status')
        t=n['temporal']
        check(all(t[k]==r['publication'][k] for k in r['publication']),'publication_preservation')
        expected=parse_period(r['raw']['period_header'],r['raw']['year_header'])
        check(t['reference_period']==expected,'reporting_period')
        check(t['effective_period'] is None and n['valid_from'] is None and n['valid_to'] is None,'effective_date_invention')
        check(not n['negation'] and n['conditions']==[],'unsupported_negation_or_condition')
        check(p['assessment']['review_readiness']=='needs_review' and p['assessment']['probability'] is None,'confidence_overclaim')
        for path in ('normalized.temporal.published_at','normalized.temporal.timezone','normalized.temporal.available_at',
                     'normalized.temporal.effective_period','normalized.valid_from','normalized.valid_to','assessment.probability'):
            check(bool(p['field_missing_reasons'].get(path)),'missing_reason:'+path)
        if relation:
            check(n['relation_type']=='reports_segment' and n['subject_entity_id']==rules['company_id'] and n['object_entity_id']==scope,'relation_endpoints')
            check(n['subject_role']=='reporting_company' and n['object_role']=='reported_segment' and n['direction']=='subject_to_object','relation_roles_direction')
            check(n['numeric_value'] is None and n['metric_id'] is None,'relation_not_numeric_claim')
            check(p['candidate_relation_id'] is not None and p['candidate_claim_id'] is None,'candidate_identity_kind')
        else:
            mr=dict(metric_id='revenue',balance_or_flow='flow',statement_type='segment_revenue',sign_policy='preserve') if segment else rules['metric_labels'][label]
            check(all(n[k]==mr[k] for k in mr),'metric_rules')
            signed=parse_number(r['raw']['value_cell']);scaled=(-signed if mr['sign_policy']=='outflow_to_positive' else signed)*Decimal(rules['units'][r['raw']['unit_header']])
            check(Decimal(n['numeric_value'])==scaled,'numeric_value')
            check(n['scale']=='1' and n['source_scale']==rules['units'][r['raw']['unit_header']],'unit_scale')
            check(Decimal(n['source_numeric_value'])==signed,'source_sign')
            check(n['currency']=='USD' and n['canonical_unit']=='USD' and n['accounting_basis']==ctx['accounting_basis'],'currency_accounting')
            ve=next(e for e in r['evidence'] if e['kind']=='numeric_value')
            check(raw['value_raw']==ve['selected_text'] and raw['value_span_start']==ve['start'] and raw['value_span_end']==ve['end'],'value_span')
            check(p['candidate_claim_id'] is not None and p['candidate_relation_id'] is None,'candidate_identity_kind')
            check(len(p['derived'])>=1 and p['derived'][0]['output']==n['numeric_value'],'derived_numeric_lineage')
        if expected['period_start']:
            check(any(d['formula_id']=='calendar_months_from_three_or_twelve_month_header' and d['output']==expected['period_start'] for d in p['derived']),'derived_period_lineage')
        return sorted(set(errors))

def validate_run(ctx,predictions,results):
    findings=[]
    for p in predictions:
        try: errors=ctx.check(p)
        except (KeyError,ValueError,TypeError,ArithmeticError) as exc: errors=['malformed_prediction:'+type(exc).__name__]
        if errors:findings.append(dict(prediction_id=p.get('prediction_id'),errors=errors))
    ids=[r.get('input_id') for r in results];pids=[p.get('prediction_id') for p in predictions]
    checks=dict(input_sources=not any(ctx.input_errors.values()),unique_results=len(ids)==len(set(ids)),
                all_inputs_have_terminal_result=set(ids)==set(ctx.inputs),unique_predictions=len(pids)==len(set(pids)),
                predictions_reference_known_inputs=all(p.get('input_id') in ctx.inputs for p in predictions),
                terminal_status_valid=all(r.get('status') in ('predicted','abstained','failed','quarantined') for r in results),
                terminal_prediction_links=all(r.get('prediction_ids')==[p['prediction_id'] for p in predictions if p['input_id']==r['input_id']]
                                              and r.get('candidate_count')==len(r.get('prediction_ids',[])) for r in results),
                predicted_result_has_candidate=all(r['status']!='predicted' or r['candidate_count']>0 for r in results),
                candidate_status_matches_result=all(p.get('status')==r.get('status') for r in results for p in predictions if p.get('input_id')==r.get('input_id')),
                no_candidate_validation_errors=not findings)
    return dict(checked_at=now(),status='passed_with_explicit_limitations' if all(checks.values()) else 'needs_improvement',
                input_count=len(ctx.inputs),result_count=len(results),candidate_count=len(predictions),
                checks=checks,findings=findings,input_findings=ctx.input_errors,
                source_locations_requeried=len({m['p04_evidence_id'] for m in ctx.maps.values()}),
                source_role_bindings=len(ctx.maps),manual_body_audits=0,date_conflict_audits=0,
                independent_evaluation='not_evaluated')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--input-dir',type=Path,default=P4)
    parser.add_argument('--run-dir',type=Path,required=True);parser.add_argument('--report',type=Path)
    args=parser.parse_args();ctx=ValidationContext(args.input_dir)
    report=validate_run(ctx,rows(args.run_dir/'predictions.jsonl'),rows(args.run_dir/'input_results.jsonl'))
    json_file(args.report or args.run_dir/'validation_report.json',report)
    print(json.dumps({k:report[k] for k in ('status','input_count','candidate_count','checks')}))
    raise SystemExit(0 if all(report['checks'].values()) else 1)
