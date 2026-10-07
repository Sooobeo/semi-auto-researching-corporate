"""Fixed offline batch: extraction replay -> guarded comparison -> review -> cards."""
from __future__ import annotations
import argparse
import platform
import subprocess
import sys
import time
from collections import Counter
from p08_common import *
from p08_cards import build
from p08_feedback import snapshot_feedback, journal
from p06_common import audit_p05

def prepare(config):
    from p06_verify_package import verify_run as v6
    from p07_verify_package import verify_run as v7
    data, snap = audit_p05(config['source_run'])
    for key, verify in [('p06_run',v6),('p07_run',v7)]:
        p = ROOT/config[key]
        if verify(p)['status'] == 'failed': raise ValueError('upstream_package_failed')
        snap['inputs'].append({'path':config[key]+'/run_manifest.json','sha256':sha(p/'run_manifest.json')})
    snap['feedback_hash'] = digest(journal(ROOT/config['feedback_store']))
    snap['config_hash'] = digest(config); snap['code_hashes'] = code_hashes()
    return data, snap

def command(args, timeout):
    result = subprocess.run([sys.executable, str(ROOT/'scripts'/args[0]), *map(str,args[1:])],
        cwd=ROOT, env={**os.environ,'PYTHONIOENCODING':'utf-8'}, capture_output=True, text=True,
        encoding='utf-8', timeout=timeout)
    if result.returncode: raise RuntimeError('fixed_cli_failed:'+args[0])
    # Private subprocess logs are never copied to artifacts or public responses.

def source_semantic(preds):
    from p05_common import semantic as prediction_semantic
    return sorted((prediction_semantic(p) for p in preds), key=lambda p:p['input_id'])

def execute_stage(stage, run_dir, output, state, config, data):
    timeout = config['stage_timeout_seconds']
    refs = {k: run_dir/v['output_dir'] for k,v in state['stages'].items() if v.get('output_dir')}
    if stage == 'extract':
        target = output/'replay'
        command(['p05_rule_baseline.py','--run-id','p08-replay','--output-dir',target],timeout)
        command(['p05_validate_predictions.py','--run-dir',target],timeout)
        command(['p05_compare_reference.py','--run-dir',target],timeout)
        active = read(ROOT/'artifacts/us_equity/p4/active_run.json')
        original = rows(ROOT/active['run_dir']/'predictions.jsonl'); replay = rows(target/'predictions.jsonl')
        if source_semantic(original) != source_semantic(replay): raise ValueError('fresh_extraction_changed_create_new_adapter')
        if read(target/'comparison_manifest.json')['field_errors'] != 0: raise ValueError('development_regression_failed')
        atomic(output/'adapter_check.json',{'fresh_extraction_matches_frozen':True,
            'adapter':'verified P05 candidate store; stable source IDs after semantic replay match',
            'candidates':len(data),'source_run':config['source_run']})
        return {'unit':'candidate','input':len(data),'normal':len(replay),'failed':0,'held':0}
    if stage == 'compare':
        command(['p07_run.py','--source-run',config['source_run'],'--run-dir',output/'result'],timeout)
        expected = ROOT/config['p07_run']
        actual = read(output/'result/run_manifest.json'); original = read(expected/'run_manifest.json')
        if actual['semantic_hash'] != original['semantic_hash']: raise ValueError('comparison_replay_changed')
        return {'unit':'candidate','input':len(data),'normal':len(data),'failed':0,'held':0,
            'change_attempts':len(rows(output/'result/change_records.jsonl'))}
    if stage == 'review':
        command(['p06_run.py','--source-run',config['source_run'],'--run-dir',output/'result',
                 '--change-run',refs['compare']/'result'],timeout)
        expected = ROOT/config['p06_run']
        if read(output/'result/run_manifest.json')['semantic_hash'] != read(expected/'run_manifest.json')['semantic_hash']:
            raise ValueError('review_replay_changed')
        return {'unit':'candidate','input':len(data),'normal':len(data),'failed':0,'held':0}
    output.mkdir(parents=True, exist_ok=True)
    if stage == 'cards':
        cards, failures, projection = build(refs['review']/'result',refs['compare']/'result',run_dir.name)
        # Physical replay paths remain in the manifest; cards cite the original verified source runs.
        for c in cards:
            c['source_runs'] = {'P05':config['source_run'],'P06':Path(config['p06_run']).name,'P07':Path(config['p07_run']).name}
            c['card_version'] = digest({k:v for k,v in c.items() if k not in ('run_id','card_version')})
        write_rows(output/'review_cards.jsonl',cards); write_rows(output/'failed_items.jsonl',failures)
        write_rows(output/'candidate_card_links.jsonl',[{'candidate_id':i,'card_id':c['card_id'],'card_version':c['card_version']} for c in cards for i in c['candidate_refs']])
        atomic(output/'review_card_schema.json',CARD_SCHEMA)
        atomic(output/'comparison_totals.json',{'mode_counts':dict(Counter(x['cutoff_mode'] for x in projection['changes'])),
            'computed_counts':dict(Counter(x['cutoff_mode'] for x in projection['changes'] if x['status']=='computed')),
            'calculations':len(projection['calculations'])})
        return {'unit':'candidate','input':len(data),'normal':sum(len(c['candidate_refs']) for c in cards),
            'failed':sum(len(f['candidate_refs']) for f in failures),'held':0,'cards':len(cards)}
    cards = rows(refs['cards']/'review_cards.jsonl')
    if stage == 'feedback_snapshot':
        snap = snapshot_feedback(ROOT/config['feedback_store'],config['feedback_source_run'] or run_dir.name,cards)
        atomic(output/'feedback_snapshot.json',snap)
        csvfile(output/'active_learning_queue.csv',['card_id','source','exposure_status','training_eligibility','reason'],
            [{'card_id':c['card_id'],'source':'uncertainty_or_feedback','exposure_status':c['exposure_status'],
              'training_eligibility':'excluded_current_cycle','reason':'independent_human_labels_absent'} for c in cards])
        write_rows(output/'analyst_memos.jsonl',[])
        return {'unit':'feedback_event','input':len(snap['events']),'normal':len(snap['events']),'failed':0,'held':0,
                'human_gold':0,'snapshot_revision':snap['revision']}
    if stage == 'validate':
        checks = validate_cards(cards,[r['record_id'] for r in data])
        from p05_common import validator
        card_validator = validator(CARD_SCHEMA)
        checks['schema'] = all(not list(card_validator.iter_errors(c)) for c in cards)
        checks['stage_conservation'] = all(v['counts']['input'] == sum(v['counts'][k] for k in ('normal','failed','held'))
            for k,v in state['stages'].items() if k != 'validate')
        atomic(output/'validation_report.json',{'checks':checks,'status':'passed' if all(checks.values()) else 'failed'})
        if not all(checks.values()): raise ValueError('card_validation_failed')
        return {'unit':'card','input':len(cards),'normal':len(cards),'failed':0,'held':0}
    raise ValueError('unknown_stage')

def run(run_dir, config=None, resume=False, fail_before=None, deadline_seconds=None):
    run_dir = inside(run_dir,P7/'runs'); config = config_check(config or dict(DEFAULT_CONFIG))
    data, snap = prepare(config); key = digest(snap); started = time.perf_counter()
    if resume:
        state = read(run_dir/'pipeline_state.json')
        if state['stage_input_key'] != key or read(run_dir/'run_config.json') != config: raise ValueError('resume_inputs_changed_new_run_required')
    else:
        run_dir.mkdir(parents=True,exist_ok=False)
        atomic(run_dir/'run_config.json',config); atomic(run_dir/'input_snapshot.json',snap)
        state = {'phase_id':'P08','run_id':run_dir.name,'stage_input_key':key,'status':'running','started_at':now(),
                 'stages':{},'errors':[],'resume_count':0,'external_calls':0,'new_source_requests':0}
    state['resume_count'] += int(resume); state['status']='running'; atomic(run_dir/'pipeline_state.json',state)
    attempts = rows(run_dir/'stage_attempts.jsonl') if (run_dir/'stage_attempts.jsonl').exists() else []
    try:
        for index, stage in enumerate(STAGES):
            old = state['stages'].get(stage)
            stage_key = digest([key,stage,{k:v.get('hashes') for k,v in state['stages'].items() if k in STAGES[:index]}])
            if old and old['status'] in ('succeeded','reused'):
                if old['stage_key'] != stage_key or not hashes_ok(run_dir/old['output_dir'],old['hashes']): raise ValueError('resume_output_tampered')
                old['status']='reused'; old['reason']='same_key_and_output_hash_verified'
                atomic(run_dir/'pipeline_state.json',state); continue
            if deadline_seconds is not None and time.perf_counter()-started >= deadline_seconds: raise TimeoutError('pipeline_deadline')
            attempt = sum(a['stage']==stage for a in attempts)+1
            output = run_dir/'stages'/stage/f'attempt_{attempt:03d}'
            t = time.perf_counter(); stamp = now()
            state['stages'][stage] = {'status':'running','stage_key':stage_key,'started_at':stamp,'attempt':attempt}
            atomic(run_dir/'pipeline_state.json',state)
            try:
                if fail_before == stage: raise RuntimeError('injected_test_failure')
                output.mkdir(parents=True,exist_ok=False)
                counts = execute_stage(stage,run_dir,output,state,config,data)
                v = {'status':'succeeded','reason':None,'stage_key':stage_key,'output_dir':output.relative_to(run_dir).as_posix(),
                     'hashes':output_hashes(output),'counts':counts,'attempt':attempt,'started_at':stamp,'completed_at':now(),
                     'elapsed_seconds':time.perf_counter()-t,'external_calls':0}
                state['stages'][stage] = v
                attempts.append({'stage':stage,'attempt':attempt,**{k:v[k] for k in ('status','started_at','completed_at','elapsed_seconds','counts')}})
                write_rows(run_dir/'stage_attempts.jsonl',attempts); atomic(run_dir/'pipeline_state.json',state)
            except (Exception,KeyboardInterrupt) as exc:
                v = state['stages'][stage]; v.update(status='retryable' if isinstance(exc,(TimeoutError,subprocess.TimeoutExpired)) else 'failed',
                    reason=str(exc) if isinstance(exc,(RuntimeError,ValueError,TimeoutError)) else type(exc).__name__,
                    elapsed_seconds=time.perf_counter()-t,partial_output_dir=output.relative_to(run_dir).as_posix())
                attempts.append({'stage':stage,'attempt':attempt,'status':v['status'],'reason':v['reason'],'elapsed_seconds':v['elapsed_seconds']})
                write_rows(run_dir/'stage_attempts.jsonl',attempts)
                raise
        cards_output = run_dir/state['stages']['cards']['output_dir']
        feedback_output = run_dir/state['stages']['feedback_snapshot']['output_dir']
        for filename in ('review_cards.jsonl','candidate_card_links.jsonl','failed_items.jsonl','review_card_schema.json'):
            (run_dir/filename).write_bytes((cards_output/filename).read_bytes())
        for filename in ('feedback_snapshot.json','active_learning_queue.csv','analyst_memos.jsonl'):
            (run_dir/filename).write_bytes((feedback_output/filename).read_bytes())
        report = read(run_dir/state['stages']['validate']['output_dir']/'validation_report.json')
        atomic(run_dir/'validation_report.json',report)
        cards = rows(run_dir/'review_cards.jsonl')
        from p08_test_integration import cases
        tests = cases(run_dir)
        atomic(run_dir/'synthetic_tests.json',tests)
        if tests['passed'] != tests['total']: raise ValueError('feedback_counterexamples_failed')
        state.update(status='succeeded',completed_at=now(),semantic_hash=semantic(cards),card_count=len(cards),candidate_count=len(data),
                     empty_result_reason='no_matching_candidates' if not data else ('processing_failed' if not cards else None))
        atomic(run_dir/'pipeline_state.json',state)
        csvfile(run_dir/'cost_report.csv',['stage','attempt','status','elapsed_seconds','external_calls','operating_cost','cost_reason'],
            [{'stage':a['stage'],'attempt':a['attempt'],'status':a['status'],'elapsed_seconds':a['elapsed_seconds'],
              'external_calls':0,'operating_cost':'NA','cost_reason':'hardware_labor_energy_not_measured'} for a in attempts])
        atomic(run_dir/'run_manifest.json',{'phase_id':'P08','run_id':run_dir.name,'schema_version':'p08-run-0.1','policy_version':VERSION,
            'status':'development_ready','research_status':'not_evaluated','formal_benchmark_complete':False,
            'semantic_hash':state['semantic_hash'],'source_run_refs':{k:config[k] for k in ('source_run','p06_run','p07_run')},
            'input_snapshot_sha256':sha(run_dir/'input_snapshot.json'),'code_hashes':code_hashes(),
            'output_hashes':{name:sha(run_dir/name) for name in ('review_cards.jsonl','candidate_card_links.jsonl','review_card_schema.json',
                'feedback_snapshot.json','validation_report.json','failed_items.jsonl','active_learning_queue.csv','analyst_memos.jsonl','run_config.json','cost_report.csv','synthetic_tests.json')},
            'summary':{'documents':2,'families':2,'candidates':len(data),'numeric_candidates':33,'relation_candidates':6,'cards':len(cards),
                'human_gold':0,'independent_test':0,'feedback_events':len(read(run_dir/'feedback_snapshot.json')['events'])},
            'environment':{'python':platform.python_version(),'platform':platform.platform(),'processor':platform.processor(),
                           'logical_cpu_count':os.cpu_count(),'hardware_cost':None,'memory_peak_bytes':None},
            'pipeline_elapsed_seconds':time.perf_counter()-started,'external_calls':0,'new_source_requests':0,
            'api_cost':None,'operating_cost':None,'cost_reason':'not_measured','completed_at':now()})
        return state
    except (Exception,KeyboardInterrupt) as exc:
        state.update(status='cancelled' if isinstance(exc,KeyboardInterrupt) else 'failed',completed_at=now())
        state['errors'].append({'at':now(),'reason':str(exc) if isinstance(exc,(RuntimeError,ValueError,TimeoutError)) else type(exc).__name__})
        for stage in STAGES:
            if stage not in state['stages']: state['stages'][stage]={'status':'skipped','reason':'upstream_incomplete'}
        atomic(run_dir/'pipeline_state.json',state)
        raise

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run-dir',type=Path,required=True); p.add_argument('--config',type=Path); p.add_argument('--resume',action='store_true')
    p.add_argument('--fail-before',choices=STAGES,help='synthetic fault test only'); p.add_argument('--deadline-seconds',type=float)
    a = p.parse_args()
    try:
        result = run(a.run_dir,read(a.config) if a.config else None,a.resume,a.fail_before,a.deadline_seconds)
        print(json.dumps({k:result[k] for k in ('status','run_id','semantic_hash','card_count','candidate_count')}))
    except (Exception,KeyboardInterrupt) as exc:
        print(json.dumps({'status':'failed','reason':str(exc) if isinstance(exc,(ValueError,RuntimeError,TimeoutError)) else type(exc).__name__})); raise SystemExit(1)
