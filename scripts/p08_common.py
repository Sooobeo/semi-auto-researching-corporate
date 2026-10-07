"""P08 file contracts. No network, credentials, or source prose exports."""
from __future__ import annotations
import json
import os
import tempfile
import time
from pathlib import Path
from p06_common import ROOT, now, read, rows, sha, digest, stable, csvfile, textfile

VERSION = 'integration-0.1.0'
P7 = ROOT / 'artifacts/us_equity/p7'
STAGES = ('extract', 'compare', 'review', 'cards', 'feedback_snapshot', 'validate')
DEFAULT_CONFIG = {
    'schema_version': 'p08-config-0.1', 'source_run': 'm0_004',
    'p06_run': 'artifacts/us_equity/p5/runs/review_change_003',
    'p07_run': 'artifacts/us_equity/p6/runs/change_002',
    'cutoff': '2026-10-06', 'cutoff_mode': 'all', 'feedback_source_run': None,
    'stage_timeout_seconds': 120, 'feedback_store': 'artifacts/us_equity/p7/feedback',
    'rights_basis': 'existing narrow factual reference; no new collection or prose export',
}

def atomic(p, obj):
    p = Path(p); p.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile('w', encoding='utf-8', dir=p.parent, delete=False) as f:
        json.dump(obj, f, ensure_ascii=False, indent=2); f.write('\n'); name = f.name
        f.flush(); os.fsync(f.fileno())
    replace_with_retry(name, p)

def replace_with_retry(source, target):
    # Windows readers/virus scanners may briefly hold a shared file handle.
    for attempt in range(12):
        try: os.replace(source, target); return
        except PermissionError:
            if attempt == 11: raise
            time.sleep(0.05 * (attempt+1))

def write_rows(p, data):
    p = Path(p); p.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile('w', encoding='utf-8', dir=p.parent, delete=False) as f:
        for r in data: f.write(json.dumps(r, ensure_ascii=False) + '\n')
        name = f.name; f.flush(); os.fsync(f.fileno())
    replace_with_retry(name, p)

def inside(p, parent):
    p = Path(p).resolve(); parent = Path(parent).resolve()
    if not p.is_relative_to(parent) or p == parent: raise ValueError('path_outside_allowed_directory')
    return p

def config_check(c):
    if set(c) != set(DEFAULT_CONFIG): raise ValueError('unknown_or_missing_config_fields')
    if c['schema_version'] != DEFAULT_CONFIG['schema_version'] or c['source_run'] != 'm0_004':
        raise ValueError('unregistered_source')
    if c['cutoff_mode'] != 'all': raise ValueError('three_modes_required')
    from datetime import date
    date.fromisoformat(c['cutoff'])
    if c['cutoff'] != '2026-10-06': raise ValueError('frozen_development_cutoff_required')
    if c['feedback_source_run'] is not None:
        import re
        if not re.fullmatch(r'[A-Za-z0-9_-]{1,80}', c['feedback_source_run']): raise ValueError('invalid_feedback_source_run')
    if not isinstance(c['stage_timeout_seconds'], int) or not 1 <= c['stage_timeout_seconds'] <= 600:
        raise ValueError('invalid_timeout')
    for key, phase in [('p06_run', 'p5'), ('p07_run', 'p6')]:
        inside(ROOT/c[key], ROOT/f'artifacts/us_equity/{phase}/runs')
    inside(ROOT/c['feedback_store'], P7)
    if c['rights_basis'] != DEFAULT_CONFIG['rights_basis']: raise ValueError('rights_scope_changed')
    return c

def code_hashes():
    paths = sorted((ROOT/'scripts').glob('p08_*.py'))
    paths += [ROOT/'web/p05/phase_snapshot.py', ROOT/'web/p05/integration_snapshot.py', ROOT/'web/p05/server.py']
    return {p.relative_to(ROOT).as_posix(): sha(p) for p in paths}

def output_hashes(path):
    return {p.relative_to(path).as_posix(): sha(p) for p in sorted(Path(path).rglob('*')) if p.is_file()}

def hashes_ok(path, hashes):
    return all((Path(path)/p).is_file() and sha(Path(path)/p) == h for p, h in hashes.items())

def semantic(cards):
    return digest([{k: v for k, v in c.items() if k != 'run_id'} for c in cards])

CARD_SCHEMA = {
    '$schema': 'https://json-schema.org/draft/2020-12/schema', 'type': 'object',
    'required': ['card_id','card_version','run_id','candidate_refs','facts','changes','calculations',
                 'review_readiness','evidence_status','pipeline_status','materiality_assessment'],
    'properties': {'card_id': {'type': 'string'}, 'card_version': {'type': 'string'},
                   'candidate_refs': {'type': 'array', 'minItems': 1}, 'facts': {'type': 'array', 'minItems': 1},
                   'review_readiness': {'const': 'needs_review'}, 'evidence_status': {'const': 'company_reported'},
                   'pipeline_status': {'enum': ['succeeded','partial_failure']},
                   'materiality_assessment': {'type': 'object', 'properties': {'score': {'type': 'null'}}}}}

def validate_cards(cards, ids):
    mapped = [r for c in cards for r in c['candidate_refs']]
    checks = {
        'unique_cards': len({c['card_id'] for c in cards}) == len(cards),
        'every_candidate_once': len(mapped) == len(set(mapped)) and set(mapped) == set(ids),
        'candidate_status_preserved': all(c['review_readiness'] == 'needs_review' and
            c['evidence_status'] == 'company_reported' and c['materiality_assessment']['score'] is None for c in cards),
        'unknown_event_ids_preserved': all(c['event_id'] is None for c in cards),
        'version_integrity': all(c['card_version'] == digest({k:v for k,v in c.items() if k not in ('card_version','run_id')}) for c in cards),
        'change_refs_resolve': all(set(x['source_record_refs']) <= set(ids) for c in cards for x in c['changes']),
        'withheld_null': all(x['delta'] is x['relative_delta'] is None for c in cards for x in c['changes'] if x['status'] != 'computed'),
        'calculation_refs_resolve': all(set(x['input_refs']) <= set(ids) for c in cards for x in c['calculations']),
        'decimal_strings': all(f['normalized']['numeric_value'] is None or isinstance(f['normalized']['numeric_value'], str) for c in cards for f in c['facts']),
    }
    return checks
