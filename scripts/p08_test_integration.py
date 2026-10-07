"""Synthetic feedback/security checks plus an actual interrupted batch/resume test."""
import argparse
import copy
import tempfile
from p08_common import *
from p08_feedback import *

def cases(run_dir, fault_run=None):
    run_dir=Path(run_dir); c=rows(run_dir/'review_cards.jsonl')[0]; results=[]
    def case(name, ok): results.append({'name':name,'passed':bool(ok),'kind':'synthetic'})
    e={'feedback_id':'F-test-a','idempotency_key':'I-test-a','source_run':run_dir.name,'card_id':c['card_id'],
       'card_version':c['card_version'],'actor_id':'reviewer-a','action':'correct_fact','field':'numeric_value',
       'before':base_value(c,'numeric_value'),'after':'123','evidence_refs':[c['facts'][0]['evidence'][0]['evidence_id']],
       'reason_code':'value_mismatch','created_at':'2026-10-07T00:00:00+09:00'}
    def payload(events): return {'schema_version':'p08-feedback-export-0.1','source_run':run_dir.name,'events':events}
    with tempfile.TemporaryDirectory() as tmp:
        store=Path(tmp); before=sha(run_dir/'review_cards.jsonl')
        a=import_payload(payload([e]),run_dir,store); b=import_payload(payload([e]),run_dir,store)
        case('idempotent_reimport',a['accepted']==1 and b['duplicates']==1 and len(journal(store)['events'])==1)
        other=dict(e,feedback_id='F-test-b',idempotency_key='I-test-b',actor_id='reviewer-b',after='456')
        d=import_payload(payload([other]),run_dir,store)
        case('two_writer_conflict_preserved',d['conflicts']==1 and len(journal(store)['events'])==2)
        conflict=journal(store)['conflicts'][0]
        resolve(store,conflict['conflict_id'],'adopt',['F-test-a'],'local-owner')
        case('owner_resolution_history',len(journal(store)['resolutions'])==1 and len(journal(store)['events'])==2)
        alternate=store/'other-run'; alternate.mkdir()
        write_rows(alternate/'review_cards.jsonl',[dict(c,run_id='other-run')])
        cross=dict(e,source_run='other-run',feedback_id='F-test-c',idempotency_key='I-test-c',after='789')
        other_payload={'schema_version':'p08-feedback-export-0.1','source_run':'other-run','events':[cross]}
        r=import_payload(other_payload,alternate,store)
        case('same_card_version_cross_run_conflict',r['conflicts']==1)
        snap=snapshot_feedback(store,'other-run',[dict(c,run_id='other-run')])
        case('rerun_preserves_compatible_feedback',len(snap['events'])==3 and len(snap['conflicts'])==2 and len(snap['resolutions'])==1)
        changed=dict(c,card_version='new-logical-version')
        case('changed_card_version_does_not_inherit_reviews',not snapshot_feedback(store,'other-run',[changed])['events'])
        for name, edits in [
            ('unknown_card',{'card_id':'unknown'}),('wrong_run',{'source_run':'wrong'}),
            ('stale_version',{'card_version':'old'}),('forged_before',{'before':'forged'}),
            ('script_in_decimal',{'after':'<script>alert(1)</script>'}),('untrusted_actor',{'actor_id':'<img src=x>'}),
            ('field_allowlist',{'field':'private_file'}),('evidence_reference',{'evidence_refs':['unknown']}),
            ('same_key_other_value',{'after':'999'}),('gold_promotion',{'after':'human_gold'}),
        ]:
            bad=dict(e,**edits)
            r=import_payload(payload([bad]),run_dir,store)
            case(name,len(r['rejected'])==1 and r['accepted']==0)
        case('journal_reload_persistent',journal(store)['events'][0]['after']=='123')
        case('predictions_never_overwritten',sha(run_dir/'review_cards.jsonl')==before)
        case('no_gold_or_training',all(x['human_gold'] is False and x['training_eligibility']=='excluded_current_cycle' for x in journal(store)['events']))
        try: import_payload(payload([e]*(MAX_EVENTS+1)),run_dir,store); ok=False
        except ValueError: ok=True
        case('oversize_rejected',ok)
        with locked(store):
            try: import_payload(payload([]),run_dir,store); ok=False
            except ValueError: ok=True
        case('single_writer_lock',ok)
    cards=rows(run_dir/'review_cards.jsonl'); ids=[i for c in cards for i in c['candidate_refs']]
    case('zero_cards_distinct_from_success',validate_cards([],ids)['every_candidate_once'] is False)
    broken=copy.deepcopy(cards); broken[0]['changes'][0]['delta']='1'
    case('tampered_card_detected',validate_cards(broken,ids)['version_integrity'] is False)
    case('empty_universe_valid',all(validate_cards([],[]).values()))
    if fault_run:
        from p08_run import run
        fault_run=inside(fault_run,P7/'runs')
        try: run(fault_run,fail_before='review'); ok=False
        except RuntimeError: ok=True
        state=read(fault_run/'pipeline_state.json')
        case('partial_failure_kept',ok and state['status']=='failed' and state['stages']['review']['status']=='failed' and state['stages']['cards']['status']=='skipped')
        original=state['stages']['extract']['hashes']
        complete=run(fault_run,resume=True)
        case('resume_reuses_verified_success',complete['stages']['extract']['status']=='reused' and complete['stages']['extract']['hashes']==original)
        case('resume_matches_full_run',complete['semantic_hash']==read(run_dir/'run_manifest.json')['semantic_hash'])
        tamper=fault_run/complete['stages']['cards']['output_dir']/'review_cards.jsonl'
        old=read(fault_run/'run_config.json'); bad_config=dict(old,stage_timeout_seconds=119)
        try: run(fault_run,bad_config,resume=True); ok=False
        except ValueError: ok=True
        case('changed_config_requires_new_run',ok)
        # Do not corrupt a frozen run; verify the hash checker against a separate file.
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'x'; p.write_text('first'); h={'x':sha(p)}; p.write_text('second')
            case('output_hash_tamper_detected',not hashes_ok(Path(temp),h))
        timeout_run=fault_run.with_name(fault_run.name+'_deadline')
        try: run(timeout_run,deadline_seconds=0); ok=False
        except TimeoutError: ok=True
        stopped=read(timeout_run/'pipeline_state.json')
        case('timeout_retains_state_no_success',ok and stopped['status']=='failed' and
             all(s['status']=='skipped' for s in stopped['stages'].values()) and not (timeout_run/'run_manifest.json').exists())
    return {'cases':results,'passed':sum(x['passed'] for x in results),'total':len(results),'human_participants':0}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--run-dir',type=Path,required=True);p.add_argument('--fault-run',type=Path)
    p.add_argument('--report',type=Path);a=p.parse_args();r=cases(a.run_dir,a.fault_run)
    if a.report: atomic(a.report,r)
    print(json.dumps(r));raise SystemExit(r['passed']!=r['total'])
