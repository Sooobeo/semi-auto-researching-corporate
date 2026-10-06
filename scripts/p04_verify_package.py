"""Read-only integrity checks for the final P04 agent-development package."""
from __future__ import annotations
import argparse
import subprocess
from p04_common import *

EXCLUDED={'artifact_inventory.csv','package_manifest.json','package_validation.json'}
DOCS=['README.md','structure/README.md','structure/P04_phase3_annotation_pilot.md','structure/DECISIONS.md']

def public_files():
    data=[p for p in OUT.rglob('*') if p.is_file() and not set(p.parts)&{'private','__pycache__'}
          and p.relative_to(OUT).as_posix() not in EXCLUDED]
    return sorted(data+list((ROOT/'scripts').glob('p04_*.py'))+[ROOT/p for p in DOCS])

def integrity():
    checks={}; details={}
    def document(name):return json.loads((OUT/name).read_text('utf-8'))
    snap=document('input_snapshot.json')
    checks['original_14_inputs_unchanged']=len(snap['inputs'])==14 and all(sha(ROOT/r['path'])==r['sha256'] for r in snap['inputs'])
    checks['no_legacy_inputs']=snap['legacy_inputs']==[]
    for name in ['contract_freeze_manifest.json','annotation_freeze_v1_1.json','annotation_freeze_v1_2.json','annotation_execution_manifest.json']:
        freeze=document(name)
        checks[name+'_files_unchanged']=all(sha(OUT/r['path'])==r['sha256'] for r in freeze['files'])
        for key in ['code','scripts']:
            if key in freeze:checks[name+'_'+key+'_unchanged']=all(sha(ROOT/r['path'])==r['sha256'] for r in freeze[key])
    stages=[require_stage(i) for i in range(1,5)]
    checks['stage_01_to_04_order']=all(a['checked_at']<b['checked_at'] for a,b in zip(stages,stages[1:]))
    checks['stage_04_outputs_unchanged']=all(sha(OUT/r['path'])==r['sha256'] for r in stages[-1]['files'])
    checks['reservation_metadata_unchanged']=sha(OUT/'source_reservation/reservation_summary.json')==stages[0]['source_reservation_summary_sha256']
    for name in ['stage_reviews/stage_04_independent.json','stage_reviews/stage_05_independent.json']:
        report=document(name)
        checks[name+'_inputs_unchanged']=all(sha(ROOT/p)==h for p,h in report['source_input_hashes'].items())
        checks[name+'_passed']=report['gate']=='passed_with_explicit_limitations'
    independent=document('stage_reviews/stage_05_independent.json')
    checks['split_27_counterexamples_passed']=independent['negative_checks']['passed']==independent['negative_checks']['total']==27
    checks['split_no_validation_errors']=independent['result']['errors']==[]
    checks['step_05_started_after_step_04']=document('stage_reviews/stage_05_initial.json')['created_at']>stages[-1]['checked_at']
    handoff=document('stage_reviews/handoff_validation_final.json')
    checks['handoff_39_records_13_counterexamples']=handoff['status']=='passed_with_explicit_limitations' and handoff['records']==39 and len(handoff['negative_cases'])==13 and all(t['passed'] for t in handoff['negative_cases'])
    checks['handoff_current_code_matches']=sha(ROOT/'scripts/p04_validate_handoff.py')==handoff['code_sha256']
    gold=document('gold_status.json'); phase=document('phase_status.json')
    checks['human_gold_absent_not_completed']=gold['gold_events']==gold['gold_relations']==gold['human_annotations']==0 and not phase['formal_phase_complete'] and not rows(OUT/'gold_events.jsonl') and not rows(OUT/'gold_relations.jsonl')
    checks['all_12_task_statuses_explicit']=len(rows(OUT/'task_status.csv'))==12 and all(r['human_completed']=='false' for r in rows(OUT/'task_status.csv'))
    docs=rows(SOURCE/'document_manifest_v0_3.csv')
    reserve=document('source_reservation/document_manifest.json')
    # Hash bytes only; never parse/display reserved prose or numeric facts.
    checks['raw_4_document_hashes_unchanged']=all(sha(ROOT/d['storage_uri'])==d['sha256'] for d in docs+[reserve])
    private=[str(p.relative_to(ROOT)).replace('\\','/') for base in [SOURCE,OUT] for p in base.rglob('*') if p.is_file() and 'private' in p.parts]
    git=subprocess.run(['git','check-ignore','-z','--stdin'],input=('\0'.join(private)+'\0').encode('utf-8'),capture_output=True,cwd=ROOT,check=False)
    checks['all_private_files_gitignored']=git.returncode==0 and set(git.stdout.decode('utf-8').strip('\0').split('\0'))==set(private)
    details['private_files_gitignored']=len(private)
    changes=subprocess.run(['git','diff','--name-only','--','artifacts/us_equity/p0','artifacts/us_equity/p1','artifacts/us_equity/p2'],text=True,capture_output=True,cwd=ROOT,check=False)
    checks['no_original_phase_files_modified']=changes.returncode==0 and not changes.stdout.strip()
    parse_errors=[];file_count=0
    for path in public_files():
        file_count+=1
        try:
            if path.suffix=='.json':json.loads(path.read_text('utf-8'))
            elif path.suffix in {'.csv','.jsonl'}:rows(path)
            elif path.suffix=='.py':compile(path.read_text('utf-8'),str(path),'exec')
            else:path.read_text('utf-8')
        except Exception as exc:parse_errors.append({'path':str(path.relative_to(ROOT)),'error':str(exc)})
    checks['public_files_parse_and_scripts_compile']=not parse_errors
    details.update(public_files=file_count,parse_errors=parse_errors,original_inputs=14,source_documents=4)
    return checks,details

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--report',type=Path);args=parser.parse_args()
    if args.report and args.report.exists():raise FileExistsError(args.report)
    manifest=json.loads((OUT/'package_manifest.json').read_text('utf-8'))
    checks,details=integrity()
    expected={p.relative_to(ROOT).as_posix() for p in public_files()}|{(OUT/'artifact_inventory.csv').relative_to(ROOT).as_posix()}
    checks['manifest_file_set_complete']=expected=={r['path'] for r in manifest['files']}
    checks['all_package_hashes_match']=all(sha(ROOT/r['path'])==r['sha256'] for r in manifest['files'])
    final=require_stage(5)
    checks['stage_05_gate_checks_passed']=all(final['checks'].values())
    checks['final_stage_order']=final['checked_at']>require_stage(4)['checked_at']
    report={'checked_at':now(),'status':'passed_with_explicit_limitations' if all(checks.values()) else 'failed',
        'checks':checks,'details':details,'package_manifest_sha256':sha(OUT/'package_manifest.json'),
        'formal_phase_complete':False,'human_gold':0,'independent_test_items':0,
        'limitations':['Integrity and recorded implementation tests only; no human gold certification','Reserved body is only hashed, never parsed']}
    if args.report:json_file(args.report,report)
    print(json.dumps({'status':report['status'],'checks_passed':sum(checks.values()),'checks_total':len(checks),
        'manifest_files':len(manifest['files']),'failed_checks':[k for k,v in checks.items() if not v]}))
    if not all(checks.values()):raise SystemExit(1)

if __name__=='__main__':main()
