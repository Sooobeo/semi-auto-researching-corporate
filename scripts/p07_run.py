"""P07 CLI: file store, exact/sparse priors, guarded changes and calculations."""
from __future__ import annotations
import argparse
from collections import Counter
from p06_common import *
from p07_engine import *
from p07_test_engine import test_cases

def no_prior(new,q,policy):
    return {'change_id':stable('CH',new['record_id'],q['cutoff_mode'],'no-prior',policy['version']),
        'new_record_id':new['record_id'],'prior_record_id':None,'comparison_basis':'relation_state' if new['record_kind']=='business_relation' else 'prior_search',
        'cutoff_mode':q['cutoff_mode'],'cutoff':q['cutoff'],'new_doc_id':new['doc_id'],'prior_doc_id':None,
        'new_revision_id':new['revision_id'],'prior_revision_id':None,'compatibility':{'decision':'needs_review','checks':{},'reasons':[q['status']]},
        'status':'withheld','reasons':[q['status']]+q['query_availability']['reasons'],'old_value':None,
        'new_value':new['normalized'].get('numeric_value'),'delta':None,'relative_delta':None,'relative_delta_missing_reason':'prior_not_available',
        'change_types':['prior_not_found_in_limited_corpus'],'unit':new['normalized'].get('canonical_unit'),
        'evidence_refs':new['evidence_refs'],'formula_id':None,'policy_version':policy['version'],'review_readiness':'needs_review',
        'evidence_status':new['normalized']['evidence_status'],'historical_eligible':False,'source_record_refs':[new['record_id']], 'origin':'derived','correction_confirmed':False}

def compute(data,cutoff_mode='all',cutoff=None,policy=POLICY):
    modes=MODES if cutoff_mode=='all' else (cutoff_mode,);by_id={r['record_id']:r for r in data}
    retrieval=[];prior=[];changes=[];calculations=[];reconciliations=[]
    for mode in modes:
        review_cutoff=cutoff or ('2026-10-06' if mode=='current_review' else None)
        for new in data:
            result=[retrieve(new,data,mode,review_cutoff,m) for m in ('exact_key','local_label_tfidf')]
            retrieval.extend(result);q=result[0]
            # Preserve incompatible comparator candidates for review; they are not selected priors.
            candidates=q['candidates']
            selected=q['selected_record_id']; comparator=selected
            if not comparator and candidates:
                np=new['normalized']['temporal']['reference_period']
                aligned=[c for c in candidates if by_id[c['record_id']]['normalized']['temporal']['reference_period']['period_kind']==np['period_kind']]
                comparator=(aligned or candidates)[0]['record_id']
            prior.append({'query_id':q['query_id'],'new_record_id':new['record_id'],'cutoff_mode':mode,'cutoff':q['cutoff'],
                'selected_prior_id':selected,'review_comparator_id':comparator,'status':q['status'],
                'reason':q['query_availability']['reasons'],'candidate_count':len(candidates),'excluded_count':len(q['excluded'])})
            if comparator:
                old=by_id[comparator];np=new['normalized']['temporal']['reference_period'];op=old['normalized']['temporal']['reference_period']
                basis='relation_state' if new['record_kind']=='business_relation' else ('same_period_revision' if np==op else 'yoy')
                changes.append(change(new,old,basis,mode,q['cutoff'],policy))
            else:changes.append(no_prior(new,q,policy))
        # Explicit within-release comparisons are separated from independent prior retrieval.
        numeric=[r for r in data if r['record_kind']=='event_claim' and r['normalized']['scope_id'].startswith('US-MSFT-SEG')]
        for new in numeric:
            for old in numeric:
                if new['doc_id']==old['doc_id'] and key(new)==key(old) and new['normalized']['temporal']['reference_period']['fiscal_year']==old['normalized']['temporal']['reference_period']['fiscal_year']+1:
                    asof=review_cutoff or new['normalized']['temporal']['published_date']
                    changes.append(change(new,old,'within_release_comparison',mode,asof,policy))
        groups={}
        for r in data:
            if r['record_kind']=='event_claim' and r['normalized']['scope_id']=='US-MSFT-CONSOLIDATED' and r['normalized']['balance_or_flow']=='flow':
                groups.setdefault((r['doc_id'],digest(r['normalized']['temporal']['reference_period'])),[]).append(r)
        for group in groups.values():
            asof=review_cutoff or group[0]['normalized']['temporal']['published_date']
            for f in ('operating_margin','project_fcf'):
                roles={'operating_margin':{'operating_income','revenue'},'project_fcf':{'cfo','positive_cash_capex'}}[f]
                inputs=[r for r in group if r['normalized']['metric_id'] in roles]
                calculations.append(calculate(f,inputs,mode,asof))
            reconciliations.append({'reconciliation_id':stable('REC',mode,*[r['record_id'] for r in group]),'company_id':'US-MSFT',
                'scope_id':'US-MSFT-CONSOLIDATED','target_period':group[0]['normalized']['temporal']['reference_period'],
                'cutoff_mode':mode,'as_of':asof,'reconciliation_type':'net_income_to_cfo','formula_id':'net_income_plus_adjustments',
                'formula_version':'0.1','input_refs':[r['record_id'] for r in group if r['normalized']['metric_id'] in ('net_income','cfo')],
                'reported_target_claim_id':None,'calculated_value':None,'reported_value':None,'residual':None,
                'completeness_status':'incomplete','reconciliation_status':'incomplete','missing_inputs':['noncash_adjustments','working_capital_adjustments','reconciliation_target_audit'],
                'prepared_by':'program','reviewed_by':None,'evidence_refs':sorted(set(e for r in group for e in r['evidence_refs']))})
    return retrieval,prior,changes,calculations,reconciliations

def regression(data,changes):
    # Only called after semantic results have been written and hashed.
    p=ROOT/'artifacts/us_equity/p2/applied_002/comparability_results.jsonl';original=rows(p);byid={r['record_id']:r for r in data};out=[]
    for c in changes:
        if c['cutoff_mode']!='current_review' or not c['prior_record_id'] or c['comparison_basis']=='relation_state':continue
        new=byid[c['new_record_id']];n=new['normalized'];period=n['temporal']['reference_period']
        if n['scope_id']=='US-MSFT-CONSOLIDATED':
            keyid='YOY-'+n['metric_id']+'-'+({'quarter':'Q4','annual':'FY','instant':'instant'}[period['period_kind']])
        else:
            prefix={'yoy':'SEG-OLD-TO-NEW-','same_period_revision':'SEG-OLD-TO-REVISED-PRIOR-','within_release_comparison':'SEG-ALIGNED-PRESENTATION-'}[c['comparison_basis']]
            keyid=prefix+n['scope_id']
        ref=next(r for r in original if r['pair_id']==keyid)
        decision=c['compatibility']['decision']
        out.append({'pair_id':keyid,'change_id':c['change_id'],'decision_match':decision==ref['decision'],
            'delta_match':c['delta']==ref['delta'],'relative_delta_match':c['relative_delta']==ref['relative_delta'],
            'development_regression_only':True})
    return {'source_path':p.relative_to(ROOT).as_posix(),'source_sha256':sha(p),'rows':out,
        'matched':sum(r['decision_match'] and r['delta_match'] and r['relative_delta_match'] for r in out),'total':len(original),
        'independent_evaluation_count':0}

def run(source_run,run_dir,cutoff_mode='all',cutoff=None,policy=None):
    data,snap=audit_p05(source_run);policy=policy or dict(POLICY)
    retrieval,prior,changes,calcs,recs=compute(data,cutoff_mode,cutoff,policy);path=new_run(run_dir)
    save(path/'input_snapshot.json',snap);save(path/'asof_policy.json',dict(policy,modes=MODES if cutoff_mode=='all' else [cutoff_mode],cutoff_override=cutoff))
    jsonl(path/'event_store_records.jsonl',data);jsonl(path/'retrieval_results.jsonl',retrieval);jsonl(path/'retrieval_review_candidates.jsonl',[r for r in retrieval if r['method']=='exact_key'])
    jsonl(path/'prior_state_records.jsonl',prior);jsonl(path/'change_records.jsonl',changes)
    jsonl(path/'numeric_changes.jsonl',[c for c in changes if c['comparison_basis']!='relation_state'])
    jsonl(path/'qualitative_changes.jsonl',[c for c in changes if c['comparison_basis']=='relation_state'])
    jsonl(path/'calculation_results.jsonl',calcs);jsonl(path/'financial_reconciliations.jsonl',recs);jsonl(path/'research_assumptions.jsonl',[])
    scenarios=[dict(scenario('revenue_from_units_asp',{}),scenario_id='SC-no-inputs',synthetic=False,assumptions_status='not_provided')]
    jsonl(path/'scenario_runs.jsonl',scenarios);jsonl(path/'asof_query_cases.jsonl',[{'query_id':r['query_id'],'cutoff_mode':r['cutoff_mode'],'cutoff':r['cutoff'],'query_availability':r['query_availability']} for r in retrieval if r['method']=='exact_key'])
    tests=test_cases(data);save(path/'synthetic_tests.json',tests)
    summary={'candidates':len(data),'numeric_candidates':sum(r['record_kind']=='event_claim' for r in data),'relation_candidates':sum(r['record_kind']=='business_relation' for r in data),
        'documents':len({r['doc_id'] for r in data}),'families':len({r['event_family_id'] for r in data}),'queries':len(retrieval),
        'retrieval_statuses':dict(Counter(r['status'] for r in retrieval)),'modes':{},'human_qrels':0,'human_change_gold':0,'independent_test':0,'recall_at_k':None,'change_accuracy':None,
        'scenario_computed':0,'scenario_attempts':len(scenarios),'reconciliation_complete':0,'reconciliation_attempts':len(recs),'new_source_requests':0}
    for mode in (MODES if cutoff_mode=='all' else [cutoff_mode]):
        qq=[r for r in retrieval if r['cutoff_mode']==mode];cc=[c for c in changes if c['cutoff_mode']==mode];ff=[f for f in calcs if f['cutoff_mode']==mode]
        summary['modes'][mode]={'queries':len(qq),'selected_queries':sum(r['status']=='selected' for r in qq),
            'queries_with_candidates':sum(bool(r['candidates']) for r in qq),'excluded_candidates':sum(len(r['excluded']) for r in qq),
            'changes':len(cc),'paired_comparisons':sum(c['prior_record_id'] is not None for c in cc),
            'comparable_pairs':sum(c['compatibility']['decision']=='comparable' for c in cc),
            'not_comparable_pairs':sum(c['compatibility']['decision']=='not_comparable' for c in cc),
            'computed_changes':sum(c['status']=='computed' for c in cc),'withheld_changes':sum(c['status']!='computed' for c in cc),
            'formula_attempts':len(ff),'formula_computed':sum(f['status']=='computed' for f in ff)}
    registry=[{'formula_id':'absolute_and_relative_delta','version':'0.1','input_roles':'new,old','expression':'new-old; delta/abs(old)', 'unit':'same base unit; relative=fraction','period_scope':'same actual period or calendar-anniversary yoy','rounding':'28 significant digits HALF_EVEN','output_kind':'derived_change'},
        {'formula_id':'operating_margin','version':'0.1','input_roles':'operating_income,revenue','expression':'operating_income/revenue','unit':'fraction','period_scope':'same company/consolidated/actual period','rounding':'28 significant digits HALF_EVEN','output_kind':'project_ratio'},
        {'formula_id':'project_fcf','version':'0.1','input_roles':'cfo,positive_cash_capex','expression':'cfo-positive_cash_capex','unit':'USD scale=1','period_scope':'same company/consolidated/actual period','rounding':'exact subtraction','output_kind':'project_fcf_not_company_reported'},
        {'formula_id':'revenue_from_units_asp','version':'0.1','input_roles':'units,asp,scope_id,target_period,currency,assumption_refs','expression':'units*asp','unit':'explicit currency','period_scope':'same future scope/period; reviewed assumptions','rounding':'28 significant digits HALF_EVEN','output_kind':'derived_forecast'}]
    csvfile(path/'calculation_registry.csv',list(registry[0]),registry);csvfile(path/'retrieval_qrels.csv',['query_id','prior_record_id','relevance','human_reviewer'],[])
    schema={'$schema':'https://json-schema.org/draft/2020-12/schema','type':'object',
        'required':['change_id','new_record_id','prior_record_id','compatibility','status','delta','relative_delta','evidence_refs','cutoff_mode'],
        'properties':{'status':{'enum':['computed','withheld']},'cutoff_mode':{'enum':list(MODES)},'delta':{'type':['string','null']},'relative_delta':{'type':['string','null']},'review_readiness':{'const':'needs_review'}},
        'allOf':[{'if':{'properties':{'status':{'const':'withheld'}}},'then':{'properties':{'delta':{'type':'null'},'relative_delta':{'type':'null'}}}}]}
    save(path/'change_schema.json',schema);save(path/'event_store_schema.json',{'required':['record_id','doc_id','revision_id','raw','normalized','assessment','derived','evidence_refs'],'record_id_unique':True,'revision_immutable':True,'source':'P05 candidate extension; not human gold'})
    semantic=['event_store_records.jsonl','retrieval_results.jsonl','prior_state_records.jsonl','change_records.jsonl','calculation_results.jsonl','financial_reconciliations.jsonl','scenario_runs.jsonl']
    before={name:sha(path/name) for name in semantic};save(path/'output_freeze_before_regression.json',{'hashes':before,'frozen_at':now()})
    reg=regression(data,changes);save(path/'p03_regression.json',reg)
    checks={'all_modes_all_candidates_accounted':len(prior)==len(data)*(3 if cutoff_mode=='all' else 1),
        'no_duplicate_change_ids':len(changes)==len({c['change_id'] for c in changes}),
        'references_resolve':all(set(c['source_record_refs'])<={r['record_id'] for r in data} for c in changes),
        'withheld_numeric_outputs_null':all(c['delta'] is c['relative_delta'] is None for c in changes if c['status']!='computed'),
        'relation_no_numeric_delta':all(c['delta'] is None and c['relative_delta'] is None for c in changes if c['comparison_basis']=='relation_state'),
        'reconciliations_incomplete_not_success':all(r['residual'] is None and r['reconciliation_status']=='incomplete' for r in recs),
        'no_human_gold_invented':summary['human_qrels']==summary['human_change_gold']==0,
        'outputs_frozen_before_p03_regression':all(sha(path/n)==h for n,h in before.items()),
        'p03_regression_complete':reg['matched']==reg['total']==21 if cutoff_mode in ('all','current_review') and cutoff is None else True,
        'synthetic_counterexamples':all(c['passed'] for c in tests['cases'])}
    save(path/'validation_report.json',{'checks':checks,'synthetic_cases':len(tests['cases']),'summary':summary})
    for name,body in {
        'retrieval_protocol.md':'# 검색 계약\n\n39개 후보의 표준 라벨/선택 셀 file store. exact key와 local label TF-IDF는 동일 동결 corpus·cutoff 사용. 원문 전체 검색 아님. 후보와 독립 사람 qrels 분리; qrels 파일은 header-only이며 미실행. no-hit는 제한 corpus 안에서만 의미.',
        'retrieval_benchmark.md':'# 검색 개발 보고\n\n독립 qrels 0: Recall@k=null. dense/hybrid/reranker 미실행. 실제 분모와 모드별 제외는 run_manifest.summary.modes와 retrieval_results에 저장.',
        'change_benchmark.md':'# 변화 개발 보고\n\n독립 사람 change gold 0: 정확도 null. P03 같은 adaptation 자료 21행 회귀는 독립 검색 평가가 아님. 서로 다른 비교 종류 유지.',
        'reproducibility_report.md':'# 재현\n\nDecimal 28자리 HALF_EVEN; USD base scale 1. 원 배율 다시 곱하지 않음. 미래 revision 반례 차단. 별도 run semantic_hash 비교; 동료 재실행 미실행.',
        'handoff_p6.md':'# P07 → P06/P08\n\nchange_records는 stable change ID/new/prior/revision/evidence/policy/모드 연결. current_review 기본; historical/observed 결과와 분리. 계산 성공도 needs_review 유지. 관계 유효시점 null, 독립 qrels/gold 없음. P06 후속 run에서만 change feature 연결. 게시 기록 별도.',
        'readiness_report.md':'# 범위\n\nMicrosoft release 2개·family 2개·숫자 33/관계 6. 신규 자료 수집 0, reserved FY2026 Q1 본문 미열람. 기존 최소 사실 참조만 사용. 사람 검토·정식 benchmark 미완료.',
    }.items():textfile(path/name,body)
    if not all(checks.values()):raise ValueError('P07 checks failed: '+str([k for k,v in checks.items() if not v]))
    m=freeze(path,'P07',policy,snap,summary,semantic)
    print(json.dumps({'status':'development_ready','run_id':path.name,'summary':summary},ensure_ascii=False));return m

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-run',default='m0_004');p.add_argument('--run-dir',required=True,type=Path)
    p.add_argument('--cutoff-mode',choices=['all',*MODES],default='all');p.add_argument('--cutoff');p.add_argument('--policy',type=Path);a=p.parse_args()
    run(a.source_run,a.run_dir,a.cutoff_mode,a.cutoff,read(a.policy) if a.policy else None)
