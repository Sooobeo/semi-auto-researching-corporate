"""Read-only package integrity, input conservation, source QA, and reproducibility."""
from __future__ import annotations
import argparse
import subprocess
import sys
from pathlib import Path
from p05_common import *
from p05_compare_reference import compare
from p05_validate_predictions import ValidationContext, validate_run

def verify(out):
    manifest=read_json(out/'package_manifest.json');active=read_json(out/'active_run.json')
    run=out/'runs'/active['run_id'];repro=out/'runs'/active['reproduction_run']
    p04=subprocess.run([sys.executable,str(ROOT/'scripts/p04_verify_package.py')],capture_output=True,text=True,check=True)
    prior=json.loads(p04.stdout);snapshot=read_json(out/'input_snapshot.json')
    ctx=ValidationContext(out);preds=rows(run/'predictions.jsonl');results=rows(run/'input_results.jsonl')
    source_check=validate_run(ctx,preds,results)
    references=rows(P3/'reviewed_agent_claims.jsonl')+rows(P3/'reviewed_agent_relations.jsonl')
    evidence={r['evidence_id']:r for r in rows(P3/'evidence_index.jsonl')}
    compared=compare(preds,references,list(ctx.inputs.values()),list(ctx.maps.values()),evidence,[x['prediction_id'] for x in source_check['findings']])
    expected_files={p.resolve().relative_to(ROOT).as_posix() for p in out.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name not in ('package_manifest.json','package_validation.json')}
    expected_files|={p.relative_to(ROOT).as_posix() for p in (ROOT/'scripts').glob('p05_*.py')}
    expected_files|={p.relative_to(ROOT).as_posix() for p in (ROOT/'artifacts/us_equity/p4_attempts').rglob('*') if p.is_file()}
    inputs=list(ctx.inputs.values());stages=[require_stage(i,out) for i in range(1,6)]
    runmeta=read_json(run/'run_manifest.json');repmeta=read_json(repro/'run_manifest.json')
    private=[d['storage_uri'] for d in rows(SOURCE/'document_manifest_v0_3.csv')]
    ignored=subprocess.run(['git','check-ignore','--',*private],cwd=ROOT,capture_output=True,text=True,check=False)
    store=rows(out/'candidate_store_records.jsonl');export=rows(out/'validated_candidates.jsonl')
    checks=dict(p04_30_of_30=prior['checks_passed']==prior['checks_total']==30,
        package_file_set=expected_files=={f['path'] for f in manifest['files']},
        package_hashes=all(sha(ROOT/f['path'])==f['sha256'] for f in manifest['files']),
        upstream_preserved=all(sha(ROOT/x['path'])==x['sha256'] for x in snapshot['inputs']),
        gates_1_to_5=all(s['gate']=='passed_with_explicit_limitations' and all(s['checks'].values()) for s in stages),
        stage_order=all(a['checked_at']<b['checked_at'] for a,b in zip(stages,stages[1:])),
        numeric_inputs_33=sum(r['input_kind']=='numeric_cell' for r in inputs)==33,
        relation_inputs_6=sum(r['input_kind']=='relation_context' for r in inputs)==6,
        no_reserved_or_legacy=all(r['doc_id'] in ctx.rules['documents'] and r['doc_id']!='US-MSFT-FY2026-Q1-RELEASE' for r in inputs),
        input_allowlist=all(not ctx.iv.is_valid({**r,'source_claim_id':'probe'}) and ctx.iv.is_valid(r) for r in inputs),
        source_and_prediction_validation=all(source_check['checks'].values()),
        one_to_one_matching=compared['reference_keys_unique'] and all(m['match_status']=='matched' for m in compared['matches']),
        regression_fields=all(f['matched'] for m in compared['matches'] for f in m['fields']),
        independent_scores_null=all(m['value'] is None and m['denominator']==0 for m in compared['metrics'] if m['record_kind']=='independent'),
        semantic_reproduction=[semantic(p) for p in preds]==[semantic(p) for p in rows(repro/'predictions.jsonl')],
        current_code_frozen=runmeta['code_sha256']==repmeta['code_sha256']==code_hashes(),
        current_input_frozen=all(sha(ROOT/p)==h for p,h in runmeta['input_schema_registry_dependency_hashes'].items()),
        runtime_outputs_frozen=all(sha(ROOT/p)==h for p,h in runmeta['output_hashes'].items()),
        inference_reference_free=runmeta['reference_read_at'] is None and repmeta['reference_read_at'] is None and not runmeta['blocked_accesses'],
        offline_calls_zero=runmeta['external_calls']==repmeta['external_calls']==0,
        private_gitignored=set(ignored.stdout.splitlines())==set(private),
        private_not_packaged=not any('/private/' in f['path'] for f in manifest['files']),
        candidate_export_39=export==preds and len(store)==39,
        relation_links_6=len(rows(out/'relation_claim_links.jsonl'))==6 and all(l['candidate_claim_id'] for l in rows(out/'relation_claim_links.jsonl')),
        needs_review_and_no_human_gold=all(s['record_status']=='candidate_needs_review' and s['human_gold'] is False for s in store),
        synthetic_separate=all(not p['synthetic'] for p in preds),
        status_development_only=active['status']=='development_baseline_ready' and manifest['formal_p05_benchmark_complete'] is False)
    for name in ('stage_02_tests_final.json','stage_04_rules_after_fix.json','stage_04_adverse_tests.json'):
        t=read_json(out/'stage_reviews'/name);checks[name]=t['passed']==t['total'] and all(c['passed'] for c in t['cases'])
    report=dict(checked_at=now(),status='passed_with_explicit_limitations' if all(checks.values()) else 'failed',
                checks=checks,checks_passed=sum(checks.values()),checks_total=len(checks),failed_checks=[k for k,v in checks.items() if not v],
                package_manifest_sha256=sha(out/'package_manifest.json'),counts=dict(inputs=len(inputs),candidates=len(preds),
                numeric_candidates=33,reporting_relations=6,source_locations=84,role_bindings=88,
                upstream_files=len(snapshot['inputs']),package_files=len(manifest['files'])),
                human_gold=0,independent_evaluation='not_evaluated',manual_source_body_audit='not_performed')
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--input-dir',type=Path,default=P4);p.add_argument('--report',type=Path)
    a=p.parse_args();report=verify(a.input_dir)
    if a.report:json_file(a.report,report)
    print(json.dumps({k:report[k] for k in ('status','checks_passed','checks_total','failed_checks','counts')}))
    raise SystemExit(0 if report['status']=='passed_with_explicit_limitations' else 1)
