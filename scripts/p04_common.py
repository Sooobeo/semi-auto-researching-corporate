"""Shared I/O for the P04 pilot. Existing evidence is never overwritten."""
from __future__ import annotations
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'artifacts/us_equity/p3'
SOURCE = ROOT / 'artifacts/us_equity/p0/available_20261005'
REGISTRY = ROOT / 'artifacts/us_equity/p2'

def now():
    return datetime.now(timezone.utc).isoformat()

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def rows(path):
    path = Path(path)
    if path.suffix == '.csv':
        with path.open(encoding='utf-8-sig', newline='') as stream:
            return list(csv.DictReader(stream))
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]

def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FileExistsError(f'Refusing to overwrite: {path}')
    with path.open('x', encoding='utf-8', newline='') as stream:
        stream.write(value)

def json_file(path, value):
    write(path, json.dumps(value, ensure_ascii=False, indent=2) + '\n')

def jsonl(path, values):
    write(path, ''.join(json.dumps(v, ensure_ascii=False) + '\n' for v in values))

def csv_file(path, values, fields=None):
    values = list(values)
    fields = fields or list(values[0])
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FileExistsError(f'Refusing to overwrite: {path}')
    with path.open('x', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(values)

def event_id(family):
    # Existing P03 relations already use this stable event anchor.
    return family

def require_stage(number):
    path = OUT / 'stage_reviews' / f'stage_{number:02d}_final.json'
    report = json.loads(path.read_text(encoding='utf-8'))
    if report.get('gate') != 'passed_with_explicit_limitations':
        raise ValueError(f'Stage {number} did not pass implementation review')
    return report
