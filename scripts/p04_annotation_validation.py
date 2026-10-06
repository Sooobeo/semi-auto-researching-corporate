"""Validate agent annotation packets without claiming human gold or accuracy."""
from __future__ import annotations
import re
from datetime import date
from decimal import Decimal, InvalidOperation
from p04_common import OUT, rows

def validate_annotation(row, packets, contract):
    errors = []
    for key in contract['required_top_level']:
        if key not in row:
            errors.append('missing:' + key)
    if errors:
        return errors
    if row['annotator_kind'] != 'agent' or row['status'] != 'agent_draft':
        errors.append('agent_output_must_not_claim_human_or_gold')
    if row['method'] != contract['method']:
        errors.append('undisclosed_annotation_method')
    if row['guide_version'] != contract['guide_version']:
        errors.append('wrong_guide_version')
    packet = packets.get(row['item_id'])
    if packet is None:
        return errors + ['unknown_item_id']
    if row['item_type'] != packet['item_type']:
        errors.append('wrong_item_type')
    facts = row['facts']
    field_list = contract['numeric_fact_fields'] if row['item_type']=='numeric_claim' else contract['relation_fact_fields']
    for key in field_list:
        if key not in facts:
            errors.append('missing_fact:' + key)
    if errors:
        return errors
    for key in ['doc_id','revision_id','event_id','event_family_id','source_claim_id']:
        if facts[key] != packet[key]:
            errors.append('packet_identity_mismatch:' + key)
    for key in ['published_at','published_date','time_precision']:
        if facts[key] != packet['publication'][key]:
            errors.append('publication_mismatch:' + key)
    if facts['published_at'] is not None:
        errors.append('invented_exact_publication_time')
    if set(row['evidence_refs']) != set(packet['evidence_refs']):
        errors.append('evidence_reference_set_changed')
    for key in contract['provenance_required_fields']:
        if key not in row['provenance']:
            errors.append('missing_provenance:' + key)
    if row['provenance'].get('doc_sha256') != packet['source_sha256']:
        errors.append('source_hash_mismatch')
    if row['provenance'].get('source_record_ref') != packet['source_record_ref']:
        errors.append('source_record_ref_mismatch')
    if row['provenance'].get('availability_dependency_refs') != packet['scope_dependency_refs']:
        errors.append('scope_dependency_dropped_or_added')
    if row['provenance'].get('offset_basis') != contract['provenance_rules']['offset_basis']:
        errors.append('offset_basis_not_original_unicode_cell')
    flags = row['exposure_log'].get('flags', []) if isinstance(row['exposure_log'],dict) else row['exposure_log']
    if not all(flag in flags for flag in contract['exposure_flags_required']):
        errors.append('missing_exposure_flags')
    for key,value in facts.items():
        if value is None and 'facts.'+key not in row['field_missing_reasons']:
            errors.append('null_without_reason:facts.'+key)
    if row['item_type']=='numeric_claim':
        raw = packet['raw']['value_cell']
        start,end = facts['value_span_start'],facts['value_span_end']
        if not isinstance(start,int) or not isinstance(end,int) or start < 0 or end < start or raw[start:end] != facts['value_raw']:
            errors.append('source_span_roundtrip_failed')
        try:
            signed = Decimal(facts['value_raw'].replace('$','').replace(',','').replace('(','-').replace(')',''))
            norm = -signed if facts['sign_policy']=='outflow_to_positive' else signed
            if norm != Decimal(facts['numeric_value']):
                errors.append('source_sign_or_value_mismatch')
            if not norm.is_finite() or not Decimal(facts['scale']).is_finite():
                errors.append('nonfinite_number')
            if norm*Decimal(facts['scale']) != Decimal(facts['numeric_value_base_units']):
                errors.append('scale_conversion_mismatch')
        except (InvalidOperation,TypeError):
            errors.append('invalid_decimal')
        if facts['period_kind']=='instant':
            if any(facts[key] is not None for key in ['period_start','period_end','duration_days']):
                errors.append('instant_is_not_duration')
            if not facts['as_of_date']:
                errors.append('instant_missing_asof')
        elif facts['period_kind']=='duration':
            if facts['as_of_date'] is not None:
                errors.append('flow_has_asof')
            try:
                n=(date.fromisoformat(facts['period_end'])-date.fromisoformat(facts['period_start'])).days+1
                if n <= 0 or n != facts['duration_days']:
                    errors.append('period_length_mismatch')
            except (TypeError,ValueError):
                errors.append('invalid_period_date')
        else:
            errors.append('unknown_period_kind')
        if facts['scope_id']=='US-MSFT-CONSOLIDATED' and facts['scope_status_as_of']!='unresolved_retrospective_dependency':
            errors.append('historical_scope_support_overclaimed')
    else:
        expected = {'relation_type':'reports_segment','subject_role':'reporting_company',
            'object_role':'reported_segment','direction':'subject_to_object','subject_entity_id':'US-MSFT'}
        for key,val in expected.items():
            if facts[key] != val:
                errors.append('reporting_relation_semantics:' + key)
        if facts['scope_id'] != facts['object_entity_id']:
            errors.append('reporting_scope_mismatch')
        if any(facts[key] is not None for key in ['effective_period_start','effective_period_end','valid_from','valid_to']):
            errors.append('reporting_period_is_not_business_validity')
        if row['provenance'].get('source_effective_period') != {'start':facts['reference_period_start'],'end':facts['reference_period_end']}:
            errors.append('source_effective_period_history_missing')
    return errors

def validate_assessment(row, annotations, contract):
    errors = ['missing:'+key for key in contract['assessment_file_required_top_level'] if key not in row]
    if errors:
        return errors
    if row['annotation_id'] not in annotations:
        errors.append('unknown_annotation_id')
    if row['annotator_kind']!='agent':
        errors.append('assessment_must_be_agent')
    if row['purpose']!='historical_comparison' or row['as_of_precision']!='date':
        errors.append('assessment_purpose_or_precision')
    if row['review_readiness']!='needs_review':
        errors.append('historical_comparison_missing_prior')
    question_ids = {q['question_id'] for q in row['questions']}
    if question_ids != {f'MQ{i:02d}' for i in range(1,9)}:
        errors.append('question_coverage_mismatch')
    for q in row['questions']:
        if not q.get('reason'):
            errors.append('assessment_missing_reason:' + q['question_id'])
        if q['question_id'] in {'MQ01','MQ02','MQ03','MQ04','MQ05','MQ07'} and q['response'] not in {'unknown','not_assessed','not_applicable'}:
            errors.append('unsupported_materiality_or_prior_answer:' + q['question_id'])
    flags = row['exposure_log'].get('flags',[]) if isinstance(row['exposure_log'],dict) else row['exposure_log']
    if not all(flag in flags for flag in contract['exposure_flags_required']):
        errors.append('assessment_exposure_omitted')
    return errors
