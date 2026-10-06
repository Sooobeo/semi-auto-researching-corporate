"""Read-only P06 package and review sidecar validation."""
import argparse
from p06_common import *
def verify_run(path):
    report=verify(path,'P06'); path=Path(path);data=rows(path/'input_records.jsonl');rank=rows(path/'ranking_predictions.jsonl')
    report['checks']['candidate_universe']={r['record_id'] for r in data}=={r['record_id'] for r in rank} and len(rank)==len(data)
    report['checks']['no_scores_or_promotion']=all(r['materiality_score'] is None and r['probability'] is None and r['review_readiness']=='needs_review' for r in rank)
    report['failed_checks']=[k for k,v in report['checks'].items() if not v];report['status']='failed' if report['failed_checks'] else 'passed_with_explicit_limitations'
    return report
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--run-dir',required=True,type=Path);a=p.parse_args();r=verify_run(a.run_dir)
    print(json.dumps(r,ensure_ascii=False));raise SystemExit(1 if r['status']=='failed' else 0)
