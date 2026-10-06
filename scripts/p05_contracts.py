"""Strict selected-cell and candidate envelopes, intentionally separate from P04 IDs."""
from p05_common import INPUT_VERSION, SCHEMA_VERSION

S = {'type': 'string'}
NS = {'type': ['string', 'null']}
NI = {'type': ['integer', 'null']}
B = {'type': 'boolean'}
NULL = {'type': 'null'}
STRINGS = {'type': 'array', 'items': S}

def obj(properties, required=None):
    return {'type': 'object', 'properties': properties,
            'required': list(properties) if required is None else required,
            'additionalProperties': False}

def enum(*values):
    return {'enum': list(values)}

def schemas():
    publication = obj(dict(published_date={'type': 'string', 'format': 'date'},
                           published_at=NULL, time_precision={'const': 'date'}, observed_at=S))
    evidence = obj(dict(evidence_id=S, kind=enum('numeric_value','row_label','period_header','year_header','unit'),
                        location=S, table_id=S, row_index=NI, col_index=NI,
                        start={'type':'integer','minimum':0}, end={'type':'integer','minimum':1},
                        raw_fragment=S, fragment_origin={'type':'integer','minimum':0},
                        selected_text=S, normalized_fragment=S,
                        normalized_to_raw={'type':'array','items':{'type':'array','items':{'type':'integer'},'minItems':2,'maxItems':2}},
                        header_refs=STRINGS, offset_unit={'const':'unicode_code_point'},
                        offset_interval={'const':'0-based-[start,end)'}))
    inp = obj(dict(schema_version={'const':INPUT_VERSION}, input_id={'type':'string','pattern':'^I-[a-f0-9]{24}$'},
                   input_kind=enum('numeric_cell','relation_context'), input_mode={'const':'preselected_cells'},
                   doc_id=S, revision_id=S, source_sha256={'type':'string','pattern':'^[a-f0-9]{64}$'},
                   publication=publication,
                   raw=obj(dict(value_cell=NS,row_label=S,period_header=S,year_header=S,unit_header=S)),
                   context=obj(dict(context_origin={'const':'curator_provided'}, context_provenance_ref=S,
                                    company_name=S,company_id=S,scope_label=S,
                                    table_purpose=enum('company_financial_statement','segment_revenue'),
                                    currency=NS,accounting_basis=NS,source_qualifier=S)),
                   evidence={'type':'array','items':evidence,'minItems':1}, synthetic=B))
    period = obj(dict(period_start=NS,period_end=NS,as_of_date=NS,period_kind=enum('quarter','annual','instant'),
                      fiscal_year={'type':'integer'},fiscal_quarter=NI,duration_days=NI,period_basis={'const':'fiscal'}))
    temporal = obj(dict(published_date=S,published_at=NULL,time_precision={'const':'date'},
                        timezone=NULL,observed_at=S,available_at=NULL,date_conflict_status={'const':'not_yet_checked'},
                        reference_period=period,effective_period=NULL))
    normalized = obj(dict(company_id=S,scope_id=S,definition_version=S,modality={'const':'actual_reported'},
                          evidence_status={'const':'company_reported'},temporal=temporal,scope_status_as_of=S,
                          availability_dependencies={'type':'array','items':obj(dict(record_id=S,published_date=NULL,observed_at=S,sha256=S,use_policy=S))},
                          metric_id=NS,numeric_value={'type':['string','null'],'pattern':r'^-?\d+(\.\d+)?$'},
                          currency=NS,canonical_unit=NS,scale=NS,source_scale=NS,source_numeric_value=NS,
                          sign_policy=NS,balance_or_flow=NS,statement_type=NS,accounting_basis=NS,
                          relation_type=NS,subject_entity_id=NS,object_entity_id=NS,subject_role=NS,object_role=NS,
                          direction=NS,negation=B,conditions={'type':'array','items':S},valid_from=NULL,valid_to=NULL))
    pred = obj(dict(schema_version={'const':SCHEMA_VERSION},registry_version=S,rule_version=S,
                    prediction_id=S,run_id=S,input_id=S,doc_id=S,revision_id=S,
                    candidate_claim_id=NS,candidate_relation_id=NS,
                    record_kind=enum('numeric_claim','reporting_relation'),input_mode={'const':'preselected_cells'},
                    status=enum('predicted','abstained','failed','quarantined'),synthetic=B,
                    raw=obj(dict(value_raw=NS,value_cell=NS,row_label=S,period_header=S,year_header=S,
                                 unit_header=S,source_qualifier=S,value_span_start=NI,value_span_end=NI)),
                    normalized=normalized,
                    assessment=obj(dict(review_readiness={'const':'needs_review'},reasons=STRINGS,
                                        rule_signal=STRINGS,score_type={'const':'uncalibrated_rule'},probability=NULL)),
                    derived={'type':'array','items':obj(dict(formula_id=S,input_refs=STRINGS,output=NS,
                                                           rounding_policy=S,origin={'const':'derived'}))},
                    provenance=obj(dict(source_sha256=S,source_url=S,rights_basis_ref=S,context_origin={'const':'curator_provided'},
                                        context_provenance_ref=S,exposure={'const':'adaptation'},
                                        leakage_group=S,historical_blind={'const':False},source_parser_version=S)),
                    evidence_refs=STRINGS,field_missing_reasons={'type':'object','additionalProperties':S}))
    for schema in (inp, pred):
        schema['$schema']='https://json-schema.org/draft/2020-12/schema'
    return inp, pred
