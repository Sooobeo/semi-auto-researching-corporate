"""Read-only validation of frozen P07 store/retrieval/change/calculation artifacts."""
import argparse
from p06_common import *
def verify_run(path):
    r=verify(path,'P07');path=Path(path);data=rows(path/'event_store_records.jsonl');changes=rows(path/'change_records.jsonl')
    r['checks']['ids_resolve']=all(set(c['source_record_refs'])<={x['record_id'] for x in data} for c in changes)
    r['checks']['withheld_null']=all(c['delta'] is c['relative_delta'] is None for c in changes if c['status']=='withheld')
    r['failed_checks']=[k for k,v in r['checks'].items() if not v];r['status']='failed' if r['failed_checks'] else 'passed_with_explicit_limitations';return r
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--run-dir',type=Path,required=True);a=p.parse_args();r=verify_run(a.run_dir)
    print(json.dumps(r,ensure_ascii=False));raise SystemExit(1 if r['status']=='failed' else 0)
