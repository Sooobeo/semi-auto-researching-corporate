"""File contracts shared by the P06/P07 development runs (no network/prose)."""
from __future__ import annotations
import csv
import hashlib
import json
import platform
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
P4 = ROOT / 'artifacts/us_equity/p4'

def now(): return datetime.now(timezone.utc).isoformat()
def read(p): return json.loads(Path(p).read_text('utf-8'))
def rows(p): return [json.loads(x) for x in Path(p).read_text('utf-8').splitlines() if x.strip()]
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(obj): return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()
def stable(prefix, *parts): return prefix + '-' + digest(parts)[:24]
def save(p, obj): Path(p).write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', 'utf-8')
def jsonl(p, data): Path(p).write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in data), 'utf-8')
def csvfile(p, fields, data):
    with Path(p).open('w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(data)
def textfile(p, value): Path(p).write_text(value.rstrip() + '\n', 'utf-8')
def new_run(path):
    path = Path(path).resolve()
    path.mkdir(parents=True, exist_ok=False)
    return path

def audit_p05(source_run='m0_004'):
    active = read(P4/'active_run.json')
    if source_run != active['run_id']:
        raise ValueError('Source must be the verified active P05 run')
    package = read(P4/'package_manifest.json')
    if any(sha(ROOT/r['path']) != r['sha256'] for r in package['files']):
        raise ValueError('P05 frozen package changed; do not regenerate it')
    data = rows(P4/'candidate_store_records.jsonl')
    validated = rows(P4/'validated_candidates.jsonl')
    ids = {r['record_id'] for r in data}
    predicted = {r['candidate_claim_id'] or r['candidate_relation_id'] for r in validated}
    if len(data) != len(ids) or ids != predicted:
        raise ValueError('Candidate store/validated IDs differ')
    if any(r['provenance']['run_id'] != source_run or r['human_gold'] or r['record_status'] != 'candidate_needs_review' for r in data):
        raise ValueError('Unsupported candidate/gold state')
    inputs = [P4/x for x in ['active_run.json','candidate_store_records.jsonl','validated_candidates.jsonl',
        'relation_claim_links.jsonl','context_provenance.jsonl','evidence_map.jsonl','package_manifest.json',
        'input_snapshot.json','handoff_p4.md']]
    inputs += [ROOT/'artifacts/us_equity/p3/package_manifest.json',
        ROOT/'artifacts/us_equity/p3/split_manifest.csv', ROOT/'artifacts/us_equity/p3/exposure_manifest.csv',
        ROOT/'artifacts/us_equity/p0/available_20261005/source_conditions.md',
        ROOT/'artifacts/us_equity/p0/available_20261005/source_registry.csv',
        ROOT/'artifacts/us_equity/p0/available_20261005/document_manifest_v0_3.csv']
    snap = {'source_run': source_run, 'inputs': [{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)} for p in inputs],
        'candidate_count':len(data), 'numeric_count':sum(r['record_kind']=='event_claim' for r in data),
        'relation_count':sum(r['record_kind']=='business_relation' for r in data),
        'documents':len({r['doc_id'] for r in data}), 'families':len({r['event_family_id'] for r in data}),
        'human_gold':0, 'independent_test':0, 'reserved_body_read':False, 'legacy_inputs':[],
        'rights_basis':'existing narrow factual reference; no new source collection or prose export',
        'rights_checked_date':'2026-10-05', 'new_source_requests':0}
    return sorted(data, key=lambda r:r['record_id']), snap

def freeze(path, phase, policy, snap, summary, semantic_files):
    code = sorted((ROOT/'scripts').glob('p06_*.py'))
    if phase == 'P07': code += sorted((ROOT/'scripts').glob('p07_*.py'))
    manifest = {'phase_id':phase, 'run_id':path.name, 'completed_at':now(),
        'policy_version':policy['version'], 'policy_sha256':digest(policy), 'schema_version':phase.lower()+'-0.1',
        'input_snapshot_sha256':sha(path/'input_snapshot.json'), 'summary':summary,
        'code_hashes':{p.relative_to(ROOT).as_posix():sha(p) for p in code},
        'output_hashes':{p.name:sha(p) for p in sorted(path.iterdir()) if p.is_file()},
        'semantic_hash':digest({name:read(path/name) if name.endswith('.json') else rows(path/name) for name in semantic_files}),
        'semantic_files':semantic_files, 'environment':{'python':platform.python_version(),'dependencies':'Python standard library'},
        'development_status':'development_ready', 'research_status':'not_evaluated', 'formal_benchmark_complete':False}
    save(path/'run_manifest.json', manifest)
    return manifest

def verify(path, phase):
    path = Path(path).resolve(); m = read(path/'run_manifest.json'); snap = read(path/'input_snapshot.json')
    checks = {'phase':m['phase_id']==phase, 'outputs_frozen':all(sha(path/p)==h for p,h in m['output_hashes'].items()),
        'inputs_frozen':all(sha(ROOT/r['path'])==r['sha256'] for r in snap['inputs']),
        'code_frozen':all(sha(ROOT/p)==h for p,h in m['code_hashes'].items()),
        'semantic_hash':m['semantic_hash']==digest({n:read(path/n) if n.endswith('.json') else rows(path/n) for n in m['semantic_files']}),
        'no_formal_benchmark':not m['formal_benchmark_complete'],
        'validation_passed':all(read(path/'validation_report.json')['checks'].values()),
        'synthetic_passed':all(r['passed'] for r in read(path/'synthetic_tests.json')['cases'])}
    return {'status':'passed_with_explicit_limitations' if all(checks.values()) else 'failed',
        'checks':checks,'failed_checks':[k for k,v in checks.items() if not v],'summary':m['summary']}
