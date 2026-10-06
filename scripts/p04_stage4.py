"""Compare original agent annotations and preserve reviewed drafts separately from gold."""
from __future__ import annotations
from collections import Counter, defaultdict
from p04_common import *

def pairs(records, key='item_id'):
    groups=defaultdict(dict)
    for row in records:
        actor=row['annotator_id']; item=row[key]
        if actor not in {'AGENT-A','AGENT-B'} or actor in groups[item]:
            raise ValueError('Duplicate or unexpected annotator: '+str(item))
        groups[item][actor]=row
    if any(set(g)!={'AGENT-A','AGENT-B'} for g in groups.values()):
        raise ValueError('Missing peer annotation')
    return {k:(v['AGENT-A'],v['AGENT-B']) for k,v in groups.items()}

def fact_agreement(grouped, contract):
    by_field=defaultdict(Counter); tuples=Counter(); mismatches=[]
    span={'pairs':0,'exact':0,'overlap_characters':0,'a_characters':0,'b_characters':0}
    for item,(a,b) in grouped.items():
        if a['item_type']!=b['item_type']:raise ValueError('Item kind disagreement')
        kind=a['item_type']; fields=contract['numeric_fact_fields'] if kind=='numeric_claim' else contract['relation_fact_fields']
        same=True
        for field in fields:
            if field not in a['facts'] or field not in b['facts']:raise ValueError('Missing fact field')
            av,bv=a['facts'][field],b['facts'][field]
            count=by_field[kind+'.'+field];count['pairs']+=1;count['exact']+=int(av==bv)
            if av is None and bv is None:count['both_null']+=1
            elif av is None or bv is None:count['one_null']+=1
            else:count['both_present']+=1;count['exact_both_present']+=int(av==bv)
            if av!=bv:same=False;mismatches.append({'item_id':item,'field':field,'a_value':av,'b_value':bv})
        tuples[kind+'_pairs']+=1;tuples[kind+'_exact']+=int(same)
        if kind=='numeric_claim':
            af,bf=a['facts'],b['facts'];sa,ea=af['value_span_start'],af['value_span_end'];sb,eb=bf['value_span_start'],bf['value_span_end']
            if af['doc_id']!=bf['doc_id'] or set(a['evidence_refs'])!=set(b['evidence_refs']):
                overlap=0
            else:overlap=max(0,min(ea,eb)-max(sa,sb))
            span['pairs']+=1;span['exact']+=int(sa==sb and ea==eb and overlap==ea-sa)
            span['overlap_characters']+=overlap;span['a_characters']+=ea-sa;span['b_characters']+=eb-sb
    fields=[]
    for name,c in sorted(by_field.items()):
        fields.append({'field':name,**{k:c[k] for k in ['pairs','exact','both_null','one_null','both_present','exact_both_present']},
            'exact_rate':c['exact']/c['pairs'],'exact_nonnull_rate':c['exact_both_present']/c['both_present'] if c['both_present'] else None})
    denom=span['a_characters']+span['b_characters']
    span['micro_character_overlap_f1']=2*span['overlap_characters']/denom if denom else None
    span['offset_basis']='original_DOM_cell_Unicode_code_points'
    return {'fields':fields,'tuple_counts':dict(tuples),'spans':span,'mismatches':mismatches}

def assessment_agreement(grouped):
    results=[];missing={'unknown','not_applicable','not_assessed','unable_to_judge'}
    for qid in [f'MQ{i:02d}' for i in range(1,9)]:
        confusion=Counter(); matches=0; usable=0;usable_matches=0
        for item,(a,b) in grouped.items():
            aq={q['question_id']:q for q in a['questions']};bq={q['question_id']:q for q in b['questions']}
            av,bv=aq[qid]['response'],bq[qid]['response'];confusion[(av,bv)]+=1;matches+=int(av==bv)
            if av not in missing and bv not in missing:usable+=1;usable_matches+=int(av==bv)
        results.append({'question_id':qid,'pairs':len(grouped),'exact':matches,'exact_rate':matches/len(grouped) if grouped else None,
            'both_substantive_pairs':usable,'exact_both_substantive':usable_matches,
            'exact_substantive_rate':usable_matches/usable if usable else None,
            'excluded_unknown_or_na_pairs':len(grouped)-usable,
            'confusion':[{'a':a,'b':b,'count':n} for (a,b),n in sorted(confusion.items())]})
    return results

def main():
    require_stage(3)
    annotations=rows(OUT/'annotations_raw.jsonl');assessments=rows(OUT/'assessments_raw.jsonl')
    grouped=pairs(annotations);assessment_pairs=pairs(assessments)
    if set(grouped)!=set(assessment_pairs):raise ValueError('Assessment item set mismatch')
    contract=json.loads((OUT/'annotation_output_contract_v1_2.json').read_text(encoding='utf-8'))
    agreement={'calculated_at':now(),'comparison_kind':'two_agent_shared_input_implementation_consistency',
        'guide_version':contract['guide_version'],'pre_adjudication':True,
        'source_files':[{'path':name,'sha256':sha(OUT/name)} for name in ['annotations_raw.jsonl','assessments_raw.jsonl']],
        'input_annotations':len(annotations),'unique_items':len(grouped),'fact_agreement':fact_agreement(grouped,contract),
        'assessment_agreement':assessment_agreement(assessment_pairs),'human_inter_annotator_agreement':None,
        'human_annotation_count':0,'extraction_accuracy':None,
        'chance_corrected_coefficient':None,
        'coefficient_reason':'No independent human labels; agent outputs share curated context and deterministic guide rules.',
        'limitations':['All source items are adaptation','Source IDs and registry metadata provide hints',
            'Guide exposes post-cutoff context; this is retrospective simulation','Both-null agreement is reported separately']}
    json_file(OUT/'agreement_results.json',agreement)
    csv_file(OUT/'agreement_by_field.csv',agreement['fact_agreement']['fields'])
    adjudications=[];claims=[];relations=[];assessment_reviews=[];unresolved=[]
    for i,(item,(a,b)) in enumerate(grouped.items(),1):
        aid=f'AGENT-ADJ-{i:03d}';fa,fb=a['facts'],b['facts']
        fields=contract['numeric_fact_fields'] if a['item_type']=='numeric_claim' else contract['relation_fact_fields']
        disagreements=[k for k in fields if fa[k]!=fb[k]]
        aa,ab=assessment_pairs[item];qa={q['question_id']:q for q in aa['questions']};qb={q['question_id']:q for q in ab['questions']}
        question_reviews=[]
        for qid in qa:
            av,bv=qa[qid]['response'],qb[qid]['response'];same=av==bv
            question_reviews.append({'question_id':qid,'input_responses':[av,bv],
                'input_assessment_ids':[aa['assessment_id'],ab['assessment_id']],
                'final_response':av if same else None,
                'status':'unresolved_information_missing' if same and av in {'unknown','unable_to_judge'} else 'agent_agreed' if same else 'unresolved_agent_disagreement',
                'rationale_refs':[{'assessment_id':x['assessment_id'],'question_id':qid} for x in [aa,ab]]})
        adjudications.append({'adjudication_id':aid,'item_id':item,'item_type':a['item_type'],
            'input_annotation_ids':[a['annotation_id'],b['annotation_id']],
            'adjudicator_id':'CODEX-ROOT','adjudicator_kind':'agent','created_at':now(),
            'mode':'source_checked_agent_merge','agreed_fact_fields':[k for k in fields if k not in disagreements],
            'disputed_fact_fields':disagreements,'selected_annotation_id':a['annotation_id'] if not disagreements else None,
            'rationale':'Matching agent fields were separately checked against the source-verified contract; agreement does not establish independent gold.',
            'source_check_ref':'stage_reviews/main_check_final.json','evidence_refs':a['evidence_refs'],
            'human_adjudication_status':'not_performed','gold_created':False,
            'review_readiness':'needs_review','readiness_reason':'Historical comparison prior not supplied; disclosed scope/presentation limitations remain.'})
        if disagreements:
            unresolved.append({'item_id':item,'category':'agent_fact_disagreement','fields':';'.join(disagreements),'status':'unresolved','next_action':'source_recheck_required'})
        else:
            final={'item_id':item,'record_kind':a['item_type'],'facts':fa,'provenance':a['provenance'],
                'field_missing_reasons':a['field_missing_reasons'],'evidence_refs':a['evidence_refs'],
                'source_annotation_ids':[a['annotation_id'],b['annotation_id']], 'adjudication_id':aid,
                'guide_version':contract['guide_version'],'registry_version':a['registry_version'],
                'status':'reviewed_agent_draft','human_gold':False,'split':'adaptation'}
            (claims if a['item_type']=='numeric_claim' else relations).append(final)
        assessment_reviews.append({'item_id':item,'adjudication_id':aid,'questions':question_reviews,
            'review_readiness':'needs_review','status':'agent_review_not_human_materiality_gold'})
        unresolved.append({'item_id':item,'category':'prior_not_provided','fields':'MQ01-MQ05;MQ07','status':'unresolved','next_action':'provide_asof_eligible_prior_and_assumptions'})
        if fa['scope_id']=='US-MSFT-CONSOLIDATED':
            unresolved.append({'item_id':item,'category':'historical_scope_support_unavailable','fields':'scope_status_as_of','status':'unresolved','next_action':'verify_publication_availability_of_scope_evidence'})
        elif a['item_type']=='numeric_claim':
            unresolved.append({'item_id':item,'category':'presentation_change_policy_unverified','fields':'definition_version;comparability','status':'unresolved','next_action':'source_policy_review_before_cross_presentation_comparison'})
        else:
            unresolved.append({'item_id':item,'category':'business_effective_dates_unknown','fields':'effective_period;valid_from;valid_to','status':'unresolved','next_action':'require_explicit_validity_evidence_if_needed'})
    jsonl(OUT/'adjudications.jsonl',adjudications)
    jsonl(OUT/'reviewed_agent_claims.jsonl',claims)
    jsonl(OUT/'reviewed_agent_relations.jsonl',relations)
    jsonl(OUT/'assessment_reviews.jsonl',assessment_reviews)
    events=[]
    for family in rows(OUT/'event_families.csv'):
        events.append({'event_id':family['event_id'],'event_family_id':family['event_family_id'],
            'doc_id':family['doc_id'],'company_id':family['company_id'],'event_type':'earnings_release',
            'claim_ids':[r['item_id'] for r in claims if r['facts']['event_id']==family['event_id']],
            'relation_ids':[r['item_id'] for r in relations if r['facts']['event_id']==family['event_id']],
            'grouping_status':'agent_announcement_anchor','human_gold':False,'split':'adaptation'})
    jsonl(OUT/'reviewed_agent_events.jsonl',events)
    csv_file(OUT/'unresolved_cases.csv',unresolved)
    jsonl(OUT/'gold_events.jsonl',[]);jsonl(OUT/'gold_relations.jsonl',[])
    json_file(OUT/'gold_status.json',{'recorded_at':now(),'status':'not_created_pending_independent_human_annotation',
        'gold_events':0,'gold_relations':0,'human_annotations':0,'human_adjudications':0,
        'reviewed_agent_numeric_claims':len(claims),'reviewed_agent_relations':len(relations),'agent_event_groups':len(events),
        'empty_file_reason':'No independent human annotation/adjudication provenance exists; empty files are not phase completion evidence.'})
    exact=sum(v for k,v in agreement['fact_agreement']['tuple_counts'].items() if k.endswith('_exact'))
    substantive=sum(x['both_substantive_pairs'] for x in agreement['assessment_agreement'])
    write(OUT/'agreement_report.md',f'''# P04 조정 전 agent 비교

두 agent의 본 주석 {len(annotations)}개를 {len(grouped)}개 item으로 정렬했다. 동일 원자료·가이드·등록부 문맥에서 작성한 결정적 변환의 일관성 검사다. 인간 독립 일치도와 시스템 추출 정확도는 미측정(null)이다.

- 사실 전체 tuple 일치: {exact}/{len(grouped)}. 숫자와 관계의 분모 및 필드별 exact/nonnull/null 수는 agreement_results.json과 agreement_by_field.csv에 있다.
- 숫자 span exact: {agreement['fact_agreement']['spans']['exact']}/{agreement['fact_agreement']['spans']['pairs']}. overlap은 원 DOM 셀 code point 문자 기준이며 토큰 F1과 구별한다.
- 질문 응답은 8질문×{len(grouped)}개 pair이다. unknown/NA 등을 뺀 양쪽 실질 응답 pair는 {substantive}개다. 분모가 0인 질문은 substantive rate=null이다. 조정 후 값을 원본 일치도 계산에 사용하지 않았다.
- MQ01~MQ05/MQ07의 unknown은 근거 부족이며 낮은 중요성이 아니다. 같은 unknown끼리의 일치로 판단 능력을 입증하지 않는다.
- 공유 가이드/metadata에 의한 일치이므로 사람용 chance-corrected 계수를 만들지 않았다. guide1.1 연습의 vocabulary 오류와1.2 보완은 별도 이력으로 보존한다.

39개 agent 조정 기록은 원본 annotation/assessment와 근거에 연결된다. 사실이 일치해도 과거 scope·사업부 표시 정책·prior 부재·실제 관계 유효기간은 미해결로 유지했다. 최종 산출물은 reviewed_agent_*이며 gold_events/gold_relations는 실제 인간 독립 원본이 없어 0건이다.
''')
    json_file(OUT/'stage_reviews/stage_04_initial.json',{'stage':4,'checked_at':now(),'status':'awaiting_independent_recalculation',
        'tuple_exact':exact,'tuple_pairs':len(grouped),'field_mismatches':len(agreement['fact_agreement']['mismatches']),
        'adjudications':len(adjudications),'unresolved_rows':len(unresolved),'human_gold':0})
    print(json.dumps({'stage':4,'exact_tuples':exact,'pairs':len(grouped),'agent_adjudications':len(adjudications),
        'reviewed_numeric':len(claims),'reviewed_relations':len(relations),'human_gold':0}))

if __name__=='__main__':main()
