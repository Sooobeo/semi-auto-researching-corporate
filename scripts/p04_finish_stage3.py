"""Freeze raw agent records only after practice and full-sample verification."""
from p04_common import *

def main():
    previous=require_stage(2)
    practice=json.loads((OUT/'stage_reviews/practice_check_final.json').read_text(encoding='utf-8'))
    maincheck=json.loads((OUT/'stage_reviews/main_check_final.json').read_text(encoding='utf-8'))
    if practice['status']!='passed' or maincheck['status']!='passed': raise ValueError('Annotation review incomplete')
    combined={}; input_files=[]
    for phase in ['practice','main']:
        for kind in ['annotations','assessments']:
            collection=[]
            for reviewer in ['a','b']:
                suffix_name='_v1_2' if phase=='practice' else ''
                path=OUT/f'reviewer_{reviewer}'/f'{phase}_{kind}{suffix_name}.jsonl'
                collection+=rows(path);input_files.append(path)
            combined[(phase,kind)]=collection
            name=('practice_'+kind if phase=='practice' else kind+'_raw')+'.jsonl'
            jsonl(OUT/name,collection)
    actual={}
    for phase in ['practice','main']:
        for row in combined[(phase,'annotations')]:
            actual[(phase,row['item_id'],row['annotator_id'])]=row
    executions=[]
    for assignment in rows(OUT/'annotation_assignments.csv'):
        row=actual[(assignment['phase'],assignment['item_id'],assignment['annotator_id'])]
        executions.append(dict(assignment_id=assignment['assignment_id'],annotation_id=row['annotation_id'],
            phase=assignment['phase'],item_id=row['item_id'],annotator_id=row['annotator_id'],
            annotator_kind='agent',guide_version=row['guide_version'],started_at=row['started_at'],
            completed_at=row['completed_at'],status='agent_draft_created_and_machine_checked'))
    csv_file(OUT/'assignment_execution.csv',executions)
    freeze=json.loads((OUT/'annotation_freeze_v1_2.json').read_text(encoding='utf-8'))
    annotations=combined[('main','annotations')]
    checks={'guide_freeze_unchanged':all(sha(OUT/f['path'])==f['sha256'] for f in freeze['files']),
        'practice_review_passed':practice['status']=='passed','main_source_and_contract_review_passed':maincheck['status']=='passed',
        'all_94_assignments_resolve':len(executions)==len(actual)==94,
        'main_78_agent_records':len(annotations)==78 and all(a['annotator_kind']=='agent' for a in annotations),
        'main_39_items_each_annotated_twice':len({a['item_id'] for a in annotations})==39 and all(sum(b['item_id']==a['item_id'] for b in annotations)==2 for a in annotations),
        'no_human_annotation_or_gold_claim':all(a['status']=='agent_draft' for a in annotations),
        'practice_before_main':all(a['started_at']>=practice['checked_at'] for a in annotations),
        'stage_sequence':previous['checked_at']<practice['checked_at']<maincheck['checked_at']}
    if not all(checks.values()):raise AssertionError(checks)
    write(OUT/'stage_reviews/stage_03_improvements.md','''# 3번 자가검증·개선

두 별도 agent 작업 맥락이 공통 raw packet/ID 가이드에서 주석을 작성했다. 서로의 답은 제공하지 않았고 동일 가이드/표본의 공유와 사후정보 노출은 명시했다. 접근 제한은 작업 지침이며 운영체제 ACL로 독립성을 보장한 실험은 아니다.

연습 전에 A/B 모두 definition_version 및 단위/부호/기간 라벨의 정확한 표기가 빠졌다고 질문했다. 특정 항목 답을 공유하지 않고 naming/enum 및 선정 표의 USD/GAAP 문맥만 v1.1로 보완했다. 이전 v1.0과 기준본은 그대로 보존했다. 이 보완은 가이드 수정 이력이며 agent 독립성이 완전 비보조 추출을 의미하지 않음을 추가했다.

첫 연습의 숫자 검사는 통과했으나 MQ06/MQ08 응답 vocabulary가 허용 범위를 넘은 문제를 발견했다. root 출력 계약이 응답 enum을 누락한 원인으로 기록하고 가이드/계약1.2와 validator 추가판을 만들었다. 기존1.1 연습16기록을 보존한 채1.2 연습을 다시 수행했다. 응답을 한 값으로 고르고 부분지지·복합행동은 이유에 쓰도록 정했으며 특정 항목 답은 공유하지 않았다.

최종 연습 8항목×2=16기록과 본작업 39항목×2=78기록을 각각 구조/원문값/기간/배율/부호/ID/span/과거 scope/필드별 null/assessment 사유/노출 이력으로 검사했다. 연습은 본작업에도 포함되므로 독립 항목은 39개다. 실수/수정 이력이 있다면 reviewer별 실행 로그와 practice/main check 보고서에 남아 있다. 원본 주석은 reviewer별 파일에 보존하고 집계 파일은 복사본이다.

현재 facts/assessments는 agent 초안이다. MQ01~MQ05/MQ07의 근거 부족을 unknown으로 유지하고 낮은 중요성/no로 바꾸지 않았다. 인간 원본, 인간 시간 측정, 인간 일치도, 인간 조정은 미실행이다.

다음 단계: 조정 이전 본 주석 78개를 고정한 뒤 A/B 필드/tuple/span 및 assessment 응답의 일치·불일치를 계산하고 agent 조정 기록을 별도 작성한다.
''')
    json_file(OUT/'annotation_execution_manifest.json',{'frozen_at':now(),'guide_version':'us-p3-guide-1.2',
        'files':[{'path':p.relative_to(OUT).as_posix(),'sha256':sha(p)} for p in input_files],
        'scripts':[{'path':f'scripts/p04_annotate_{r}.py','sha256':sha(ROOT/f'scripts/p04_annotate_{r}.py')} for r in ['a','b']],
        'counts':{'practice_items':8,'practice_annotations':16,'main_items':39,'main_annotations':78,'main_assessments':78,
            'human_annotations':0,'human_gold':0},'human_annotation_minutes':None,
        'peer_answer_visibility':'withheld_by_task_instruction_not_OS_access_control'})
    json_file(OUT/'stage_reviews/stage_03_final.json',{'stage':3,'checked_at':now(),'gate':'passed_with_explicit_limitations',
        'checks':checks,'annotation_manifest_sha256':sha(OUT/'annotation_execution_manifest.json'),
        'counts':{'practice_records':16,'main_records':78,'unique_annotation_items':39,'human_annotations':0},
        'limitations':['Agent-authored deterministic annotations on shared preselected inputs, not human annotation or extraction accuracy',
            'Historical cutoff simulation retains disclosed post-cutoff guide context'],'next_stage':4})
    print(json.dumps({'stage':3,'checks_passed':sum(checks.values()),'checks_total':len(checks)}))

if __name__=='__main__':main()
