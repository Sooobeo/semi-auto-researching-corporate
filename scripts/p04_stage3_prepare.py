"""Freeze practice selection and two explicitly nonhuman annotation assignments."""
from p04_common import *

def main():
    require_stage(2)
    packets = rows(OUT/'source_packets.jsonl')
    ids = [
        'US-MSFT-FY2024-Q4-RELEASE-US-MSFT-CONSOLIDATED-revenue-FY2024-Q4-current_period',
        'US-MSFT-FY2025-Q4-RELEASE-US-MSFT-CONSOLIDATED-cfo-FY2025-FY-current_period',
        'US-MSFT-FY2024-Q4-RELEASE-US-MSFT-CONSOLIDATED-positive_cash_capex-FY2024-Q4-current_period',
        'US-MSFT-FY2025-Q4-RELEASE-US-MSFT-CONSOLIDATED-total_assets-FY2025-instant-current_period',
        'US-MSFT-FY2024-Q4-RELEASE-US-MSFT-SEG-IC-revenue-FY2024-FY-current_period',
        'US-MSFT-FY2025-Q4-RELEASE-US-MSFT-SEG-IC-revenue-FY2024-FY-comparative_prior_year',
        'US-MSFT-FY2024-Q4-RELEASE-REPORTS-PBP',
        'US-MSFT-FY2025-Q4-RELEASE-REPORTS-MPC']
    by_id = {p['item_id']:p for p in packets}
    assert set(ids) <= by_id.keys()
    json_file(OUT/'practice_selection.json',{'selected_at':now(),'item_ids':ids,
        'selection_kind':'purposive_rule_coverage_not_representative',
        'coverage':['quarterly','annual','instant','raw_negative_cash_capex','old_segment_presentation','comparative_new_presentation','reporting_relation'],
        'practice_repeated_in_main':True,'split':'adaptation','human_assignment_count':0})
    assignments=[]
    for phase, subset in [('practice',ids),('main',list(by_id))]:
        for i,item in enumerate(subset):
            for annotator in ['AGENT-A','AGENT-B']:
                assignments.append({'assignment_id':f'{phase}-{annotator}-{i+1:03d}',
                    'phase':phase,'item_id':item,'item_type':by_id[item]['item_type'],
                    'annotator_id':annotator,'annotator_kind':'agent','independent_context':'true',
                    'shared_source_and_guide':'true','human_independence_claim':'false',
                    'split':'adaptation','status':'assigned'})
    csv_file(OUT/'annotation_assignments.csv',assignments)
    write(OUT/'annotation_operations.md', '''# P04 agent 주석 운영

가이드/출력 계약을 고정한 뒤 새 agent 실행 맥락 A/B에 같은 raw packet과 공통 ID 참조를 제공한다. 상대의 주석/코드·mapper 변환 정답·P03 결과는 읽지 않는다. source packet의 ID와 참조 가이드는 의미 힌트를 포함하므로 이 절차는 비보조 자연어 추출 평가가 아니다.

연습은 8항목×2 작성자=16기록. 연습 검사/개선 이후 본작업 39항목×2 작성자=78기록을 생성한다. 연습 8항목은 본작업에도 포함되므로 독립 항목 수를 더하지 않는다. 기존 자료는 모두 adaptation이다. 실제 인간 배정/주석은 0이다.

annotation 원본·assessment 원본은 reviewer_a/reviewer_b별로 새 파일에 저장한다. 개선 전 기록을 지우지 않고 새 revision과 이유를 남긴다. agent 작성 스크립트와 실제 실행 시간·방법·노출 이력을 보존한다. 인간 소요시간·합의 gold로 표현하지 않는다.

연습 검사는 형식/원문값/기간/ID/노출·미상 기록의 결함을 찾는다. 본작업 전에 공유한 수정 규칙은 가이드 이력에 기록한다. 본작업의 A/B 조정 전 비교와 조정은 다음 순서에서 수행한다.
''')
    print(json.dumps({'practice_items':len(ids),'main_items':len(packets),'agent_assignments':len(assignments),'human_assignments':0}))

if __name__=='__main__': main()
