"""Apply final gate, inventory all public artifacts, and freeze the package."""
from p04_common import *
from p04_verify_package import integrity, public_files

def main():
    require_stage(4)
    checks,details=integrity()
    if not all(checks.values()):
        print(json.dumps({'failed_checks':[k for k,v in checks.items() if not v],'details':details}));raise SystemExit(1)
    json_file(OUT/'stage_reviews/stage_05_final.json',{'stage':5,'checked_at':now(),'gate':'passed_with_explicit_limitations',
        'checks':checks,'details':details,'improvement_ref':'stage_reviews/stage_05_improvements.md',
        'independent_review_ref':'stage_reviews/stage_05_independent.json',
        'counts':{'reviewed_items':39,'source_numeric_claims':33,'relation_claims':6,'agent_annotations':78,
            'split_rows':43,'reserved_unlabeled_documents':1,'human_gold':0,'train_items':0,'dev_items':0,'test_items':0},
        'authorized_work_packages_completed':[1,2,3,4,5],'formal_P04_complete':False,'next_stage':None,
        'limitations':['Actual human independent annotation/adjudication absent','Reserved candidate not certified test','All labeled items adaptation']})
    inventory=[]
    for path in public_files():
        relative=path.relative_to(ROOT).as_posix()
        count=len(rows(path)) if path.suffix in {'.jsonl','.csv'} else None
        inventory.append({'path':relative,'sha256':sha(path),'bytes':path.stat().st_size,'rows_if_tabular':count,
            'role':'history_or_review' if any(x in relative for x in ['stage_reviews','contract_revisions','code_history']) else 'code' if path.suffix=='.py' else 'artifact_or_documentation'})
    csv_file(OUT/'artifact_inventory.csv',inventory)
    file_rows=[{'path':r['path'],'sha256':r['sha256']} for r in inventory]
    file_rows.append({'path':(OUT/'artifact_inventory.csv').relative_to(ROOT).as_posix(),'sha256':sha(OUT/'artifact_inventory.csv')})
    json_file(OUT/'package_manifest.json',{'package_version':'us-p3-agent-pilot-1.0','frozen_at':now(),
        'files':file_rows,'input_snapshot_sha256':sha(OUT/'input_snapshot.json'),
        'active_guide':'us-p3-guide-1.2','source_contract':'1.0.0-agent-pilot','registry_version':'us-p2-0.1.0',
        'split_version':'us-p3-split-1.0','human_gold':0,'formal_phase_complete':False,
        'excluded':['private source and policy files','__pycache__','package_manifest.json (self)','package_validation.json (post-freeze validation)'],
        'reproduce':'verification_commands.md','recorded_failures_retained':True})
    print(json.dumps({'stage':5,'checks_passed':len(checks),'manifest_files':len(file_rows),'human_gold':0,'formal_phase_complete':False}))

if __name__=='__main__':main()
