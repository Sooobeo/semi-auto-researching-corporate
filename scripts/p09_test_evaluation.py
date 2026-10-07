"""Counterexamples for independent-data gates and undefined metrics."""
import argparse
from p09_common import *
def cases():
    checks={
        'zero_denominator_null':metric('x',1,0,0,'item')['value'] is None,
        'missing_gold_blocks_independent':not readiness(2,0,0,0,'untouched')['independent_ready'],
        'adaptation_never_untouched':not readiness(2,39,39,0,'adaptation')['independent_ready'],
        'qrels_absent_not_no_answer':not readiness(2,39,0,0,'untouched')['independent_ready'],
        'empty_sessions_not_zero_time':readiness(2,0,0,0,'adaptation')['human_study_status']=='not_performed',
        'independent_dev_threshold_null':PROTOCOL['threshold'] is None,
        'absent_systems_explicit':PROTOCOL['unexecuted_systems']==['S2','S4','S5'],
    }
    return {'cases':[{'name':k,'passed':v,'kind':'synthetic'} for k,v in checks.items()], 'passed':sum(checks.values()),'total':len(checks)}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--report',type=Path);a=p.parse_args();r=cases()
    if a.report:atomic(a.report,r)
    print(json.dumps(r));raise SystemExit(r['passed']!=r['total'])
