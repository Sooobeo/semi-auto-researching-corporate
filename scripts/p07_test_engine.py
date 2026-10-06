"""Counterexamples are synthetic development checks, never independent gold."""
from copy import deepcopy
from p06_common import *
from p07_engine import *

def test_cases(data):
    cases=[]
    def check(name, value):cases.append({'name':name,'passed':bool(value),'synthetic':True})
    new=deepcopy(next(r for r in data if r['normalized'].get('metric_id')=='revenue' and r['normalized']['temporal']['reference_period']['fiscal_year']==2025 and r['normalized']['scope_id']=='US-MSFT-CONSOLIDATED' and r['normalized']['temporal']['reference_period']['period_kind']=='quarter'))
    old=deepcopy(next(r for r in data if r['normalized'].get('metric_id')=='revenue' and r['normalized']['temporal']['reference_period']['fiscal_year']==2024 and r['normalized']['scope_id']=='US-MSFT-CONSOLIDATED' and r['normalized']['temporal']['reference_period']['period_kind']=='quarter'))
    check('retrospective_dependency_excluded',not availability(old,'historical_public','2025-07-30')['eligible'])
    check('late_observed_excluded',not availability(old,'observed_live','2025-07-30')['eligible'])
    check('current_review_not_historical',availability(old,'current_review','2026-10-06')['eligible'])
    check('same_day_date_order_unknown',moment_before('2025-07-30','2025-07-30',True)==(False,'same_day_order_unknown'))
    check('unknown_publication_withheld',not moment_before(None,'2025-07-30')[0])
    check('date_only_cutoff_never_fabricates_time',not moment_before('2025-07-30','2025-07-30T12:00:00+00:00',True)[0])
    ref=retrieve(new,data,'historical_public',None,'exact_key')
    future=deepcopy(old);future['record_id']='SYNTH-FUTURE';future['normalized']['temporal']['revision_published_date']='2027-01-01'
    future['normalized']['availability_dependencies']=[];future['normalized']['scope_status_as_of']='known'
    augmented=retrieve(new,data+[future],'historical_public',None,'exact_key')
    check('future_revision_does_not_change_eligible_priors',ref['candidates']==augmented['candidates'] and ref['selected_record_id']==augmented['selected_record_id'])
    same=deepcopy(old);same['doc_id']=new['doc_id'];same['normalized']['temporal']['published_date']='2025-07-30'
    hit=retrieve(new,[same],'current_review','2026-10-06','exact_key')
    check('same_release_prior_cell_not_historical',not hit['candidates'])
    for field,value in [('currency','EUR'),('scale','1000000'),('definition_version','different'),('balance_or_flow','balance'),('accounting_basis','non_GAAP'),('scope_id','different'),('modality','forecast')]:
        altered=deepcopy(old);altered['normalized'][field]=value
        check(field+'_mismatch_withheld',change(new,altered,'yoy','current_review','2026-10-06')['status']=='withheld')
    altered=deepcopy(old);altered['normalized']['temporal']['reference_period']['duration_days']=90
    check('invalid_period_length_withheld',compatible(new,altered,'yoy')['decision']!='comparable')
    altered=deepcopy(old);altered['normalized']['numeric_value']='0'
    z=change(new,altered,'yoy','current_review','2026-10-06')
    check('zero_value_is_real_but_ratio_null',z['status']=='computed' and z['relative_delta'] is None and z['relative_delta_missing_reason']=='zero_denominator')
    altered['normalized']['numeric_value']=None
    check('missing_value_not_zero',change(new,altered,'yoy','current_review','2026-10-06')['delta'] is None)
    altered['normalized']['numeric_value']='-10'
    negative=change(new,altered,'yoy','current_review','2026-10-06')
    check('negative_base_keeps_interpretation',negative['interpretation']=='negative_base_or_loss_transition')
    percent_new,percent_old=deepcopy(new),deepcopy(old)
    for r,val in [(percent_new,'25'),(percent_old,'20')]:
        r['normalized'].update(canonical_unit='percent',numeric_value=val)
    pct=change(percent_new,percent_old,'yoy','current_review','2026-10-06')
    check('percentage_points_not_relative_percent',pct['delta']=='5' and pct['relative_delta']=='0.25' and pct['unit']=='percent_point')
    real=change(new,old,'yoy','current_review','2026-10-06')
    check('base_usd_not_scaled_twice',real['delta']=='11714000000')
    fcf_inputs=[deepcopy(r) for r in data if r['doc_id']==new['doc_id'] and r['normalized'].get('metric_id') in ('cfo','positive_cash_capex') and r['normalized']['temporal']['reference_period']['period_kind']=='quarter']
    calc=calculate('project_fcf',fcf_inputs,'current_review','2026-10-06')
    check('positive_cash_capex_subtracted_once',calc['output']=='25568000000')
    fcf_inputs[1]['normalized']['numeric_value']='-1';fcf_inputs[1]['normalized']['sign_policy']='preserve'
    check('invalid_capex_sign_stops',calculate('project_fcf',fcf_inputs,'current_review','2026-10-06')['output'] is None)
    check('missing_formula_input_stops',calculate('project_fcf',[],'current_review','2026-10-06')['status']=='insufficient_inputs')
    rel=deepcopy(next(r for r in data if r['record_kind']=='business_relation'));other=deepcopy(rel);other['record_id']='SYNTH-REL'
    other['normalized']['direction']='object_to_subject'
    check('relation_direction_not_numeric_delta',change(rel,other,'relation_state','current_review','2026-10-06')['delta'] is None and compatible(rel,other,'relation_state')['decision']=='not_comparable')
    check('relation_unknown_validity_preserved',compatible(rel,rel,'relation_state')['decision']=='needs_review')
    planned=deepcopy(rel);planned['normalized']['modality']='plan'
    check('plan_actual_not_delta',change(rel,planned,'relation_state','current_review','2026-10-06')['delta'] is None)
    check('scenario_missing_inputs_stops',scenario('revenue_from_units_asp',{})['output'] is None)
    check('scenario_invalid_formula_stops',scenario('invented',{})['status']=='invalid_formula')
    vals={'units':'100','asp':'2','target_period':'SYNTH-future','scope_id':'SYNTH-product','currency':'USD'}
    check('scenario_no_assumptions_stops',scenario('revenue_from_units_asp',vals)['output'] is None)
    check('synthetic_scenario_arithmetic',scenario('revenue_from_units_asp',vals,['SYNTH-A'])['output']=='200')
    return {'synthetic':True,'real_candidate_count':0,'cases':cases}

if __name__=='__main__':
    data,_=audit_p05();result=test_cases(data);print(json.dumps({'passed':sum(c['passed'] for c in result['cases']),'total':len(result['cases']),'failed':[c['name'] for c in result['cases'] if not c['passed']]}));raise SystemExit(0 if all(c['passed'] for c in result['cases']) else 1)
