"""Read-only P08 verification; upstream frozen packages are never regenerated."""
import argparse
from p08_common import *

def verify_run(path):
    path=Path(path); m=read(path/'run_manifest.json'); snap=read(path/'input_snapshot.json'); state=read(path/'pipeline_state.json')
    cards=rows(path/'review_cards.jsonl'); ids=[r['candidate_id'] for r in rows(path/'candidate_card_links.jsonl')]
    checks=validate_cards(cards,ids)
    checks.update(outputs_frozen=hashes_ok(path,m['output_hashes']),
        inputs_frozen=all((ROOT/r['path']).exists() and sha(ROOT/r['path'])==r['sha256'] for r in snap['inputs']),
        code_frozen=m['code_hashes']==code_hashes(),semantic_hash=m['semantic_hash']==semantic(cards),
        completed=state['status']=='succeeded' and all(v['status'] in ('succeeded','reused') for v in state['stages'].values()),
        stage_outputs_frozen=all(hashes_ok(path/v['output_dir'],v['hashes']) for v in state['stages'].values()),
        no_gold_promotion=m['summary']['human_gold']==m['summary']['independent_test']==0 and not m['formal_benchmark_complete'],
        validation=all(read(path/'validation_report.json')['checks'].values()),
        synthetic_passed=read(path/'synthetic_tests.json')['passed']==read(path/'synthetic_tests.json')['total'])
    return {'status':'passed_with_explicit_limitations' if all(checks.values()) else 'failed',
            'checks':checks,'failed_checks':[k for k,v in checks.items() if not v],'summary':m['summary']}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--run-dir',type=Path,required=True);a=p.parse_args()
    r=verify_run(a.run_dir);print(json.dumps(r));raise SystemExit(r['status']=='failed')
