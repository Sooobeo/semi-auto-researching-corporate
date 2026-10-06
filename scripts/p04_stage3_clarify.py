"""Record independently reported guide gaps without overwriting the stage-2 freeze."""
from p04_common import *

def main():
    require_stage(2)
    clarified = {
        'version':'us-p3-guide-1.1','previous_version':'us-p3-guide-1.0','created_at':now(),
        'trigger':'Both annotators independently reported missing registry naming/enums before practice execution.',
        'contains_item_answers':False,
        'definition_version':{'corporate':'us-financial-0.1','segment':'msft-segment-presentation-fy{source_release_fiscal_year}',
            'rule':'Use packet source_presentation_id release year, not comparative reference year.'},
        'currency':'USD','canonical_unit':'USD','scale':'1000000',
        'source_metadata_basis':'Preselected Microsoft financial-statement table references; these currency/accounting categories are curator-provided context, not independently inferred from a numeric cell.',
        'accounting_basis':'GAAP','accounting_basis_limit':'financial_statement_context_not_nonGAAP_reconciliation; company_policy_prose_not_audited',
        'sign_policy':{'default':'preserve','cash_ppe_additions':'outflow_to_positive'},
        'balance_or_flow':{'cash_and_equivalents':'balance','total_assets':'balance','other_selected_metrics':'flow'},
        'period_start_derivation':{'duration':'calendar_months_from_three_or_twelve_month_header','instant':'instant_end_date'},
        'period_kind':['duration','instant'],'duration_days_instant':None,
        'evidence_status':{'numeric_claim':'company_reported_unaudited','reporting_relation':'company_reported_table'},
        'speaker':'Microsoft Corporation',
        'scope_status_as_of':{'corporate':'unresolved_retrospective_dependency','segment':'reported_segment_in_selected_table'},
        'direction':'subject_to_object','relation_type':'reports_segment',
        'subject_role':'reporting_company','object_role':'reported_segment',
        'offset_basis':'Unicode code point; 0-based [start,end) within original DOM-cell text',
        'assessment_question_object':['question_id','response','reason'],
        'exposure_log_shape':{'flags':'array of required flags plus actual exposure','inputs':'array of files actually read'},
        'other_rules':['Recompute numeric values/spans/periods from raw cells and headers.',
            'Do not open source_record_ref paths as answer keys.',
            'Shared metadata means this is agent consistency work on preselected facts, not end-to-end extraction evaluation.']}
    json_file(OUT/'annotation_clarifications_v1_1.json',clarified)
    guide=(OUT/'annotation_guide_v1.md').read_text(encoding='utf-8')
    guide=guide.replace('가이드 v1.0','가이드 v1.1').replace('`us-p3-guide-1.0`','`us-p3-guide-1.1`')
    guide+='''

## v1.1 연습 전 보완

A/B가 서로의 답을 보지 않은 상태에서 공통 naming/enum의 누락을 각각 발견했다. `annotation_clarifications_v1_1.json`에 전사/사업부 definition_version 명명, USD/GAAP의 선정 자료 문맥, preserve/outflow_to_positive, balance/flow, 기간 유도 문자열과 provenance 표현을 고정했다. 특정 항목의 숫자/정답은 추가하지 않았다. 숫자·span·기간은 계속 raw cell과 머리글에서 계산한다.

원 1.0 가이드/계약 및 stage2 freeze는 보존한다. 이 버전은 stage3의 연습 및 본 주석에 적용하고 mapper 1.0 기록은 출처 비교용으로 유지한다. 공통 metadata 제공으로 작성자는 완전 비보조 추출자가 아니며 결과는 공유 입력 위의 agent 구현 일관성이다.
'''
    write(OUT/'annotation_guide_v1_1.md',guide)
    contract=json.loads((OUT/'annotation_output_contract.json').read_text(encoding='utf-8'))
    contract['contract_version']='us-p3-annotation-1.1'
    contract['guide_version']='us-p3-guide-1.1'
    contract['clarification_ref']='annotation_clarifications_v1_1.json'
    json_file(OUT/'annotation_output_contract_v1_1.json',contract)
    paths=['annotation_guide_v1_1.md','annotation_output_contract_v1_1.json','annotation_clarifications_v1_1.json',
        'annotation_reference.json','source_packets.jsonl','evidence_index.jsonl','practice_selection.json']
    json_file(OUT/'annotation_freeze_v1_1.json',{'frozen_at':now(),'guide_version':'us-p3-guide-1.1',
        'previous_freeze_sha256':sha(OUT/'contract_freeze_manifest.json'),
        'reason':'prepractice_annotator_questions_resolved_by_shared_enums_no_answers',
        'files':[{'path':p,'sha256':sha(OUT/p)} for p in paths]})
    print(json.dumps({'guide_version':'us-p3-guide-1.1','item_answers_added':False,'stage2_files_overwritten':False}))

if __name__=='__main__':main()
