"""Deterministic review reasons/order; positions are never materiality scores."""
from __future__ import annotations
from p06_common import *

POLICY = {'version':'review-0.1.0', 'mode':'current_review',
    'group_order':['scope_availability','segment_definition','relation_validity','evidence_review'],
    'date_sort':'ascending; unknown last; record_id ascending for ties',
    'score_type':'not_estimated', 'change_policy':'missing_until_p07'}

def build(data, policy, links, changes=None):
    parent = {x['candidate_relation_id']:x['candidate_claim_id'] for x in links}
    change_map = {}
    for c in changes or []:
        change_map.setdefault(c['new_record_id'], []).append(c)
    features, items = [], []
    for r in sorted(data,key=lambda r:r['record_id']):
        n=r['normalized']; t=n['temporal']; rid=r['record_id']; relation=r['record_kind']=='business_relation'
        reasons=['human_review_missing','selected_evidence_only','publication_time_unknown','date_conflict_not_audited']
        suggestions=['선택한 근거와 숫자·기간·사업 범위를 사람이 확인하세요.','발표 날짜 충돌과 정확한 시각을 확인하세요.']
        group='evidence_review'
        if n['availability_dependencies'] or n['scope_status_as_of']=='unresolved_retrospective_dependency':
            group='scope_availability'; reasons+=['retrospective_scope_dependency']; suggestions+=['전사 정의의 발표 당시 근거를 확인하세요.']
        elif str(n['definition_version']).startswith('msft-segment'):
            group='segment_definition'; reasons+=['presentation_definition_requires_review']; suggestions+=['같은 사업부 이름의 발표별 표시 정의를 확인하세요.']
        if relation:
            reasons+=['relation_validity_unknown','shared_numeric_evidence']; suggestions+=['실제 사업 관계 유효기간을 확인하세요. 보고 관계를 매출 영향으로 해석하지 마세요.']
        connected=change_map.get(rid,[])
        computed=[c for c in connected if c['status']=='computed']
        historical=not bool(n['availability_dependencies']) and n['scope_status_as_of']!='unresolved_retrospective_dependency'
        values={'metric_or_relation':n.get('metric_id') or n.get('relation_type'),'scope_id':n['scope_id'],
            'modality':n['modality'],'evidence_linked':bool(r['evidence_refs']),
            'missing_field_count':sum(v not in ('not_applicable','not_applicable_to_numeric_claim','not_applicable_to_reporting_relation') for v in r['field_missing_reasons'].values()),
            'prior':None,'novelty':None,'financial_impact':None,'change':None}
        missing={'prior':'prior_not_available','novelty':'prior_not_available','financial_impact':'not_estimated','change':'not_yet_checked'}
        if changes is not None:
            values['change']=[{'change_id':c['change_id'],'status':c['status'],'comparison_basis':c['comparison_basis'],
                'delta':c['delta'],'relative_delta':c['relative_delta'],'historical_eligible':c['historical_eligible']} for c in connected]
            missing['change']=None if connected else 'no_change_record_in_limited_corpus'
            if connected:
                reasons+=['comparison_conditions_checked']; suggestions+=['비교 조건과 현재·과거 모드의 차이를 확인하세요.']
        features.append({'record_id':rid,'source_prediction_id':r['provenance']['prediction_id'],
            'values':values,'missing_reasons':missing,'origin':'derived','source_field_refs':['normalized','assessment','evidence_refs','field_missing_reasons'],
            'published_date':t['published_date'],'observed_at':t['observed_at'],'availability_dependencies':n['availability_dependencies'],
            'historical_eligible':historical,'change_source_refs':[c['change_id'] for c in connected],
            'change_historical_eligible':bool(computed) and all(c['historical_eligible'] for c in computed), 'train_fit':False})
        items.append({'review_item_id':stable('RI',rid),'record_id':rid,'candidate_claim_id':None if relation else rid,
            'candidate_relation_id':rid if relation else None,'prediction_id':r['provenance']['prediction_id'],
            'source_record_refs':[rid], 'source_run':r['provenance']['run_id'],'event_family_id':r['event_family_id'],
            'doc_id':r['doc_id'],'revision_id':r['revision_id'], 'review_group_id':stable('RG',parent.get(rid,rid)),
            'reason_group':group,'review_session_id':'MSFT-current-development','policy_version':policy['version'],
            'published_date':t['published_date'],'review_reasons':reasons,'missing_features':missing,'suggested_checks':suggestions,
            'review_readiness':'needs_review','evidence_status':n['evidence_status'],'materiality_label':None,
            'materiality_score':None,'probability':None,'score_type':'not_estimated','historical_eligible':historical,
            'exposure_status':'adaptation','change_source_refs':[c['change_id'] for c in connected]})
    key=lambda i:(i['published_date'] is None,i['published_date'] or '',i['record_id'])
    chronological=[]; ranked=[]
    for method,out,ordered in [('chronological',chronological,sorted(items,key=key)),
        ('reason_group_then_date',ranked,sorted(items,key=lambda i:(policy['group_order'].index(i['reason_group']),*key(i))))]:
        for position,item in enumerate(ordered,1):out.append(dict(item,ordering_method=method,position=position))
    return features,chronological,ranked

def synthetic_cases(data, links):
    from copy import deepcopy
    a=build(data,POLICY,links); b=build(list(reversed(data)),POLICY,links)
    cases=[('input_order_and_ties_stable',a==b),('all_candidates_retained',len(a[2])==len(data)),
        ('no_materiality_from_amount_or_relation',all(i['probability'] is None and i['materiality_score'] is None for i in a[2])),
        ('retrospective_context_not_historical',all(not f['historical_eligible'] for f in a[0] if f['availability_dependencies'])),
        ('prior_missing_not_zero',all(f['values']['prior'] is None and f['values']['novelty'] is None for f in a[0]))]
    copied=deepcopy(data[:1]);copied[0]['normalized']['temporal']['published_date']=None
    c=build(copied+data[1:],POLICY,links)[1]
    cases += [('unknown_date_last',c[-1]['record_id']==copied[0]['record_id']),
        ('readiness_never_promoted',all(i['review_readiness']=='needs_review' for i in a[2]))]
    return {'synthetic':True,'real_candidate_count':0,'cases':[{'name':n,'passed':bool(v)} for n,v in cases]}
