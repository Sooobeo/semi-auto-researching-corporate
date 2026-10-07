"""Validate a browser export; append a review revision without modifying predictions."""
import argparse
from p08_common import *
from p08_feedback import import_payload, resolve, MAX_BYTES

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('--run-dir',type=Path,required=True)
    p.add_argument('--file',type=Path); p.add_argument('--store',type=Path,default=P7/'feedback')
    p.add_argument('--resolve'); p.add_argument('--decision',choices=['adopt','merge','defer']); p.add_argument('--selected',nargs='*',default=[])
    p.add_argument('--owner'); p.add_argument('--report',type=Path)
    a = p.parse_args(); inside(a.run_dir,P7/'runs'); inside(a.store,P7)
    from p08_verify_package import verify_run
    if verify_run(a.run_dir)['status']=='failed': raise SystemExit('Unverified source run')
    if a.resolve:
        result = resolve(a.store,a.resolve,a.decision,a.selected,a.owner or '')
    else:
        if not a.file or a.file.stat().st_size>MAX_BYTES: raise SystemExit('Missing or oversized export')
        result = import_payload(read(a.file),a.run_dir,a.store)
    if a.report: atomic(a.report,result)
    print(json.dumps(result,ensure_ascii=False))
    raise SystemExit(1 if result.get('rejected') else 0)
