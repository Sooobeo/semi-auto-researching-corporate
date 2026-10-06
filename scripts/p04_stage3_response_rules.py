"""Close a practice-discovered assessment vocabulary gap before main annotation."""
from p04_common import *

def main():
    require_stage(2)
    guide=(OUT/'annotation_guide_v1_1.md').read_text(encoding='utf-8').replace('가이드 v1.1','가이드 v1.2').replace('`us-p3-guide-1.1`','`us-p3-guide-1.2`')
    guide+='''

## v1.2 연습 응답 척도 보완

첫 연습에서 숫자/원문 대응은 통과했으나 MQ06의 partially_supported와 MQ08의 investigate_then_defer처럼 응답 vocabulary가 확장됐다. v1.1 원본은 유지하며 본작업 전에 P1 질문 후보의 명시적 응답 범위를 적용해 다시 연습한다. 복합 판단과 부분 지지는 reason에 기술하고 response는 허용된 한 값을 선택한다.

- MQ01~MQ05: yes / no / unknown / not_applicable.
- MQ06: sufficient / insufficient / unknown / not_applicable. 질문은 원문 위치·기간·scope 연결의 충분성이다. 부분만 확인됐을 때 무엇이 부족한지 reason에 적고 이 네 값 중 판단한다. 전체 문서 완전성이나 실적의 외부 진실성은 판정 대상이 아니다.
- MQ07: comparable / conditional / not_comparable / unknown. prior 미제공이면 unknown이다.
- MQ08: maintain / revise / investigate / defer / not_applicable / unable_to_judge. 조사 후 보류하려는 복합 행동은 대표 행동 하나와 reason으로 기록한다.

이 수정은 척도의 통일이며 A/B에게 특정 항목의 응답을 지정하지 않는다. facts와 독립 판단 이유는 보존한다. 두 번째 연습 이후 불일치가 남으면 본 주석의 원본을 유지하고 다음 단계에서 필드별로 비교한다.
'''
    write(OUT/'annotation_guide_v1_2.md',guide)
    contract=json.loads((OUT/'annotation_output_contract_v1_1.json').read_text(encoding='utf-8'))
    contract['contract_version']='us-p3-annotation-1.2';contract['guide_version']='us-p3-guide-1.2'
    enums={f'MQ{i:02d}':['yes','no','unknown','not_applicable'] for i in range(1,6)}
    enums.update(MQ06=['sufficient','insufficient','unknown','not_applicable'],
        MQ07=['comparable','conditional','not_comparable','unknown'],
        MQ08=['maintain','revise','investigate','defer','not_applicable','unable_to_judge'])
    contract['assessment_response_enums']=enums
    json_file(OUT/'annotation_output_contract_v1_2.json',contract)
    json_file(OUT/'stage_reviews/practice_vocabulary_findings.json',{'recorded_at':now(),
        'prior_practice_structural_and_source_review':'practice_check_001.json',
        'gap':'v1.1 omitted question response enums; source verification alone did not reject out-of-vocabulary assessment labels',
        'observed':{'AGENT-A':{'MQ06':'partially_supported','MQ08':'investigate'},
            'AGENT-B':{'MQ06':'partially_supported','MQ08':'investigate_then_defer'}},
        'improvement':'guide/contract1.2 explicit enum enforcement and fresh practice revision; preserve initial records',
        'specific_item_answers_shared':False})
    paths=['annotation_guide_v1_2.md','annotation_output_contract_v1_2.json','annotation_clarifications_v1_1.json',
        'annotation_reference.json','source_packets.jsonl','evidence_index.jsonl','practice_selection.json']
    json_file(OUT/'annotation_freeze_v1_2.json',{'frozen_at':now(),'guide_version':'us-p3-guide-1.2',
        'previous_freeze_sha256':sha(OUT/'annotation_freeze_v1_1.json'),
        'reason':'practice_response_vocabulary_gap','files':[{'path':p,'sha256':sha(OUT/p)} for p in paths]})
    print(json.dumps({'guide_version':'us-p3-guide-1.2','practice_recheck_required':True}))

if __name__=='__main__':main()
