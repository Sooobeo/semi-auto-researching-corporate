"""Manifest-driven offline P04 contract/source verification and adverse cases.

No source prose is printed or persisted. JSON Schema is loaded from an isolated
dependency directory; pass --dependency-dir if it is absent from the environment.
"""
from __future__ import annotations
import argparse
import copy
import json
import os
import re
import sys
from collections import Counter
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from lxml import html
from p04_common import ROOT, OUT, SOURCE, REGISTRY, rows, sha, now, json_file, require_stage

def load_validator(dependency_dir=None):
    if dependency_dir: sys.path.insert(0,str(dependency_dir))
    try:
        from jsonschema import Draft202012Validator, FormatChecker
    except ModuleNotFoundError:
        dep=Path(os.environ['TEMP'])/'p02-jsonschema-20261005'
        if not dep.exists(): raise RuntimeError('jsonschema missing; use an isolated --dependency-dir')
        sys.path.insert(0,str(dep))
        from jsonschema import Draft202012Validator, FormatChecker
    return Draft202012Validator, FormatChecker

class Context:
    def __init__(self, artifact_dir, manifest, dependency_dir=None):
        V,F=load_validator(dependency_dir)
        self.artifact_dir=artifact_dir
        self.schema=json.loads((artifact_dir/'event_schema_v1.json').read_text(encoding='utf-8'))
        V.check_schema(self.schema); self.validator=V(self.schema,format_checker=F())
        self.docs={x['doc_id']:x for x in rows(manifest)}
        self.evidence={x['evidence_id']:x for x in rows(artifact_dir/'evidence_index.jsonl')}
        self.links={x['item_id']:x for x in rows(OUT/'event_claim_links.csv')}
        self.packets={x['item_id']:x for x in rows(artifact_dir/'source_packets.jsonl')}
        self.metrics={x['metric_id']:x for x in rows(REGISTRY/'metric_catalog.csv')}
        self.entities={x['entity_id'] for x in rows(REGISTRY/'entity_catalog.csv')}
        self.relations={x['relation_id']:x for x in rows(REGISTRY/'business_relations.jsonl')}
        self.source_claims={x['claim_id']:x for x in rows(SOURCE/'facts_v0_3.jsonl')}
        self.trees={}; self.hashes={}
        for d in self.docs.values():
            path=ROOT/d['storage_uri']; self.hashes[d['doc_id']]=sha(path)
            # Never parse the supplemental prose or reserved new release.
            if d['document_kind']=='earnings_press_release':
                self.trees[d['doc_id']]=html.fromstring(path.read_bytes())

    def check(self,r):
        errors=[]
        def check(ok,code):
            if not ok: errors.append(code)
        schema_errors=list(self.validator.iter_errors(r))
        if schema_errors:
            errors.extend('schema:'+('/'.join(str(p) for p in e.absolute_path) or 'root') for e in schema_errors)
        try:
            n=r['normalized']; p=r['provenance']; t=n['temporal']; raw=r['raw']
            relation=r['record_kind']=='business_relation'
            item=r['relation_id'] if relation else r['claim_id']
            check(r['claim_id'] in self.source_claims,'unknown_claim_id')
            check(item in self.links,'unknown_item_id')
            if item not in self.links or r['claim_id'] not in self.source_claims: return errors
            link=self.links[item]; source=self.source_claims[r['claim_id']]
            check(p['doc_id'] in self.docs,'unknown_doc_id')
            if p['doc_id'] not in self.docs: return errors
            d=self.docs[p['doc_id']]
            check(r['event_id']==link['event_id'] and r['event_family_id']==link['event_family_id'],'event_family_link')
            check(p['doc_id']==link['doc_id'] and p['revision_id']==d['revision_id'],'source_revision')
            check(p['source_sha256']==d['sha256']==self.hashes[d['doc_id']],'source_hash')
            check(n['company_id']=='US-MSFT' and n['company_id'] in self.entities,'company_id')
            check(n['scope_id']==source['scope_id'],'scope_source_mismatch')
            check(n['definition_version']==('msft-segment-presentation-fy'+d['fiscal_year'] if '-SEG-' in n['scope_id'] else 'us-financial-0.1'),'definition_version')
            check(r['annotation_status']=='agent_draft' and r['human_gold'] is False,'false_human_gold')
            check(r['exposure_status']=='adaptation','exposure_change')
            check(r['assessment']['author_kind']=='agent_draft','false_human_assessment')
            check(n['evidence_status']=='company_reported','evidence_overclaim')
            check(t['published_date']==d['published_date'] and t['published_at'] is None and t['time_precision']=='date' and t['available_at'] is None and t['timezone'] is None and t['utc_offset'] is None,'date_only_precision')
            check(t['observed_at']==d['observed_at'],'observation_date')
            refs=[x['evidence_id'] for x in p['evidence']]
            for e in p['evidence']:
                check(e['evidence_id'] in self.evidence,'unknown_evidence_id')
                if e['evidence_id'] in self.evidence:
                    check(all(e.get(k)==v for k,v in self.evidence[e['evidence_id']].items() if k not in ('evidence_kind','source_sha256')),'evidence_index_mismatch')
                check(e['doc_id']==p['doc_id'] and e['revision_id']==p['revision_id'],'evidence_source_revision')
                found=self.trees[p['doc_id']].xpath(e['location'])
                check(len(found)==1,'source_xpath')
                if len(found)==1:
                    text=found[0].text_content()
                    check(e['start'] is not None and e['end'] is not None and 0<=e['start']<e['end']<=len(text) and text[e['start']:e['end']]==e['selected_text'],'source_span_roundtrip')
                check(all(h in refs and h in self.evidence for h in e['header_refs']),'header_ref_resolution')
            packet=self.packets[item]
            check(packet['source_sha256']==p['source_sha256'] and packet['evidence_refs']==refs,'packet_linkage')
            dep=n['availability_dependencies']
            if source['scope_id']=='US-MSFT-CONSOLIDATED':
                check(len(dep)==1,'scope_dependency_missing')
                if dep:
                    support=self.docs.get(dep[0]['record_id'])
                    check(support is not None,'unknown_dependency')
                    if support:
                        check(dep[0]['available_at']==support['observed_at'] and dep[0]['published_date'] is None,'scope_dependency_time')
                        check(datetime.fromisoformat(r['assessment']['as_of'])>=datetime.fromisoformat(dep[0]['available_at']),'future_scope_in_assessment')
            else: check(dep==[],'unexpected_scope_dependency')
            # Decode period directly from the selected source header/year, not mapper answers.
            ph=' '.join(packet['raw']['period_header'].split())
            yh=packet['raw']['year_header']
            years=re.findall(r'20\d{2}',yh); check(len(years)==1,'year_header_ambiguous')
            year=int(years[0]); instant='Months Ended' not in ph
            quarter='Three Months Ended' in ph
            end=date(year,6,30); start=date(year if quarter else year-1,4 if quarter else 7,1)
            expect=dict(period_start=None if instant else start.isoformat(),period_end=None if instant else end.isoformat(),as_of_date=end.isoformat() if instant else None,period_basis='fiscal',period_kind='instant' if instant else 'quarter' if quarter else 'annual',fiscal_year=year,fiscal_quarter=4 if quarter else None,duration_days=None if instant else (end-start).days+1,missing_reason=None)
            check(t['reference_period']==expect,'period_header_mapping')
            if relation:
                sr=self.relations[item]
                check(all(n[k]==sr[k] for k in ('subject_entity_id','object_entity_id','subject_role','object_role','relation_type','scope_id','negation','modality')) and n['direction']=='subject_to_object','relation_direction_roles')
                check(n['subject_entity_id'] in self.entities and n['object_entity_id'] in self.entities,'relation_entity_refs')
                check(n['valid_from'] is None and n['valid_to'] is None and t['effective_period']['period_kind']=='unknown' and t['effective_period']['period_start'] is None and t['effective_period']['period_end'] is None,'report_period_not_effective_period')
                check(raw['source_effective_period']==sr['effective_period'],'relation_source_sidecar')
            else:
                check(n['metric_id'] in self.metrics,'unknown_metric_id')
                check(n['metric_id']==source['metric_id'],'metric_source_mismatch')
                check(n['consolidation']==('segment' if '-SEG-' in n['scope_id'] else 'consolidated'),'consolidation_scope')
                check(n['currency']=='USD' and n['canonical_unit']=='USD' and n['scale']=='1' and n['source_scale']=='1000000','unit_scale')
                check(raw['value_raw']==source['value_raw'],'raw_value_preserved')
                signed=Decimal(raw['value_raw'].replace(',','').replace('$','').replace('(','-').replace(')',''))
                check(Decimal(n['source_numeric_value'])==signed,'source_numeric_sign')
                capex=n['metric_id']=='positive_cash_capex'
                target=(-signed if capex else signed)*Decimal('1000000')
                check(Decimal(n['numeric_value'])==target,'value_scaling_sign')
                check(n['sign_policy']==('outflow_to_positive' if capex else 'preserve'),'sign_policy')
                check(n['financial_context']['period_duration']==expect['duration_days'],'balance_duration')
                value_e=[e for e in p['evidence'] if self.evidence.get(e['evidence_id'],{}).get('evidence_kind')=='numeric_value']
                check(len(value_e)==1 and len(value_e[0]['header_refs'])==4,'numeric_header_binding')
                if value_e:
                    e=value_e[0]; original=self.trees[p['doc_id']].xpath(e['location'])[0].text_content()
                    check(packet['raw']['value_cell']==original,'packet_original_cell')
                check(len(r['derived'])==1 and r['derived'][0]['output']==n['numeric_value'] and r['derived'][0]['reviewed_by'] is None,'derived_lineage')
        except (KeyError,TypeError,ValueError,IndexError) as exc:
            errors.append('malformed_record:'+type(exc).__name__)
        return sorted(set(errors))

def negatives(ctx,records):
    numeric=next(r for r in records if r['record_kind']=='event_claim')
    capex=next(r for r in records if r['normalized'].get('metric_id')=='positive_cash_capex')
    relation=next(r for r in records if r['record_kind']=='business_relation')
    segment=next(r for r in records if r['normalized'].get('metric_id')=='revenue' and '-SEG-' in r['normalized']['scope_id'])
    cases=[]
    def case(name,base,path,value,expect):
        record=copy.deepcopy(base); target=record
        for key in path[:-1]: target=target[key]
        target[path[-1]]=value
        errors=ctx.check(record)
        cases.append(dict(case_id=name,mutation_path=path,expected_rejection=expect,rejected=bool(errors),expected_reason_detected=any(expect in x for x in errors),errors=errors))
    case('span_shift',numeric,['provenance','evidence',0,'start'],1,'source_span_roundtrip')
    case('missing_claim',numeric,['claim_id'],'DOES-NOT-EXIST','unknown_claim_id')
    case('missing_metric',numeric,['normalized','metric_id'],'DOES-NOT-EXIST','unknown_metric_id')
    case('wrong_scope',numeric,['normalized','scope_id'],'US-MSFT-SEG-IC','scope_source_mismatch')
    case('wrong_definition',segment,['normalized','definition_version'],'us-financial-0.1','definition_version')
    case('fabricated_timestamp',numeric,['normalized','temporal','published_at'],'2024-07-30T00:00:00Z','date_only_precision')
    case('future_scope_dependency',numeric,['normalized','availability_dependencies',0,'available_at'],'2024-07-30T00:00:00Z','scope_dependency_time')
    case('past_asof_using_scope',numeric,['assessment','as_of'],'2024-07-30T23:59:59Z','future_scope_in_assessment')
    case('reverse_relation',relation,['normalized','subject_entity_id'],relation['normalized']['object_entity_id'],'relation_direction_roles')
    case('fabricated_relation_effective',relation,['normalized','temporal','effective_period','period_start'],'2023-07-01','report_period_not_effective_period')
    case('null_without_reason',numeric,['normalized','numeric_value'],None,'schema:normalized/missing_reason')
    case('false_gold',numeric,['human_gold'],True,'false_human_gold')
    case('false_human',numeric,['annotation_status'],'independent_human','false_human_gold')
    case('capex_negative_normalized',capex,['normalized','numeric_value'],'-13873000000','value_scaling_sign')
    case('scale_million_twice',numeric,['normalized','scale'],'1000000','unit_scale')
    case('wrong_period_year',numeric,['normalized','temporal','reference_period','fiscal_year'],2025,'period_header_mapping')
    case('unknown_header_ref',numeric,['provenance','evidence',0,'header_refs'],['NO-EVIDENCE'],'header_ref_resolution')
    case('wrong_hash',numeric,['provenance','source_sha256'],'0'*64,'source_hash')
    case('evidence_externally_verified',numeric,['normalized','evidence_status'],'externally_verified','evidence_overclaim')
    return cases

def run(args):
    require_stage(1)
    if args.report.exists(): raise FileExistsError('Refusing to overwrite validation report')
    ctx=Context(args.artifact_dir,args.manifest,args.dependency_dir)
    records=rows(args.artifact_dir/'contract_records.jsonl')
    findings=[dict(record_id=r['record_id'],errors=errors) for r in records if (errors:=ctx.check(r))]
    ids=[r['record_id'] for r in records]
    counts=Counter(r['record_kind'] for r in records)
    checks=dict(records_unique=len(ids)==len(set(ids)),numeric_conservation=counts['event_claim']==len(ctx.source_claims),relation_conservation=counts['business_relation']==len(ctx.relations),item_link_coverage={r['relation_id'] or r['claim_id'] for r in records}==set(ctx.links),packet_coverage=set(ctx.packets)==set(ctx.links),unique_source_claims=len({r['claim_id'] for r in records})==len(ctx.source_claims),source_hashes=all(d['sha256']==ctx.hashes[d['doc_id']] for d in ctx.docs.values()),human_gold_zero=not any(r['human_gold'] for r in records))
    cases=negatives(ctx,records)
    checks['negative_cases_rejected']=all(x['rejected'] and x['expected_reason_detected'] for x in cases)
    baseline=None
    if args.baseline:
        V,F=load_validator(args.dependency_dir)
        b=V(json.loads((ROOT/'artifacts/us_equity/p1/event_schema_v0.1.json').read_text(encoding='utf-8')),format_checker=F())
        baseline=dict(records_tested=len(records),records_rejected=sum(not b.is_valid(r) for r in records),interpretation='Expected v0.1 migration incompatibility: reports_segment and explicit extension fields/version require P04 schema. No claim that baseline was production-compatible.')
    result=dict(checked_at=now(),status='passed_with_explicit_limitations' if not findings and all(checks.values()) else 'needs_improvement',schema_sha256=sha(args.artifact_dir/'event_schema_v1.json'),records_sha256=sha(args.artifact_dir/'contract_records.jsonl'),source_manifest=str(args.manifest.relative_to(ROOT)),counts=dict(records=len(records),numeric_records=counts['event_claim'],relation_records=counts['business_relation'],unique_source_claims=len({r['claim_id'] for r in records}),unique_events=len({r['event_id'] for r in records}),evidence=len(ctx.evidence),packets=len(ctx.packets),human_gold=0),checks=checks,findings=findings,baseline_compatibility=baseline,negative_cases=dict(attempted=len(cases),rejected=sum(x['rejected'] for x in cases),expected_reason_detected=sum(x['expected_reason_detected'] for x in cases)),limitations=['independent human annotation and manual visual audit absent','whole body completeness not audited','date-only release timing','segment presentation policy unresolved','scope supplement unavailable at historical release cutoff'],original_prose_exported=False,reserved_content_read=False)
    json_file(args.report,result)
    if args.cases: json_file(args.cases,cases)
    print(json.dumps({'status':result['status'],'records':len(records),'findings':len(findings),'negative_cases':result['negative_cases']}))
    return 0 if result['status']=='passed_with_explicit_limitations' else 1

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--artifact-dir',type=Path,default=OUT); p.add_argument('--manifest',type=Path,default=SOURCE/'document_manifest_v0_3.csv');p.add_argument('--report',type=Path,required=True);p.add_argument('--cases',type=Path);p.add_argument('--baseline',action='store_true');p.add_argument('--dependency-dir',type=Path)
    raise SystemExit(run(p.parse_args()))
