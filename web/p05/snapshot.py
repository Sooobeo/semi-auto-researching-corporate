"""Build the website's allowlisted factual view; never reads private source prose."""
from __future__ import annotations
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
P4=ROOT/'artifacts/us_equity/p4'
DIST=Path(__file__).parent/'dist'

def read(path):return json.loads(path.read_text('utf-8'))
def rows(path):return [json.loads(s) for s in path.read_text('utf-8').splitlines() if s.strip()]

def snapshot(run_dir=None):
    active=read(P4/'active_run.json')
    run_dir=run_dir or ROOT/active['run_dir']
    manifest=read(run_dir/'run_manifest.json')
    # Website reads finished runs only; verify that inference outputs remain frozen.
    for path,expected in manifest['output_hashes'].items():
        if hashlib.sha256((ROOT/path).read_bytes()).hexdigest()!=expected:
            raise ValueError('Frozen output changed')
    inputs={r['input_id']:r for r in rows(P4/'extractor_inputs.jsonl')}
    predictions=rows(run_dir/'predictions.jsonl')
    terminal=rows(run_dir/'input_results.jsonl')
    comparison=read(run_dir/'comparison_manifest.json')
    validation=read(run_dir/'validation_report.json')
    matches={r['prediction_id']:r for r in rows(run_dir/'reference_match_results.jsonl') if r['prediction_id']}
    records=[]
    for p in predictions:
        n=p['normalized'];m=matches.get(p['prediction_id']);r=inputs[p['input_id']]
        records.append(dict(id=p['prediction_id'],input_id=p['input_id'],kind=p['record_kind'],status=p['status'],
            doc_id=p['doc_id'],raw=p['raw'],normalized=n,
            review=p['assessment']['review_readiness'],review_reasons=p['assessment']['reasons'],
            source_url=p['provenance']['source_url'],source_sha256=p['provenance']['source_sha256'],
            definition=n['definition_version'],derived=p['derived'],
            comparison=dict(status=m['match_status'],matched=m['including_state_match'],
                fields=m['fields']) if m else None,
            evidence=[dict(kind=e['kind'],selected_text=e['selected_text'],location=e['location'],
                start=e['start'],end=e['end'],offset_unit=e['offset_unit']) for e in r['evidence']],
            context=dict(origin='curator_provided',scope=r['context']['scope_label'],
                         currency=r['context']['currency'],accounting=r['context']['accounting_basis'])))
    documents=[]
    for doc_id in dict.fromkeys(p['doc_id'] for p in predictions):
        group=[p for p in predictions if p['doc_id']==doc_id]
        documents.append(dict(id=doc_id,label='Microsoft '+('FY2024 Q4' if doc_id=='US-MSFT-FY2024-Q4-RELEASE' else 'FY2025 Q4'),
            published_date=group[0]['normalized']['temporal']['published_date'],
            source_url=group[0]['provenance']['source_url'],count=len(group)))
    counts=Counter(p['record_kind'] for p in predictions)
    statuses=Counter(r['status'] for r in terminal)
    tests=[]
    for name,label in [('stage_02_tests_final.json','입력·근거 연결'),('stage_04_rules_after_fix.json','숫자·기간 규칙'),('stage_04_adverse_tests.json','검증·비교')]:
        report=read(P4/'stage_reviews'/name)
        tests.append(dict(label=label,passed=report['passed'],total=report['total']))
    return dict(title='기업 리서치',run_id=manifest['run_id'],completed_at=manifest['completed_at'],
        rule_version=predictions[0]['rule_version'] if predictions else None,
        summary=dict(inputs=len(terminal),candidates=len(predictions),numeric=counts['numeric_claim'],
            relations=counts['reporting_relation'],documents=len(documents),families=len(documents),
            matched=sum(r['including_state_match'] for r in matches.values()),references=comparison['reference_count'],
            field_errors=comparison['field_errors'],statuses=dict(statuses),
            validation_passed=sum(validation['checks'].values()),validation_total=len(validation['checks']),
            source_locations=validation['source_locations_requeried'],
            inference_seconds=manifest['inference_seconds'],independent_test=0,human_gold=0),
        documents=documents,records=records,terminal=terminal,tests=tests,
        validation=dict(status=validation['status'],checks=validation['checks']),
        limitations=[dict(label='독립 성능 평가',detail='사람의 독립 정답과 별도 시험 자료가 없어 아직 측정하지 않았습니다.'),
            dict(label='선택한 셀에서 추출',detail='숫자 셀과 머리글을 미리 골라 제공했습니다. 문서 전체의 발견 성능은 이번 범위에 포함되지 않습니다.'),
            dict(label='검토가 필요한 사업 범위',detail='전사 범위의 후향 의존성과 발표별 사업부 표시 정의를 유지합니다. 같은 이름만으로 비교하지 않습니다.'),
            dict(label='날짜·실제 유효기간',detail='발표 날짜는 일 단위입니다. 날짜 충돌 감사와 사업부 관계의 실제 유효기간 확인은 미완료입니다.')],
        sharing=dict(contents='최소 숫자·표준 라벨·기간·위치 및 개발 결과',source_prose_included=False,
                     rights_basis='P0 source_conditions.md · 기존 개인·비상업 최소 사실 참조',checked_date='2026-10-05'))

def export(run_dir=None):
    data=snapshot(run_dir)
    path=DIST/'snapshot.json'
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n','utf-8')
    print(json.dumps(dict(run_id=data['run_id'],records=len(data['records']),snapshot=str(path),source_prose_included=False)))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--run-dir',type=Path)
    args=p.parse_args();export(args.run_dir.resolve() if args.run_dir else None)
