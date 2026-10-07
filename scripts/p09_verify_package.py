"""Read-only verification of development evaluation, missing data and report tables."""
import argparse
from p09_common import *
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--run-dir',type=Path,required=True);a=p.parse_args()
    r=verify(a.run_dir);print(json.dumps(r));raise SystemExit(r['status']=='failed')
