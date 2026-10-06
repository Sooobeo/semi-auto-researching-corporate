"""Explicit P06/P07 publication projection: facts, standard labels and templates only."""
from __future__ import annotations
import argparse
import json
import re
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
from p06_common import read,rows,sha,save,now
from p06_verify_package import verify_run as verify_p06
from p07_verify_package import verify_run as verify_p07

TEMPLATES={'human_review_missing':'사람의 독립 검토가 필요합니다.','selected_evidence_only':'선택한 셀 근거만 확인한 후보입니다.',
    'publication_time_unknown':'정확한 발표 시각은 미확인입니다.','date_conflict_not_audited':'발표 날짜 충돌 감사는 미완료입니다.',
    'retrospective_scope_dependency':'전사 정의에 사후 참고자료를 사용했습니다. 당시 근거 확인이 필요합니다.',
    'presentation_definition_requires_review':'발표별 사업부 표시 정의가 다릅니다. 같은 이름만으로 비교하지 않습니다.',
    'relation_validity_unknown':'보고 관계의 실제 사업 유효기간은 미확인입니다.','shared_numeric_evidence':'숫자 후보와 같은 근거를 사용한 관계입니다.',
    'comparison_conditions_checked':'P07의 비교 조건·계산·보류 결과를 연결했습니다.'}
FACT_FIELDS=['company_id','scope_id','definition_version','modality','evidence_status','metric_id','numeric_value','currency',
    'canonical_unit','scale','balance_or_flow','accounting_basis','relation_type','subject_entity_id','object_entity_id','direction','valid_from','valid_to']
CHANGE_FIELDS=['change_id','new_record_id','prior_record_id','comparison_basis','cutoff_mode','cutoff','new_doc_id','prior_doc_id',
    'new_revision_id','prior_revision_id','compatibility','status','reasons','old_value','new_value','delta','relative_delta',
    'relative_delta_missing_reason','change_types','unit','evidence_refs','formula_id','policy_version','review_readiness','evidence_status',
    'historical_eligible','source_record_refs','correction_confirmed','interpretation']
CALC_FIELDS=['calculation_id','formula_id','formula_version','cutoff_mode','cutoff','input_refs','status','output','output_unit',
    'missing_inputs','reasons','definition','rounding','historical_eligible']

def make(p06,p07):
    for check,path in [(verify_p06,p06),(verify_p07,p07)]:
        if check(path)['status']=='failed':raise ValueError('Cannot export unverified run')
    inputs=rows(p06/'input_records.jsonl');p7inputs=rows(p07/'event_store_records.jsonl')
    if inputs!=p7inputs:raise ValueError('Phase source universes differ')
    emap={e['evidence_id']:e for e in rows(ROOT/'artifacts/us_equity/p4/evidence_map.jsonl')}
    facts=[]
    for r in inputs:
        n=r['normalized'];t=n['temporal']
        facts.append({'record_id':r['record_id'],'prediction_id':r['provenance']['prediction_id'],'kind':r['record_kind'],
            'doc_id':r['doc_id'],'revision_id':r['revision_id'],'event_family_id':r['event_family_id'],'source_url':r['provenance']['source_url'],
            'normalized':{k:n.get(k) for k in FACT_FIELDS},'period':t['reference_period'],'published_date':t['published_date'],
            'published_at':t['published_at'],'observed_at':t['observed_at'],'scope_status_as_of':n['scope_status_as_of'],
            'date_conflict_status':t['date_conflict_status'],'historical_context_available':not bool(n['availability_dependencies']),
            'evidence':[{'evidence_id':e,'kind':emap[e]['kind'],'location':emap[e]['location'],'start':emap[e]['start'],'end':emap[e]['end'],'offset_unit':'unicode_code_point'} for e in r['evidence_refs']]})
    review=[]
    for r in rows(p06/'ranking_predictions.jsonl'):
        if not set(r['review_reasons'])<=set(TEMPLATES):raise ValueError('Non-template reason')
        review.append({k:r[k] for k in ['review_item_id','record_id','review_group_id','reason_group','policy_version','published_date','position',
            'review_reasons','missing_features','review_readiness','evidence_status','materiality_label','materiality_score','probability','score_type','historical_eligible','change_source_refs']})
    baseline=[r['record_id'] for r in rows(p06/'baseline_rankings.jsonl')]
    m6=read(p06/'run_manifest.json');m7=read(p07/'run_manifest.json')
    data={'schema_version':'p06-p07-site-0.1','generated_at':now(),'title':'기업 리서치 · 검토와 비교',
        'source_runs':{'P05':'m0_004','P06':p06.name,'P07':p07.name},'policies':{'P06':m6['policy_version'],'P07':m7['policy_version']},
        'source_output_hashes':{'P06':m6['output_hashes'],'P07':m7['output_hashes']},
        'summary':{'P06':m6['summary'],'P07':m7['summary']},'facts':facts,'review':review,'chronological_order':baseline,'reason_templates':TEMPLATES,
        'changes':[{k:c.get(k) for k in CHANGE_FIELDS} for c in rows(p07/'change_records.jsonl')],
        'calculations':[{k:c.get(k) for k in CALC_FIELDS} for c in rows(p07/'calculation_results.jsonl')],
        'priors':[{k:p[k] for k in ['new_record_id','cutoff_mode','selected_prior_id','review_comparator_id','status','candidate_count','excluded_count']} for p in rows(p07/'prior_state_records.jsonl')],
        'scenarios':rows(p07/'scenario_runs.jsonl'),'reconciliation_summary':{'attempts':len(rows(p07/'financial_reconciliations.jsonl')),'complete':0,'status':'incomplete','reason':'조정 항목과 보고 target 감사가 없어 순이익→CFO 대사를 완료하지 않았습니다.'},
        'verification':{'P06':{'checks':read(p06/'validation_report.json')['checks'],'synthetic_cases':len(read(p06/'synthetic_tests.json')['cases'])},
            'P07':{'checks':read(p07/'validation_report.json')['checks'],'synthetic_cases':len(read(p07/'synthetic_tests.json')['cases'])},
            'p03_regression':{'matched':read(p07/'p03_regression.json')['matched'],'total':read(p07/'p03_regression.json')['total'],'independent_evaluation':False}},
        'sharing':{'source_prose_included':False,'private_paths_included':False,'new_source_requests':0,'rights_checked_date':'2026-10-05','rights_basis':'기존 최소 숫자·표준 라벨·기간·위치의 사실 참조 범위','audience':'기존 지정 사용자','view':'게시 결과 snapshot'},
        'unperformed':['중요성 학습·확률 보정','독립 검색 qrels와 change gold','정식 성능 평가','사람의 날짜·범위 검토','전체 본문 완전성 감사','사람 가정과 실제 전망 scenario','동료 재실행','팀원 실제 접속 확인']}
    validate(data);return data

def validate(data):
    ids={r['record_id'] for r in data['facts']}
    if len(ids)!=len(data['facts']) or {r['record_id'] for r in data['review']}!=ids:raise ValueError('ID/universe mismatch')
    if any(r['review_readiness']!='needs_review' or r['materiality_score'] is not None or r['probability'] is not None for r in data['review']):raise ValueError('Unsupported score/review promotion')
    for c in data['changes']:
        if c['new_record_id'] not in ids or (c['prior_record_id'] and c['prior_record_id'] not in ids):raise ValueError('Broken change ref')
        if c['status']!='computed' and (c['delta'] is not None or c['relative_delta'] is not None):raise ValueError('Withheld numeric output')
    for c in data['calculations']:
        if not set(c['input_refs'])<=ids:raise ValueError('Broken calculation ref')
        if c['status']!='computed' and c['output'] is not None:raise ValueError('Failed calculation output')
    raw=json.dumps(data,ensure_ascii=False)
    if re.search(r'private[/\\]|(?:^|["\s])[A-Z]:[\\/]|password|api_key|bearer_token|raw_html|token_expires',raw,re.I):raise ValueError('Private/sensitive publication field')
    if any(r['normalized'].get('scale') not in ('1',None) for r in data['facts']):raise ValueError('Double scale risk')
    return True

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--p06-run',type=Path,required=True);p.add_argument('--p07-run',type=Path,required=True);p.add_argument('--output',type=Path,default=Path(__file__).parent/'dist/phases.json');a=p.parse_args()
    data=make(a.p06_run.resolve(),a.p07_run.resolve());save(a.output,data)
    save(a.output.parent/'phase-schema.json',{'$schema':'https://json-schema.org/draft/2020-12/schema','type':'object','required':['schema_version','source_runs','summary','facts','review','changes','calculations','sharing'],
        'properties':{'schema_version':{'const':'p06-p07-site-0.1'},'facts':{'type':'array','minItems':1},'review':{'type':'array','minItems':1},'changes':{'type':'array'},'calculations':{'type':'array'},'sharing':{'type':'object','properties':{'source_prose_included':{'const':False},'private_paths_included':{'const':False}}}}})
    print(json.dumps({'status':'passed','facts':len(data['facts']),'review':len(data['review']),'changes':len(data['changes']),'calculations':len(data['calculations']),'snapshot_sha256':sha(a.output)}))
