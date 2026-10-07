"""Development evaluation contracts; missing independent labels always yield null."""
from p08_common import *
P8 = ROOT/'artifacts/us_equity/p8'
VERSION = 'development-evaluation-0.1.0'

PROTOCOL = {
    'protocol_version': VERSION,'evaluation_kind':'development_engineering',
    'systems':['S0','S1','S3'],'unexecuted_systems':['S2','S4','S5'],
    'input_documents':2,'input_families':2,'input_candidates':39,'review_budget_candidates':39,
    'cutoff_current_review':'2026-10-06','historical_cutoff':'each release published_date; date precision',
    'primary_endpoints':['contracts','source_id_coverage','semantic_reproduction','frozen_regression','failure_retention'],
    'secondary_endpoints':['local_materialization_seconds','stage_wall_seconds','external_calls'],
    'independent_metrics':['numeric_accuracy','relation_accuracy','retrieval_recall_at_k','change_accuracy','important_recall','ndcg','human_time_saved'],
    'undefined_policy':'null with reason and denominator; zero cost is never inferred',
    'split_policy':'both exposed Microsoft families remain adaptation; reserved FY2026 Q1 body unopened',
    'gold_policy':'human independent labels and qrels required; agent references only development regression',
    'target_selection_status':'incomplete_no_independent_dev','threshold':None,'confidence_interval':None,
    'ablation':'exact_key vs local_label_tfidf query coverage/agreement only; no qrels-based performance',
    'human_study':'not_performed; at most two actual participants; distinct matched tasks and crossed order',
    'cost_policy':'two-document denominator; observed hardware/labor/energy cost null; external calls counted',
}

def code_hashes_p09():
    return {p.relative_to(ROOT).as_posix():sha(p) for p in sorted((ROOT/'scripts').glob('p09_*.py'))}

def readiness(families, human_gold, qrels, people, exposure):
    independent = bool(families and human_gold and qrels and exposure=='untouched')
    return {'formal_benchmark_complete':False,'independent_ready':independent,
        'independent_status':'ready_requires_frozen_protocol' if independent else 'blocked_missing_data',
        'human_study_status':'ready_requires_sessions' if people else 'not_performed',
        'human_gold':human_gold,'qrels':qrels,'actual_participants':people,
        'exposure':exposure,'families':families}

def metric(name, value, numerator, denominator, unit, reason=None):
    return {'metric':name,'value':None if denominator==0 else value,'numerator':numerator,
            'denominator':denominator,'unit':unit,'status':'not_evaluated' if value is None or denominator==0 else 'observed',
            'reason':reason or ('zero_denominator' if denominator==0 else None)}

def verify(path):
    path=Path(path);m=read(path/'run_manifest.json')
    checks={'outputs_frozen':hashes_ok(path,m['output_hashes']),
        'code_frozen':m['code_hashes']==code_hashes_p09(),
        'inputs_frozen':all((ROOT/x['path']).is_file() and sha(ROOT/x['path'])==x['sha256'] for x in m['inputs']),
        'engineering_passed':all(read(path/'engineering_validation.json')['checks'].values()),
        'independent_null':all(x['value'] is None and x['denominator']==0 for x in read(path/'evaluation_results.json')['independent_metrics']),
        'no_formal_promotion':not m['formal_benchmark_complete'],
        'report_numbers':read(path/'report_tables.json')==read(path/'evaluation_results.json')}
    return {'status':'passed_with_explicit_limitations' if all(checks.values()) else 'failed','checks':checks,
            'failed_checks':[k for k,v in checks.items() if not v]}
