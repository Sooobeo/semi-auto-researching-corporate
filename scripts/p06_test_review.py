"""Synthetic tests for deterministic review ordering and null-score contracts."""
from p06_common import *
from p06_review import synthetic_cases
if __name__=='__main__':
    data,_=audit_p05();result=synthetic_cases(data,rows(P4/'relation_claim_links.jsonl'))
    print(json.dumps({'passed':sum(c['passed'] for c in result['cases']),'total':len(result['cases']),'failed':[c['name'] for c in result['cases'] if not c['passed']]}));raise SystemExit(0 if all(c['passed'] for c in result['cases']) else 1)
