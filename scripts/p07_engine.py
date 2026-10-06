"""Local sparse retrieval, conservative time/compatibility guards and Decimal math."""
from __future__ import annotations
from datetime import date, datetime
from decimal import Decimal, InvalidOperation, localcontext, ROUND_HALF_EVEN
from collections import Counter
import math
import re
from p06_common import stable

POLICY={'version':'prior-change-0.1.0','default_mode':'current_review','date_only':'strictly earlier prior date',
    'dependency_policy':'historical requires public evidence; current review permits observed retrospective context',
    'relative_delta':'(new-old)/abs(old); fraction, not percent','decimal_precision':28,'rounding':'ROUND_HALF_EVEN',
    'calendar_anniversary':'exact month/day endpoints; leap-year difference <=1 day', 'retrieval':'exact_key + local_label_tfidf'}
MODES=('current_review','historical_public','observed_live')

def moment_before(value, cutoff, strict=False):
    if not value:return False,'publication_unknown'
    try:
        if len(value)>10 and datetime.fromisoformat(value.replace('Z','+00:00')).tzinfo is None:return False,'timezone_unknown'
        if len(value)==10 or len(cutoff)==10:
            a=date.fromisoformat(value[:10]); b=date.fromisoformat(cutoff[:10])
            if a==b and len(value)==10 and len(cutoff)>10:return False,'same_day_order_unknown'
            if a==b and strict:return False,'same_day_order_unknown'
            return (a<b if strict else a<=b),None if (a<b if strict else a<=b) else 'future_information'
        a=datetime.fromisoformat(value.replace('Z','+00:00'));b=datetime.fromisoformat(cutoff.replace('Z','+00:00'))
        if not a.tzinfo or not b.tzinfo:return False,'timezone_unknown'
        ok=a<b if strict else a<=b
        return ok,None if ok else 'future_information'
    except (ValueError,TypeError):return False,'invalid_time'

def availability(r, mode, cutoff, strict=False):
    n=r['normalized'];t=n['temporal'];reasons=[]
    published=t.get('revision_published_at') or t.get('revision_published_date') or t.get('published_at') or t.get('published_date')
    ok,reason=moment_before(published,cutoff,strict)
    if not ok:reasons.append(reason)
    if mode in ('observed_live','current_review'):
        observed=t.get('observed_at');ok,reason=moment_before(observed,cutoff,True if len(cutoff)==10 else False)
        if not ok:reasons.append('observed:'+str(reason))
    for dep in n.get('availability_dependencies',[]):
        if mode=='current_review':
            value=dep.get('observed_at');ok,reason=moment_before(value,cutoff,True if len(cutoff)==10 else False)
        else:
            value=dep.get('published_at') or dep.get('published_date');ok,reason=moment_before(value,cutoff,True)
            if dep.get('use_policy','').startswith('current-only'):ok=False;reason='current_only_dependency'
            if mode=='observed_live':
                oo,rr=moment_before(dep.get('observed_at'),cutoff,True)
                if not oo:ok=False;reason='observed:'+str(rr)
        if not ok:reasons.append('dependency:'+str(reason))
    if mode!='current_review' and n.get('scope_status_as_of')=='unresolved_retrospective_dependency':reasons.append('scope_unresolved_at_cutoff')
    return {'eligible':not reasons,'reasons':list(dict.fromkeys(reasons)),'mode':mode,'cutoff':cutoff}

def period_valid(p, flow):
    try:
        if flow=='balance':return bool(p.get('as_of_date')) and bool(date.fromisoformat(p['as_of_date']))
        start=date.fromisoformat(p['period_start']);end=date.fromisoformat(p['period_end'])
        return flow=='flow' and (end-start).days+1==p.get('duration_days') and end>=start
    except (KeyError,ValueError,TypeError):return False

def period_aligned(a,b,flow,basis):
    if not period_valid(a,flow) or not period_valid(b,flow):return None
    keys=['as_of_date'] if flow=='balance' else ['period_start','period_end']
    if basis=='same_period_revision':return all(a.get(k)==b.get(k) for k in keys) and a.get('duration_days')==b.get('duration_days')
    if basis in ('yoy','within_release_comparison'):
        ds=[(date.fromisoformat(a[k]),date.fromisoformat(b[k])) for k in keys]
        return all(x.year==y.year+1 and (x.month,x.day)==(y.month,y.day) for x,y in ds) and (flow=='balance' or abs(a['duration_days']-b['duration_days'])<=1)
    return False

def compatible(new,old,basis):
    a=new['normalized'];b=old['normalized'];relation=new['record_kind']=='business_relation';checks={};reasons=[];unknown=[]
    keys=['company_id','scope_id','definition_version','modality']
    keys+=['relation_type','subject_entity_id','object_entity_id','direction','subject_role','object_role','negation','conditions'] if relation else [
        'metric_id','accounting_basis','currency','canonical_unit','scale','balance_or_flow','statement_type','consolidation','sign_policy']
    for k in keys:
        av,bv=a.get(k),b.get(k)
        checks[k]=None if av is None or bv is None else av==bv
        if checks[k] is None:unknown.append(k+'_unknown')
        elif not checks[k]:reasons.append(k+'_mismatch')
    if relation:
        checks['actual_validity_known']=bool(a.get('valid_from') and b.get('valid_from'))
        if not checks['actual_validity_known']:unknown.append('actual_relation_validity_unknown')
        else:
            checks['valid_period']=a['valid_from']==b['valid_from'] and a.get('valid_to')==b.get('valid_to')
            if not checks['valid_period']:reasons.append('relation_valid_period_mismatch')
    else:
        ap=a['temporal']['reference_period'];bp=b['temporal']['reference_period']
        for k in ('period_kind','period_basis'):
            checks[k]=ap.get(k)==bp.get(k) and ap.get(k) is not None
            if not checks[k]:reasons.append(k+'_mismatch')
        checks['actual_period_alignment']=period_aligned(ap,bp,a.get('balance_or_flow'),basis)
        if checks['actual_period_alignment'] is None:unknown.append('actual_period_unknown_or_invalid')
        elif not checks['actual_period_alignment']:reasons.append('actual_period_mismatch')
        for k in ('fiscal_quarter',):
            checks[k]=ap.get(k)==bp.get(k)
            if not checks[k]:reasons.append(k+'_mismatch')
        if a.get('scale')!='1' or b.get('scale')!='1':reasons.append('base_unit_required')
        if a.get('modality')!='actual_reported' or b.get('modality')!='actual_reported':reasons.append('nonactual_numeric_comparison_not_supported')
        for c in (a,b):
            if c.get('accounting_basis')=='non_GAAP' and not c.get('adjustment_definition'):unknown.append('adjustment_definition_unknown')
            if c.get('numeric_value') is None:unknown.append('numeric_value_missing')
            else:
                try:
                    if not Decimal(c['numeric_value']).is_finite():reasons.append('nonfinite_numeric_value')
                except (InvalidOperation,TypeError):reasons.append('invalid_numeric_value')
    return {'decision':'not_comparable' if reasons else ('needs_review' if unknown else 'comparable'),
        'checks':checks,'reasons':list(dict.fromkeys(reasons+unknown))}

def change(new,old,basis,mode,cutoff,policy=POLICY):
    comp=compatible(new,old,basis);na=availability(new,mode,cutoff);oa=availability(old,mode,cutoff)
    relation=new['record_kind']=='business_relation';reasons=comp['reasons']+na['reasons']+oa['reasons']
    out={'change_id':stable('CH',new['record_id'],old['record_id'],basis,mode,policy['version']),
        'new_record_id':new['record_id'],'prior_record_id':old['record_id'],'comparison_basis':basis,'cutoff_mode':mode,'cutoff':cutoff,
        'new_doc_id':new['doc_id'],'prior_doc_id':old['doc_id'],'new_revision_id':new['revision_id'],'prior_revision_id':old['revision_id'],
        'compatibility':comp,'status':'withheld','reasons':list(dict.fromkeys(reasons)),
        'old_value':old['normalized'].get('numeric_value'),'new_value':new['normalized'].get('numeric_value'),
        'delta':None,'relative_delta':None,'relative_delta_missing_reason':None,'change_types':[],
        'unit':'percent_point' if new['normalized'].get('canonical_unit')=='percent' else new['normalized'].get('canonical_unit'),
        'evidence_refs':sorted(set(new['evidence_refs']+old['evidence_refs'])),
        'formula_id':'absolute_and_relative_delta-0.1' if not relation else None,'policy_version':policy['version'],
        'review_readiness':'needs_review','evidence_status':'company_reported','historical_eligible':False,
        'source_record_refs':[new['record_id'],old['record_id']],'origin':'derived','correction_confirmed':False}
    # Equal same-period claims are revisions only; no invented correction relation.
    historical_cutoff=new['normalized']['temporal']['published_date']
    out['historical_eligible']=bool(historical_cutoff) and availability(new,'historical_public',historical_cutoff)['eligible'] and availability(old,'historical_public',historical_cutoff,basis!='within_release_comparison')['eligible'] and comp['decision']=='comparable'
    if relation:
        out['change_types']=['relation_state_unresolved'];return out
    if comp['decision']!='comparable' or not na['eligible'] or not oa['eligible']:
        out['change_types']=['not_comparable' if comp['decision']=='not_comparable' else 'comparison_unresolved'];return out
    with localcontext() as ctx:
        ctx.prec=policy['decimal_precision'];ctx.rounding=ROUND_HALF_EVEN
        nv=Decimal(out['new_value']);ov=Decimal(out['old_value']);delta=nv-ov
        out.update(status='computed',delta=format(delta,'f'),relative_delta=format(delta/abs(ov),'f') if ov else None,
            relative_delta_missing_reason=None if ov else 'zero_denominator',
            change_types=['same_period_difference_unconfirmed_revision' if basis=='same_period_revision' else basis],
            interpretation='negative_base_or_loss_transition' if ov<0 or nv<0 else 'arithmetic_change')
    return out

def key(r):
    n=r['normalized'];return (n['company_id'],r['record_kind'],n.get('metric_id') or n.get('relation_type'),n['scope_id'])
def tokens(r):
    n=r['normalized'];return re.findall(r'[a-z0-9]+',' '.join(str(n.get(k) or '') for k in ['company_id','scope_id','metric_id','relation_type','definition_version']).lower())

def retrieve(new,data,mode,review_cutoff,method):
    qt=new['normalized']['temporal'];prior_cutoff=qt.get('published_at') or qt.get('published_date')
    cutoff=review_cutoff if mode=='current_review' else (review_cutoff or prior_cutoff)
    base=[r for r in data if r['record_id']!=new['record_id'] and key(r)[:3]==key(new)[:3] and (method!='exact_key' or key(r)==key(new))]
    exclusions=[];eligible=[]
    for old in base:
        # Within-release comparative cells never become independent historical priors.
        chronology=moment_before(old['normalized']['temporal'].get('revision_published_at') or old['normalized']['temporal'].get('revision_published_date') or old['normalized']['temporal'].get('published_at') or old['normalized']['temporal'].get('published_date'),prior_cutoff,True) if prior_cutoff else (False,'query_publication_unknown')
        av=availability(old,mode,cutoff)
        if old['doc_id']==new['doc_id'] or not chronology[0] or not av['eligible']:
            exclusions.append({'record_id':old['record_id'],'reasons':list(dict.fromkeys((['same_release_not_independent_prior'] if old['doc_id']==new['doc_id'] else [])+([] if chronology[0] else [chronology[1]])+av['reasons']))})
        else:eligible.append(old)
    document_frequency=Counter(t for r in eligible for t in set(tokens(r)));query=set(tokens(new))
    scored=[]
    for old in eligible:
        score=1.0 if method=='exact_key' else sum(math.log((len(eligible)+1)/(document_frequency[t]+1))+1 for t in query & set(tokens(old)))
        basis='relation_state' if new['record_kind']=='business_relation' else ('same_period_revision' if new['normalized']['temporal']['reference_period']==old['normalized']['temporal']['reference_period'] else 'yoy')
        comp=compatible(new,old,basis)
        scored.append({'record_id':old['record_id'],'score':str(score),'compatibility':comp,'comparison_basis':basis,
            'publication_evidence':old['normalized']['temporal'],'evidence_refs':old['evidence_refs']})
    scored.sort(key=lambda r:(-float(r['score']),r['record_id']))
    for rank,r in enumerate(scored,1):r['rank']=rank
    good=[x for x in scored if x['compatibility']['decision']=='comparable']
    query_av=availability(new,mode,cutoff)
    selected=good[0]['record_id'] if len(good)==1 and query_av['eligible'] else None
    status='selected' if selected else ('query_unavailable' if not query_av['eligible'] else ('all_candidates_incompatible' if scored else ('all_candidates_time_excluded' if base else 'no_hit_in_limited_corpus')))
    if len(good)>1:status='ambiguous_compatible_priors'
    return {'query_id':stable('Q',new['record_id'],mode,method),'new_record_id':new['record_id'], 'cutoff_mode':mode,'cutoff':cutoff,
        'prior_cutoff':prior_cutoff,'method':method,'candidate_universe':len(base),'candidates':scored,'excluded':exclusions,
        'selected_record_id':selected,'status':status,'query_availability':query_av,'qrels_status':'not_evaluated',
        'corpus_scope':'selected structured labels and cells; not full text search'}

def calculate(formula,inputs,mode,cutoff):
    roles={'operating_margin':('operating_income','revenue'),'project_fcf':('cfo','positive_cash_capex')}
    out={'calculation_id':stable('CALC',formula,mode,*[r['record_id'] for r in inputs]),'formula_id':formula,'formula_version':'0.1',
        'cutoff_mode':mode,'cutoff':cutoff,'input_refs':[r['record_id'] for r in inputs],'status':'insufficient_inputs','output':None,
        'output_unit':'fraction' if formula=='operating_margin' else 'USD','missing_inputs':[],'reasons':[],
        'definition':'project operating_income/revenue' if formula=='operating_margin' else 'project CFO - positive cash capex; not company FCF',
        'origin':'derived','rounding':'28 significant digits / ROUND_HALF_EVEN','historical_eligible':False}
    if formula not in roles:return dict(out,status='invalid_formula',reasons=['formula_not_registered'])
    by_metric={r['normalized'].get('metric_id'):r for r in inputs};out['missing_inputs']=[x for x in roles[formula] if x not in by_metric]
    if out['missing_inputs']:return out
    ordered=[by_metric[x] for x in roles[formula]];a,b=[r['normalized'] for r in ordered]
    for k in ['company_id','scope_id','definition_version','accounting_basis','currency','canonical_unit','scale','balance_or_flow','modality']:
        if a.get(k) is None or a.get(k)!=b.get(k):out['reasons'].append(k+'_mismatch_or_unknown')
    if a['temporal']['reference_period']!=b['temporal']['reference_period']:out['reasons'].append('actual_period_mismatch')
    if a.get('scope_id')!='US-MSFT-CONSOLIDATED' or a.get('currency')!='USD' or a.get('scale')!='1' or a.get('modality')!='actual_reported' or a.get('balance_or_flow')!='flow':out['reasons'].append('formula_domain_mismatch')
    if not period_valid(a['temporal']['reference_period'],'flow'):out['reasons'].append('invalid_period')
    for r in ordered:out['reasons']+=availability(r,mode,cutoff)['reasons']
    try:
        av,bv=Decimal(a['numeric_value']),Decimal(b['numeric_value'])
        if not av.is_finite() or not bv.is_finite():raise InvalidOperation()
    except (InvalidOperation,TypeError):return dict(out,status='insufficient_inputs',reasons=out['reasons']+['numeric_input_missing_or_invalid'])
    if formula=='project_fcf' and (bv<0 or b.get('sign_policy')!='outflow_to_positive'):out['reasons'].append('positive_cash_capex_sign_required')
    if formula=='operating_margin' and bv==0:out['reasons'].append('zero_denominator')
    if out['reasons']:return dict(out,status='incompatible_inputs')
    with localcontext() as ctx:
        ctx.prec=28;ctx.rounding=ROUND_HALF_EVEN
        out['output']=format(av/bv if formula=='operating_margin' else av-bv,'f')
    out['status']='computed'
    hc=ordered[0]['normalized']['temporal']['published_date']
    out['historical_eligible']=all(availability(r,'historical_public',hc)['eligible'] for r in ordered)
    return out

def scenario(formula,values,assumptions=None):
    out={'formula_id':formula,'status':'insufficient_inputs','output':None,'missing_inputs':[], 'result_kind':'derived_forecast','assumption_refs':assumptions or []}
    if formula!='revenue_from_units_asp':return dict(out,status='invalid_formula',reasons=['formula_not_registered'])
    out['missing_inputs']=[k for k in ('units','asp','target_period','scope_id','currency') if values.get(k) is None]
    if out['missing_inputs']:return out
    if not assumptions:return dict(out,status='insufficient_inputs',missing_inputs=['reviewed_assumption_refs'])
    try:
        units,asp=Decimal(str(values['units'])),Decimal(str(values['asp']))
        if not units.is_finite() or not asp.is_finite() or units<0 or asp<0:return dict(out,status='incompatible_inputs',reasons=['invalid_units_or_asp'])
        with localcontext() as ctx:
            ctx.prec=28;ctx.rounding=ROUND_HALF_EVEN;output=format(units*asp,'f')
        return dict(out,status='computed',output=output,output_unit=values['currency'])
    except InvalidOperation:return dict(out,status='error',reasons=['invalid_decimal'])
