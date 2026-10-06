"""Offline P05 I/O. All result writes are exclusive; no upstream mutations."""
from __future__ import annotations
import hashlib
import json
import os
import sys
from pathlib import Path
from p04_common import ROOT, rows, sha, now, write, json_file, jsonl, csv_file

P3 = ROOT / 'artifacts/us_equity/p3'
P4 = ROOT / 'artifacts/us_equity/p4'
SOURCE = ROOT / 'artifacts/us_equity/p0/available_20261005'
REGISTRY = ROOT / 'artifacts/us_equity/p2'
SCHEMA_VERSION = 'us-p4-prediction-0.1.0'
INPUT_VERSION = 'us-p4-selected-cells-0.1.0'
RULE_VERSION = 'm0-0.1.1'
REGISTRY_VERSION = 'us-p2-0.1.0'

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     separators=(',', ':')).encode('utf-8')).hexdigest()

def opaque(prefix, value):
    return prefix + digest(value)[:24]

def read_json(path):
    return json.loads(Path(path).read_text('utf-8'))

def hashes(paths):
    return {str(Path(p).resolve().relative_to(ROOT).as_posix()): sha(p) for p in paths}

def code_hashes():
    return hashes(sorted((ROOT / 'scripts').glob('p05_*.py')))

def validator(schema):
    try:
        import jsonschema
    except ModuleNotFoundError:
        cached = Path(os.environ['TEMP']) / 'p02-jsonschema-20261005'
        if not cached.is_dir():
            raise RuntimeError('Existing offline jsonschema dependency missing; no network fallback')
        sys.path.insert(0, str(cached))
        import jsonschema
    jsonschema.Draft202012Validator.check_schema(schema)
    return jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker())

def require_stage(n, out=P4):
    report = read_json(out / 'stage_reviews' / f'stage_{n:02d}_final.json')
    if report['gate'] != 'passed_with_explicit_limitations':
        raise ValueError(f'Stage {n} not passed')
    return report

def stage_report(n, phase, checks, details=None, out=P4):
    value = dict(stage=n, phase=phase, checked_at=now(),
                 gate='passed_with_explicit_limitations' if all(checks.values()) else 'needs_improvement',
                 checks=checks, details=details or {}, code_sha256=code_hashes(),
                 independent_evaluation='not_evaluated', human_gold=0,
                 limitations=['selected cells, shared adaptation references',
                              'no human gold or independent test', 'no full-body or date-conflict audit'])
    json_file(out / 'stage_reviews' / f'stage_{n:02d}_{phase}.json', value)
    return value

def normalize_fragment(raw, origin=0):
    """Collapse whitespace with a reversible per-character source interval map."""
    chars, mapping = [], []
    i = 0
    while i < len(raw):
        j = i + 1
        if raw[i].isspace():
            while j < len(raw) and raw[j].isspace():
                j += 1
            if chars and j < len(raw):
                chars.append(' '); mapping.append([origin+i, origin+j])
        else:
            chars.append(raw[i]); mapping.append([origin+i, origin+j])
        i = j
    return ''.join(chars), mapping

def semantic(prediction):
    value = json.loads(json.dumps(prediction))
    for k in ('run_id', 'prediction_id', 'candidate_claim_id', 'candidate_relation_id'):
        value.pop(k, None)
    return value
