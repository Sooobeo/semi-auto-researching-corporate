"""P08/P09 explicit publication adapter. Structured facts and validated feedback only."""
import argparse
import json
import re
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
from p08_common import read,rows,sha,atomic,now,semantic
from p08_verify_package import verify_run as verify_p08
from p09_common import verify as verify_p09

SCHEMA={
    '$schema':'https://json-schema.org/draft/2020-12/schema','type':'object',
    'required':['schema_version','generated_at','P08','P09','sharing'],
    'properties':{'schema_version':{'const':'p08-p09-site-0.1'},
        'P08':{'type':'object','required':['run_id','summary','cards','pipeline','feedback']},
        'P09':{'type':['object','null']},
        'sharing':{'type':'object','properties':{'source_prose_included':{'const':False},'private_paths_included':{'const':False}}}}
}

def make(p08,p09=None):
    p08=Path(p08)
    if verify_p08(p08)['status']=='failed':raise ValueError('Unverified P08 run')
    m=read(p08/'run_manifest.json');state=read(p08/'pipeline_state.json');f=read(p08/'feedback_snapshot.json')
    cards=rows(p08/'review_cards.jsonl')
    events=[{k:e[k] for k in ('feedback_id','card_id','card_version','source_run','action','field','before','after','reason_code','created_at',
        'received_at','review_status','training_eligibility','actor_verification','time_source','human_gold')} for e in f['events']]
    d={'schema_version':'p08-p09-site-0.1','generated_at':now(),
       'P08':{'run_id':p08.name,'summary':m['summary'],'semantic_hash':m['semantic_hash'],
           'source_runs':m['source_run_refs'],'policy_version':m['policy_version'],'cards':cards,
           'pipeline':{'status':state['status'],'empty_result_reason':state['empty_result_reason'],
               'stages':[{'stage':k,**{field:v.get(field) for field in ('status','reason','counts','elapsed_seconds','attempt')}} for k,v in state['stages'].items()],
               'external_calls':m['external_calls'],'new_source_requests':m['new_source_requests']},
           'feedback':{'revision':f['revision'],'source_run':read(p08/'run_config.json')['feedback_source_run'] or p08.name,
               'events':events,'compatible_source_runs':f['compatible_source_runs'],'conflicts':f['conflicts'],
               'resolutions':[{k:r[k] for k in ('resolution_id','conflict_id','decision','selected_feedback_ids','created_at','human_gold','training_eligibility')} for r in f['resolutions']],
               'shared_auto_save':False,'human_gold':0},
           'verification':{'checks':verify_p08(p08)['checks'],'synthetic_tests':None},
           'unperformed':['사람의 독립 검토','사람 사용성 세션','팀원 재실행','팀원 실제 접속 확인','전체 본문 완전성 감사']},
       'P09':None,
       'sharing':{'source_prose_included':False,'private_paths_included':False,'personal_memos_included':False,
           'audience':'기존 소유자·지정 팀원 2인','rights_basis':'기존 최소 숫자·표준 라벨·기간·위치의 사실 참조 범위',
           'rights_checked_date':'2026-10-05','view':'검증된 게시 snapshot','auto_execution':False,'automatic_shared_save':False}}
    tests=p08/('resilience_tests.json' if (p08/'resilience_tests.json').exists() else 'synthetic_tests.json')
    if tests.exists():
        t=read(tests);d['P08']['verification']['synthetic_tests']={'passed':t['passed'],'total':t['total'],'human_participants':0}
    if p09:
        p09=Path(p09)
        if verify_p09(p09)['status']=='failed':raise ValueError('Unverified P09 run')
        result=read(p09/'evaluation_results.json')
        fields=('schema_version','phase_id','run_id','source_p08_run','protocol_version','summary','systems','mode_counts',
            'engineering_checks_passed','engineering_checks_total','synthetic_passed','synthetic_total','semantic_reproduction',
            'reproduction_actor','colleague_reexecution','independent_metrics','formal_benchmark_complete','research_status',
            'external_calls','stage_wall_seconds','cost','withheld_change_count','withheld_calculation_count','card_failures',
            'retrieval_queries','paired_query_groups','exact_sparse_selection_agreement','retrieval_performance_status','ci','p_value','change_computed_breakdown')
        d['P09']={k:result[k] for k in fields}
        d['P09']['failure_cases']=rows(p09/'failure_cases.jsonl')
        d['P09']['source_output_sha256']=sha(p09/'evaluation_results.json')
        d['P09']['verification']=verify_p09(p09)['checks']
    validate(d);return d

def validate(d):
    if d['schema_version']!='p08-p09-site-0.1' or d['sharing']['source_prose_included']:raise ValueError('Publication contract')
    cards=d['P08']['cards'];ids={i for c in cards for i in c['candidate_refs']}
    if len(ids)!=d['P08']['summary']['candidates'] or len(cards)!=d['P08']['summary']['cards']:raise ValueError('Publication denominator')
    if semantic(cards)!=d['P08']['semantic_hash']:raise ValueError('Card drift')
    allowed_facts={'record_id','prediction_id','kind','doc_id','revision_id','event_family_id','source_url','normalized','period',
        'published_date','published_at','observed_at','scope_status_as_of','date_conflict_status','historical_context_available','evidence'}
    for c in cards:
        if c['review_readiness']!='needs_review' or c['human_gold'] is not False:raise ValueError('Review promotion')
        for fact in c['facts']:
            if set(fact)!=allowed_facts or not fact['source_url'].startswith('https://www.microsoft.com/'):raise ValueError('Fact allowlist')
    if d['P09']:
        if any(x['value'] is not None for x in d['P09']['independent_metrics']):raise ValueError('Unsupported independent metric')
        if d['P09']['cost']['observed_operating_cost'] is not None:raise ValueError('Unmeasured cost')
    raw=json.dumps(d,ensure_ascii=False)
    if re.search(r'private[/\\]|(?:^|["\s])[A-Z]:[\\/]|password|api_key|bearer_token|raw_html|token_expires|<script|actor_id|owner_id|rationale',raw,re.I):raise ValueError('Sensitive/unreviewed content')
    return True

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--p08-run',type=Path,required=True);p.add_argument('--p09-run',type=Path)
    p.add_argument('--output',type=Path,default=Path(__file__).parent/'dist/integration.json');a=p.parse_args()
    d=make(a.p08_run,a.p09_run);atomic(a.output,d);atomic(a.output.parent/'integration-schema.json',SCHEMA)
    print(json.dumps({'status':'passed','cards':len(d['P08']['cards']),'candidates':d['P08']['summary']['candidates'],'snapshot_sha256':sha(a.output)}))
