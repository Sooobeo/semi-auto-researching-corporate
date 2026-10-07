"""Evaluate frozen development outputs under a protocol saved before measurement."""
import argparse
import platform
import subprocess
import sys
import time
from collections import Counter
from p09_common import *
from p08_verify_package import verify_run as v8
from p09_build_report import build

def init_protocol(path):
    path=inside(path,P8/'runs');path.mkdir(parents=True,exist_ok=False)
    active=P7/'active_run.json'; current=read(active) if active.exists() else {}
    snapshot=ROOT/'web/p05/dist/integration.json'
    atomic(path/'protocol.json',dict(PROTOCOL,frozen_at=now(),site_version_at_protocol=current.get('site_version_number'),
        site_snapshot_sha256=sha(snapshot) if snapshot.exists() else None))
    textfile(path/'evaluation_protocol.md','# 평가 protocol\n\nprotocol.json을 측정 전 고정합니다. S0/S1/S3의 동일 39 후보·두 문서·두 family·세 시점 조건을 검사합니다. 개발 회귀·재현·전체 보류 사례·실제 로컬 시간을 측정합니다. qrels/gold 없는 지표·비용 미측정·분모 0은 null입니다. 독립 dev 부재로 목표/임계값 선택 미완료. 정확도·수익률·사용성 향상은 결론으로 만들지 않습니다.\n\n원문/카드 사람 과업: 기간·범위·근거 찾기·비교 가능성·추가 질문. 최대 두 실제 참여자에게 비슷한 서로 다른 과업을 교차 순서로 배정합니다. 이미 본 자료는 practice, agent 열람/논의 후 판단은 독립 정답 제외. 시작/완료/중단/idle(60초 초과 별도 기록)·영어 이해·원문 열기·배포 버전·hash를 기록합니다. 실제 참여 전 결과는 비워 둡니다.')

def run(path, p08, reproduction):
    path=inside(path,P8/'runs');p08=inside(p08,P7/'runs');reproduction=inside(reproduction,P7/'runs')
    protocol=read(path/'protocol.json')
    if {k:protocol[k] for k in PROTOCOL} != PROTOCOL or (path/'run_manifest.json').exists(): raise ValueError('protocol_changed_or_run_completed')
    checks={'p08_verified':v8(p08)['status']!='failed','reproduction_verified':v8(reproduction)['status']!='failed'}
    if not all(checks.values()): raise ValueError('unverified_input')
    cards=rows(p08/'review_cards.jsonl');m8=read(p08/'run_manifest.json');repro=read(reproduction/'run_manifest.json')
    state=read(p08/'pipeline_state.json')
    test_name='resilience_tests.json' if (p08/'resilience_tests.json').exists() else 'synthetic_tests.json'
    synthetic=read(p08/test_name)
    refs={k:p08/v['output_dir'] for k,v in state['stages'].items()}
    compare=refs['compare']/'result'; review=refs['review']/'result'; extraction=refs['extract']/'replay'
    inputs=[p08/n for n in ('run_manifest.json','review_cards.jsonl',test_name,'feedback_snapshot.json','pipeline_state.json')]
    inputs += [reproduction/'run_manifest.json',compare/'run_manifest.json',review/'run_manifest.json',extraction/'comparison_manifest.json',path/'protocol.json']
    input_refs=[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)} for p in inputs]
    atomic(path/'frozen_run_manifest.json',{'frozen_at':now(),'protocol_sha256':sha(path/'protocol.json'),
        'inputs':input_refs,'code_hashes':code_hashes_p09(),'p08_code_hashes':m8['code_hashes'],
        'site_at_protocol':{'version_number':protocol.get('site_version_at_protocol'),
                            'snapshot_sha256':protocol.get('site_snapshot_sha256')},'systems':PROTOCOL['systems']})
    facts=[f for c in cards for f in c['facts']];ids={f['record_id'] for f in facts}
    rankings=rows(review/'ranking_predictions.jsonl');facts_by={f['record_id']:f for f in facts}
    systems=[];outputs={}
    for system in ('S0','S1','S3'):
        t=time.perf_counter()
        def materialize():
            if system=='S0': return sorted(facts,key=lambda f:(f['published_date'] or '9999',f['record_id']))
            if system=='S1': return [{'fact':facts_by[r['record_id']],'review':r} for r in rankings]
            return list(cards)
        records=materialize();duration=time.perf_counter()-t
        t=time.perf_counter();warm=materialize();warm_time=time.perf_counter()-t
        covered={i for c in records for i in c['candidate_refs']} if system=='S3' else {x['fact']['record_id'] for x in records} if system=='S1' else {x['record_id'] for x in records}
        checks[system+'_same_universe']=covered==ids
        outputs[system]=records;write_rows(path/f'{system}_records.jsonl',records)
        systems.append({'system':system,'status':'executed_development','records':len(records),'covered_candidates':len(covered),
            'documents':2,'families':2,'materialization_seconds':duration,'warm_seconds':warm_time,
            'unit':'card' if system=='S3' else 'candidate','reason':'exposed_development_not_independent'})
    for system in ('S2','S4','S5'):
        systems.append({'system':system,'status':'not_evaluated','records':None,'covered_candidates':None,'documents':2,'families':2,
            'materialization_seconds':None,'warm_seconds':None,'unit':'not_applicable',
            'reason':'independent_train_dev_human_labels_absent' if system=='S2' else 'ai_external_transfer_rights_and_budget_not_established'})
    checks['semantic_reproduction']=m8['semantic_hash']==repro['semantic_hash']
    checks['synthetic_tests']=synthetic['passed']==synthetic['total']
    from p09_test_evaluation import cases
    evaluation_tests=cases()
    checks['evaluation_gate_counterexamples']=evaluation_tests['passed']==evaluation_tests['total']
    checks['regression_no_field_errors']=read(extraction/'comparison_manifest.json')['field_errors']==0
    oldchecks={}
    for phase in ('p04','p05'):
        result=subprocess.run([sys.executable,str(ROOT/f'scripts/{phase}_verify_package.py')],cwd=ROOT,
            capture_output=True,text=True,encoding='utf-8',env={**os.environ,'PYTHONIOENCODING':'utf-8'},timeout=120)
        checks[phase+'_frozen_package']=result.returncode==0
        oldchecks[phase]={'exit_code':result.returncode,'status':'passed' if result.returncode==0 else 'failed'}
    changes=rows(compare/'change_records.jsonl');calcs=rows(compare/'calculation_results.jsonl')
    checks['no_computation_promotes_human_review']=all(c['review_readiness']=='needs_review' and c['human_gold'] is False for c in cards)
    counts={mode:{'attempts':sum(x['cutoff_mode']==mode for x in changes),
        'computed':sum(x['cutoff_mode']==mode and x['status']=='computed' for x in changes),
        'calculation_attempts':sum(x['cutoff_mode']==mode for x in calcs),
        'calculated':sum(x['cutoff_mode']==mode and x['status']=='computed' for x in calcs)} for mode in ('current_review','historical_public','observed_live')}
    failures=[{'case_id':x['change_id'],'stage':'compatibility_or_time','unit':'change_result','cutoff_mode':x['cutoff_mode'],
        'candidate_refs':x['source_record_refs'],'status':x['status'],'reasons':x['reasons'],'comparison_basis':x['comparison_basis']} for x in changes if x['status']!='computed']
    failures += [{'case_id':x['calculation_id'],'stage':'calculation','unit':'formula_attempt','cutoff_mode':x['cutoff_mode'],
        'candidate_refs':x['input_refs'],'status':x['status'],'reasons':x['reasons']+x['missing_inputs'],'comparison_basis':None} for x in calcs if x['status']!='computed']
    write_rows(path/'failure_cases.jsonl',failures)
    retrieval=rows(compare/'retrieval_results.jsonl');querygroups={}
    for q in retrieval:querygroups.setdefault((q['new_record_id'],q['cutoff_mode']),{})[q['method']]=q
    ablation=[]
    for (rid,mode),qs in querygroups.items():
        a,b=qs['exact_key'],qs['local_label_tfidf']
        ablation.append({'record_id':rid,'cutoff_mode':mode,'exact_selected':a['selected_record_id'],
            'sparse_selected':b['selected_record_id'],'selection_equal':a['selected_record_id']==b['selected_record_id'],
            'independent_qrels':False,'recall':None,'metric_reason':'empty_qrels_not_true_no_answer'})
    write_rows(path/'retrieval_development_comparison.jsonl',ablation)
    ready=readiness(2,0,0,0,'adaptation');atomic(path/'evaluation_readiness.json',ready)
    independent=[metric(n,None,None,0,'human_labeled_item' if n!='human_time_saved' else 'human_session','missing_independent_labels_qrels_or_sessions') for n in PROTOCOL['independent_metrics']]
    attempts=rows(p08/'stage_attempts.jsonl'); stage_wall=sum(x['elapsed_seconds'] for x in attempts)
    result={'schema_version':'p09-results-0.1','phase_id':'P09','run_id':path.name,'source_p08_run':p08.name,
        'protocol_version':VERSION,'summary':dict(m8['summary'],actual_participants=0,qrels=0),
        'systems':systems,'mode_counts':counts,'engineering_checks_passed':sum(checks.values()),'engineering_checks_total':len(checks),
        'synthetic_passed':synthetic['passed']+evaluation_tests['passed'],'synthetic_total':synthetic['total']+evaluation_tests['total'],
        'semantic_reproduction':checks['semantic_reproduction'],'reproduction_actor':'same_agent','colleague_reexecution':'not_performed',
        'independent_metrics':independent,'formal_benchmark_complete':False,'research_status':'not_evaluated',
        'external_calls':m8['external_calls'],'stage_wall_seconds':stage_wall,
        'cost':{'observed_operating_cost':None,'cost_per_1000_documents':None,'currency':None,'denominator_documents':2,'reason':'not_measured'},
        'withheld_change_count':sum(x['status']!='computed' for x in changes),
        'withheld_calculation_count':sum(x['status']!='computed' for x in calcs),
        'card_failures':len(rows(p08/'failed_items.jsonl')),
        'retrieval_queries':len(retrieval),'paired_query_groups':len(ablation),
        'exact_sparse_selection_agreement':sum(x['selection_equal'] for x in ablation),
        'retrieval_performance_status':'not_evaluated_no_qrels','ci':None,'p_value':None,
        'change_computed_breakdown':dict(Counter(x['comparison_basis'] for x in changes if x['status']=='computed' and x['cutoff_mode']=='current_review'))}
    atomic(path/'evaluation_results.json',result)
    atomic(path/'engineering_validation.json',{'checks':checks,'upstream':oldchecks,'status':'passed' if all(checks.values()) else 'failed'})
    atomic(path/'synthetic_tests.json',synthetic)
    atomic(path/'evaluation_gate_tests.json',evaluation_tests)
    csvfile(path/'review_sessions.csv',['session_id','actor_id','condition','task_id','exposure','started_at','completed_at','idle_seconds','status','site_version'],[])
    write_rows(path/'learning_cases.jsonl',[])
    textfile(path/'split_audit_final.md','# 노출·권리 감사\n\nMicrosoft 두 발표는 같은 exposed adaptation 그룹. 사람 gold·독립 test·qrels·세션은 0. 예약 FY2026 Q1 본문 미열람. 피드백/연습/agent 참조를 test나 학습으로 승격하지 않음. 신규 수집·외부 LLM 0회. 기존 소량 숫자·표준 라벨·기간·위치 참조 조건과 private/Git 제외 규칙 유지.')
    textfile(path/'study_protocol.md', '## 사람 세션 준비\n\n실제 참여 0명; 결과 미실행. 최대 두 명의 영어 이해·실제 역할을 기록합니다. 원문만/카드 조건에 비슷한 서로 다른 과업을 교차 배정하고, 사전 열람·agent 출력·논의 이력을 기록합니다. 날짜·범위·근거·비교 조건·추가 질문을 답하게 합니다. 실제 세션 시작/완료/중단/원문 열기/수정/60초 초과 idle를 별도 기록합니다. 빈 세션을 0초 또는 시간절감으로 표시하지 않습니다. ontology/NLP/business/financial 개인 수행은 실제 작성·수정·설명 증거가 있는 경우만 learning_cases.jsonl에 추가합니다.')
    textfile(path/'reproducibility.md',f'# 재현\n\n같은 agent 실행 `{p08.name}`와 `{reproduction.name}`의 카드 의미 hash 일치. 팀원 실제 재실행 미실행.\n\n```powershell\npython scripts/p08_run.py --run-dir artifacts/us_equity/p7/runs/<새 ID>\npython scripts/p08_verify_package.py --run-dir artifacts/us_equity/p7/runs/<새 ID>\npython scripts/p09_build_report.py --run-dir artifacts/us_equity/p8/runs/{path.name}\npython scripts/p09_verify_package.py --run-dir artifacts/us_equity/p8/runs/{path.name}\n```\n\n코드/설정/정책/입출력 hash는 frozen_run_manifest.json 및 upstream run_manifest.json 참조. 제한 원문·키·private·개인 메모는 공개 묶음 제외. 원문 위치 validator는 기존 허용 private Microsoft HTML의 로컬 접근에 의존하므로 이 자료가 없는 환경에서 원문 대조는 미실행입니다. 이미 생성된 최소 사실·카드·보고서 hash 검사는 원문 재배포 없이 가능합니다.')
    atomic(path/'demo_manifest.json',{'source_p08_run':p08.name,'candidate_count':39,'card_count':33,'selection':'all_development_records','synthetic_in_actual_counts':False,'raw_source_included':False,'private_source_dependency_for_source_validation':True})
    build(path)
    if not all(checks.values()): raise ValueError('engineering_validation_failed')
    files={p.name:sha(p) for p in path.iterdir() if p.is_file()}
    atomic(path/'run_manifest.json',{'phase_id':'P09','run_id':path.name,'protocol_version':VERSION,'inputs':input_refs,
        'code_hashes':code_hashes_p09(),'output_hashes':files,'formal_benchmark_complete':False,
        'development_status':'development_validation_ready','research_status':'not_evaluated','completed_at':now(),
        'environment':{'python':platform.python_version(),'platform':platform.platform(),'cpu':platform.processor(),'cpu_count':os.cpu_count(),
            'memory_peak_bytes':None,'network_collection_calls':0,'llm_calls':0}})
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run-dir',type=Path,required=True)
    p.add_argument('--init-protocol',action='store_true');p.add_argument('--p08-run',type=Path);p.add_argument('--reproduction-run',type=Path)
    a=p.parse_args()
    if a.init_protocol:init_protocol(a.run_dir);print('{"status":"protocol_frozen_before_measurement"}')
    else:
        d=run(a.run_dir,a.p08_run,a.reproduction_run)
        print(json.dumps({k:d[k] for k in ('run_id','engineering_checks_passed','engineering_checks_total','formal_benchmark_complete','research_status')}))
