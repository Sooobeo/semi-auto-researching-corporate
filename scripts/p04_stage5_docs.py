"""Record current operational status without converting agent work into human gold."""
from p04_common import *

def main():
    require_stage(4)
    for name in ['sampling_protocol.md','coverage_gaps.csv']:
        write(OUT/'stage_reviews/stage_05_before_improvement'/name,(OUT/name).read_text('utf-8'))
    path=OUT/'sampling_protocol.md';text=path.read_text('utf-8')
    text=text.replace('아직 확보했다고 세지 않는다.','초기 계획에서는 확보 전이었다. 2026-10-06 단일 후보 접근 1/1·예약 1/1을 완료했고 현재 상태는 `reserved_document_unlabeled`다. 메타데이터만 검사했으며 본문·수치·라벨·test 적격성은 미확인이다. 초기본은 `stage_reviews/stage_05_before_improvement/`에 보존했다.')
    path.write_text(text,encoding='utf-8')
    gaps=rows(OUT/'coverage_gaps.csv')
    for row in gaps:
        if row['stratum']=='unused_later_period':
            row['status']='one_document_reserved_unlabeled_not_independence_certified'
            row['next_action']='rights_body_overlap_audit_and_independent_labels_before_test'
    # The existing independent-family count remains zero for the uncertified reservation.
    with (OUT/'coverage_gaps.csv').open('w',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(gaps[0]));writer.writeheader();writer.writerows(gaps)
    statuses=[
        ('01','파일럿 표본 계획','agent_scope_fixed','실제 인간 시간·대표 표본 규모·무관/희귀 유형 미측정','sampling_protocol.md'),
        ('02','사건 family 그룹','agent_grouping_implemented','인간의 사건 단위 확인·신규 후보 중복 감사 필요','event_families.csv'),
        ('03','가이드·registry 고정','versioned_contracts_frozen','실제 인간 적용 가능성 검증 필요','annotation_freeze_v1_2.json'),
        ('04','연습 annotation','agent_practice_reviewed','인간 연습·소요시간 미실행','stage_reviews/practice_check_final.json'),
        ('05','본 표본 배정','agent_assignments_executed','실제 사람 역할·가용시간 배정 없음','assignment_execution.csv'),
        ('06','독립 사실 annotation','agent_drafts_reviewed_human_pending','인간 독립 주석 및 선정 계산의 사람 수행 증명 없음','annotations_raw.jsonl'),
        ('07','중요성 독립 평가','agent_responses_reviewed_prior_pending','prior·가정 부재; 인간 평가·역사적 블라인드 미실행','assessments_raw.jsonl'),
        ('08','일치도·원인 분석','agent_consistency_measured','인간 IAA·분별력·추출 정확도 미측정','agreement_report.md'),
        ('09','조정·gold 작성','agent_review_complete_human_gold_pending','인간 조정·gold 0; 39항목 미해결 판단 유지','gold_status.json'),
        ('10','시간·그룹 분할','adaptation_and_reservation_frozen','train/dev/test 미구성; 예약 후보 test 미인증','split_manifest.csv'),
        ('11','label 품질·연결','agent_link_validation_passed','인간 gold·전체 본문 수동 감사 없음','gold_validation.md'),
        ('12','dataset card·인계','agent_package_documented','독립 평가용 train/dev/test 및 정식 P04 인계는 대기','dataset_card.md')]
    csv_file(OUT/'task_status.csv',[{'task_id':'P04-T'+i,'task':label,'implementation_status':status,
        'formal_design_status':'partial_human_or_evaluation_requirements_pending','remaining':remaining,'artifact':artifact,
        'human_completed':'false'} for i,label,status,remaining,artifact in statuses])
    json_file(OUT/'phase_status.json',{'updated_at':now(),'phase':'P04 / Phase 3','authorized_work_packages':[1,2,3,4,5],
        'work_package_execution':'implemented_subject_to_stage_05_final_gate','formal_phase_complete':False,
        'formal_status':'agent_development_pilot_complete_human_gold_and_independent_evaluation_pending',
        'human_annotations':0,'human_adjudications':0,'human_gold_events':0,'human_gold_relations':0,
        'independent_test_items':0,'models_trained':0,'gold_files_intentionally_empty':True,
        'completion_authority':'stage_reviews/stage_05_final.json and package_validation.json',
        'notion_or_jira_changed':False,'task_status_ref':'task_status.csv'})
    write(OUT/'stage_reviews/stage_05_improvements.md','''# 5번 자가검증·개선

1. 독립 검사기는 root 구현을 읽지 않고 source metadata·원주석으로 split 43행과 의존성 27개를 재구성했다. 27개 변형 반례를 차단했다. 신규 비교열을 읽지 않았으므로 예약 후보의 독립성은 인증하지 않았다.
2. 초기 계획의 미확보 문구와 coverage gap이 실제 예약 상태와 달랐다. 초기본을 보존하고 후보 1개 예약·라벨 0·독립성 미확인으로 갱신했다.
3. base USD 계약과 백만 USD 주석의 읽기 계약을 dataset card에 나란히 적었다. 전용 인계 검사기의 배율·부호·참조 변형을 검사했다.
4. 인계 검사 초안이 전사 scope를 entity 집합에서 잘못 찾아 24개를 거부했다. 실패 보고서·초기 코드를 보존하고 registry scope 필드로 수정했다. 회사 ID를 scope로 바꾸는 반례를 추가한 최종 결과 39/39 및 13/13 통과.
5. reviewed 파일에서 생략된 date_conflict_status가 감사 완료로 오해되지 않도록 본문·날짜 수동 감사 미실행을 문서에 명시했다. 초기 agent 초안과 인간 gold의 경계를 task_status·phase_status·빈 gold 상태에 일관되게 기록했다.
6. source/input/가이드/주석/4번 검토 파일의 기존 hash를 대조하고 public 파일 manifest와 재실행 명령을 고정한다. private 원문과 정책은 Git 제외 상태로 유지하며 신규 예약의 본문은 읽지 않는다.
''')
    print(json.dumps({'task_status_rows':len(statuses),'reservation_status_updated':True,'formal_phase_complete':False}))

if __name__=='__main__':main()
