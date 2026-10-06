"""P06 CLI: audit P05, make review sidecars, freeze a new run."""
from __future__ import annotations
import argparse
from p06_common import *
from p06_review import POLICY, build, synthetic_cases

def run(source_run, run_dir, policy=None, change_run=None):
    data,snap=audit_p05(source_run); policy=policy or dict(POLICY)
    changes=None
    if change_run:
        from p07_verify_package import verify_run
        check=verify_run(change_run)
        if check['status']=='failed':raise ValueError('P07 run not verified')
        changes=rows(Path(change_run)/'change_records.jsonl')
        policy=dict(policy,version='review-0.2.0',change_policy='p07-current-review-sidecar')
        for name in ['run_manifest.json','change_records.jsonl']:
            p=Path(change_run).resolve()/name;snap['inputs'].append({'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)})
    features,baseline,ranking=build(data,policy,rows(P4/'relation_claim_links.jsonl'),changes)
    path=new_run(run_dir)
    save(path/'input_snapshot.json',snap);save(path/'policy.json',policy)
    jsonl(path/'input_records.jsonl',data);jsonl(path/'feature_records.jsonl',features)
    jsonl(path/'baseline_rankings.jsonl',baseline);jsonl(path/'ranking_predictions.jsonl',ranking);jsonl(path/'failed_items.jsonl',[])
    registry=[]
    for key in features[0]['values']:
        registry.append({'feature':key,'source_fields':'normalized/assessment/evidence_refs' if key!='change' else 'P07.change_records',
            'layer':'derived' if key in ('missing_field_count','evidence_linked','change') else 'normalized',
            'transform':'identity or explicit missing; no fitted transform','missing_policy':'null plus reason',
            'public_time_basis':'field dependencies checked; retrospective scope excluded historically',
            'observed_time_basis':'original temporal.observed_at','use_mode':'current_review','train_fit':'false',
            'leakage_risk':'adaptation; no independent evaluation','version':policy['version']})
    csvfile(path/'feature_registry.csv',list(registry[0]),registry)
    schema={'$schema':'https://json-schema.org/draft/2020-12/schema','type':'object',
        'required':['review_item_id','record_id','review_group_id','position','review_reasons','review_readiness','materiality_score','probability'],
        'properties':{'review_readiness':{'const':'needs_review'},'materiality_score':{'type':'null'},
            'probability':{'type':'null'},'position':{'type':'integer','minimum':1},'review_reasons':{'type':'array','minItems':1}}}
    save(path/'review_schema.json',schema)
    summary=dict(snap,candidate_count=len(ranking),review_groups=len({r['review_group_id'] for r in ranking}),
        change_connected_candidates=sum(bool(f['change_source_refs']) for f in features),formal_materiality_benchmark_complete=False)
    summary.pop('inputs')
    checks={'all_inputs_have_review_result':{r['record_id'] for r in ranking}=={r['record_id'] for r in data},
        'same_universe_in_both_views':{r['record_id'] for r in ranking}=={r['record_id'] for r in baseline},
        'shared_relation_evidence_grouped':all(next(x for x in ranking if x['record_id']==l['candidate_relation_id'])['review_group_id']==next(x for x in ranking if x['record_id']==l['candidate_claim_id'])['review_group_id'] for l in rows(P4/'relation_claim_links.jsonl')),
        'null_scores_and_readiness_preserved':all(r['materiality_label'] is r['probability'] is r['materiality_score'] is None and r['review_readiness']=='needs_review' for r in ranking),
        'evidence_refs_resolve':all(set(r['evidence_refs'])<={e['evidence_id'] for e in rows(P4/'evidence_map.jsonl')} for r in data)}
    tests=synthetic_cases(data,rows(P4/'relation_claim_links.jsonl'))
    save(path/'synthetic_tests.json',tests);save(path/'validation_report.json',{'checks':checks,'synthetic_cases':len(tests['cases']),'summary':summary})
    for name,body in {
        'readiness_report.md':f'# P06 입력 감사\n\nMicrosoft {snap["documents"]}개 발표 / {snap["families"]} family / {len(data)}개 후보. 신규 수집 0. 기존 최소 사실 참조 범위. 사람 gold 0; 전사 24개 사후 scope 의존. FY2026 예약 본문 미열람.',
        'materiality_protocol.md':'# 검토 목록 정책\n\n현재 자료 재검토. 사유 묶음 순서 후 발표일 오름차순, 날짜 미상 마지막, 동률 stable record ID. 같은 후보 universe의 시간순 목록 제공. 공유 숫자·관계 근거는 검토 묶음으로 연결. 위치는 중요성 등급/확률이 아니다.',
        'label_structure_report.md':'# 라벨 구조\n\n독립 사람 assessment 0. Agent 참조는 학습 정답으로 사용하지 않음. 중요성 판단과 일치도 미실행.',
        'calibration_report.md':'# 보정\n\nnot_evaluated: independent human labels/train/dev/calibration/test absent. probability=null. NDCG/recall=null.',
        'outcome_feasibility.md':'# 시장 outcome\n\n기본 경로 제외. 가격 권리·거래일·정확 발표시각·사건연구 프로토콜 미확보. 수집 0. 빈 manifest는 미실행을 뜻함.',
        'materiality_decision.md':'# 개발 결정\n\n학습 모델 대신 명시적 사유/시간 정렬을 구현. 금액·증가 방향·관계 존재로 중요성 판단하지 않음. 독립 평가 미실행.',
        'model_card.md':'# 모델 카드\n\n학습 모델 없음; 규칙 기반 검토 목록. Microsoft adaptation 2 family. 기업 간 일반화/정식 중요성 benchmark 미완료.',
        'change_feature_ablation.md':'# P07 연결\n\n'+('P07 검증 change ID/상태/현재 재검토 delta 연결. 역사적 적합성 별도 유지.' if change_run else '최초 run: change=null / not_yet_checked.')+' 독립 dev 0으로 성능 ablation 미실행.',
        'reproducibility_report.md':'# 재현\n\n입력 순서를 뒤집은 의미 결과 동일. run_manifest semantic_hash를 별도 run에서 비교하세요. timestamp/run 경로는 의미 결과에서 제외. 동료 재실행 미실행.',
        'handoff_p5.md':'# P06 → P07/P08\n\ninput_records/feature_records/ranking_predictions와 원 record/prediction/family/revision 연결. 사람 검토 needs_review 유지, 점수 null. 사이트 게시 기록은 site_update_manifest.json에 별도 저장.'
    }.items():textfile(path/name,body)
    csvfile(path/'representation_comparison.csv',['representation','execution_status','evaluation_count','metric','metric_reason'],
        [{'representation':x,'execution_status':'not_evaluated','evaluation_count':0,'metric':'null','metric_reason':'independent_human_labels_absent'} for x in ['ordinal','binary','multiaxis','continuous']])
    csvfile(path/'outcome_manifest.csv',['source','execution_status'],[])
    if not all(checks.values()) or not all(t['passed'] for t in tests['cases']):raise ValueError('P06 validation failed; failed run preserved')
    m=freeze(path,'P06',policy,snap,summary,['feature_records.jsonl','baseline_rankings.jsonl','ranking_predictions.jsonl'])
    print(json.dumps({'status':'development_ready','run_id':path.name,'summary':summary},ensure_ascii=False))
    return m

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-run',default='m0_004');p.add_argument('--run-dir',required=True,type=Path)
    p.add_argument('--policy',type=Path);p.add_argument('--change-run',type=Path);a=p.parse_args()
    run(a.source_run,a.run_dir,read(a.policy) if a.policy else None,a.change_run)
