"""Reconcile independent calculations and freeze the reviewed agent package."""
from p04_common import *

def main():
    require_stage(3)
    agreement = json.loads((OUT/'agreement_results.json').read_text('utf-8'))
    independent = json.loads((OUT/'stage_reviews/stage_04_independent.json').read_text('utf-8'))
    result = independent['result']
    fields = {x['field']:x for x in agreement['fact_agreement']['fields']}
    field_matches = []
    for kind, group in result['fact_groups'].items():
        for key, values in group['fields'].items():
            other = fields[kind+'.'+key]
            field_matches.append(other['pairs']==values['all_pairs'] and other['exact']==values['all_exact_matches'])
    question_matches = []
    for q in agreement['assessment_agreement']:
        other = result['assessment_questions'][q['question_id']]
        question_matches.append(q['pairs']==other['all_pairs'] and q['exact']==other['all_exact_matches']
            and q['both_substantive_pairs']==other['observed_pairs'] and q['confusion']==other['confusion'])
    annotations=rows(OUT/'annotations_raw.jsonl'); by_id={r['annotation_id']:r for r in annotations}
    adjudications=rows(OUT/'adjudications.jsonl')
    reviewed=rows(OUT/'reviewed_agent_claims.jsonl')+rows(OUT/'reviewed_agent_relations.jsonl')
    evidence_ids={r['evidence_id'] for r in rows(OUT/'evidence_index.jsonl')}
    manifest=json.loads((OUT/'annotation_execution_manifest.json').read_text('utf-8'))
    checks={
        'independent_input_hashes_unchanged':all(sha(ROOT/p)==h for p,h in independent['source_input_hashes'].items()),
        'raw_reviewer_outputs_unchanged':all(sha(OUT/r['path'])==r['sha256'] for r in manifest['files']),
        'independent_validation_zero_errors':not independent['validation_errors'],
        'independent_counterexamples_22_of_22':independent['self_checks']['passed']==independent['self_checks']['total']==22,
        'all_64_field_counts_match':len(field_matches)==64 and all(field_matches),
        'all_8_question_confusions_match':len(question_matches)==8 and all(question_matches),
        'numeric_span_counts_match':agreement['fact_agreement']['spans']['overlap_characters']==result['spans']['intersection_code_points']==230,
        'all_39_adjudications_reference_two_originals':len(adjudications)==39 and all(len(a['input_annotation_ids'])==2 and all(i in by_id and by_id[i]['item_id']==a['item_id'] for i in a['input_annotation_ids']) for a in adjudications),
        'all_reviewed_items_have_evidence_and_no_gold':len(reviewed)==39 and all(not r['human_gold'] and set(r['evidence_refs'])<=evidence_ids and r['status']=='reviewed_agent_draft' for r in reviewed),
        'human_gold_files_empty':not rows(OUT/'gold_events.jsonl') and not rows(OUT/'gold_relations.jsonl'),
        'unresolved_rows_preserved':len(rows(OUT/'unresolved_cases.csv'))==78,
        'stage_sequence':independent['checked_at']>require_stage(3)['checked_at'],
    }
    if not all(checks.values()):raise ValueError(checks)
    # Preserve initial outputs before adding the stricter missing-state denominator.
    for name in ['agreement_results.json','agreement_report.md']:
        write(OUT/'stage_reviews/stage_04_before_improvement'/name,(OUT/name).read_text('utf-8'))
    agreement['observed_state_agreement']={
        'definition':independent['missing_policy'],
        'fact_groups':{kind:{k:v for k,v in g.items() if k!='fields'} for kind,g in result['fact_groups'].items()},
        'all_field_pairs':sum(g['micro_fields']['all_pairs'] for g in result['fact_groups'].values()),
        'observed_field_pairs':sum(g['micro_fields']['observed_pairs'] for g in result['fact_groups'].values()),
        'excluded_field_pairs':sum(g['micro_fields']['excluded_pairs'] for g in result['fact_groups'].values()),
        'fully_observed_tuple_pairs':sum(g['fully_observed_tuple']['denominator'] for g in result['fact_groups'].values()),
        'fully_observed_tuple_rate':None,
        'independent_report':'stage_reviews/stage_04_independent.json',
        'clarification':'nonnull includes unresolved string labels; observed excludes them. Neither is human agreement or accuracy.'}
    (OUT/'agreement_results.json').write_text(json.dumps(agreement,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    with (OUT/'agreement_report.md').open('a',encoding='utf-8') as stream:
        stream.write('''
## 자가검증 후 보완

별도 구현으로 원본 78건을 재계산하고 22개 반례를 검사했다. 전체 필드 비교는 1,329/1,329이며 null 127쌍과 unresolved 문자열 24쌍을 제외한 관측 필드 비교는 1,178/1,178이다. 기존 `nonnull` 열은 null만 제외하므로 미해결 문자열도 포함한다. 이를 관측 가능성과 혼동하지 않도록 `observed_state_agreement`와 독립 보고서의 필드별 분모를 추가했다.

숫자 관측 필드는 1,034/1,034, 관계는 144/144다. 모든 계약 필드가 관측된 완전 tuple은 0건이므로 해당 점수는 null이다. 39/39 전체 tuple 일치에는 같은 결측 상태끼리의 일치가 포함된다. MQ06과 MQ08을 제외한 6개 질문은 각각 39개 unknown으로 관측 분모 0, 점수 null이다. span 문자 비교는 230/230 code point이며 원문 진실 검증이나 end-to-end 추출 평가가 아니다.
''')
    write(OUT/'stage_reviews/stage_04_improvements.md','''# 4번 자가검증·개선

- 독립 계산기는 root 결과를 읽기 전에 원본과 계약만으로 구현했다. 64개 필드와 8개 질문의 전체 분모·일치·혼동표가 root 결과와 일치했다.
- 초기 보고서의 nonnull은 unresolved 문자열을 포함했다. 초기본을 보존하고 관측 필드 1,178/1,178, 제외 151쌍, 완전 관측 tuple 0/null을 추가했다.
- 중복·누락 peer·바뀐 ID·빠진 필드/질문·잘못된 span·타입 혼동·부분 겹침 등 22/22 반례 통과. 원본 및 연습·본 주석 해시 불변.
- 39개 조정은 양쪽 원본과 근거에 연결된다. 미해결 78행(고유 39항목), human gold 0을 유지한다.
- 4번 구현 검토를 통과한 뒤 5번 분할·인계 작업에 진입한다. 인간 주석 및 판정 완료를 뜻하지 않는다.
''')
    names=['agreement_results.json','agreement_report.md','adjudications.jsonl','reviewed_agent_claims.jsonl','reviewed_agent_relations.jsonl','reviewed_agent_events.jsonl','assessment_reviews.jsonl','unresolved_cases.csv','gold_events.jsonl','gold_relations.jsonl','gold_status.json','stage_reviews/stage_04_independent.json']
    json_file(OUT/'stage_reviews/stage_04_final.json',{'stage':4,'checked_at':now(),'gate':'passed_with_explicit_limitations','checks':checks,
        'files':[{'path':p,'sha256':sha(OUT/p)} for p in names],
        'counts':{'agent_item_pairs':39,'reviewed_numeric_claims':33,'reviewed_relations':6,'human_gold':0,'observed_field_pairs':1178},
        'limitations':['Shared-input agent consistency only','No fully observed complete tuple','Human gold remains absent'],'next_stage':5})
    print(json.dumps({'stage':4,'checks':len(checks),'passed':sum(checks.values()),'next_stage':5}))

if __name__=='__main__':main()
