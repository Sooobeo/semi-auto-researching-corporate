"""AGENT-A's independent raw-packet annotation, without source prose or answer keys.

Each run writes new files exclusively. Practice and main are separate agent runs;
they are not independent human samples. Main needs explicit root authorization.
"""
from __future__ import annotations

import argparse
import calendar
import copy
import csv
import hashlib
import json
import re
import time
from collections import Counter
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path

from p04_annotation_validation_v1_2 import validate_annotation, validate_assessment

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'artifacts/us_equity/p3'
DEST = BASE / 'reviewer_a'
AUTHOR = 'AGENT-A'
INPUT_NAMES = [
    'annotation_guide_v1.md', 'annotation_output_contract.json',
    'annotation_reference.json', 'source_packets.jsonl', 'evidence_index.jsonl',
    'practice_selection.json', 'annotation_assignments.csv',
    'contract_freeze_manifest.json', 'stage_reviews/stage_02_final.json',
    'annotation_guide_v1_1.md', 'annotation_output_contract_v1_1.json',
    'annotation_clarifications_v1_1.json', 'annotation_freeze_v1_1.json',
    'annotation_guide_v1_2.md', 'annotation_output_contract_v1_2.json',
    'annotation_freeze_v1_2.json',
]
CODE_INPUTS = ['scripts/p04_common.py', 'scripts/p04_annotation_validation.py',
               'scripts/p04_annotation_validation_v1_2.py',
               'scripts/p04_annotate_a.py']
NUMBER_TOKEN = re.compile(r'\(?\$?-?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?\)?')


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(name):
    return json.loads((BASE / name).read_text(encoding='utf-8'))


def read_lines(name):
    return [json.loads(line) for line in (BASE / name).read_text(encoding='utf-8').splitlines()
            if line.strip()]


def write_new(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8', newline='') as stream:
        stream.write(data)


def write_json(path, data):
    write_new(path, json.dumps(data, ensure_ascii=False, indent=2) + '\n')


def compact_whitespace(text):
    return ' '.join(text.split())


def parse_period(raw, reference):
    """Fiscal period values come from raw header text, never an item/document ID."""
    header = compact_whitespace(raw['period_header'])
    year_header = compact_whitespace(raw['year_header'])
    years = re.findall(r'(?<!\d)(\d{4})(?!\d)', year_header)
    if len(years) != 1:
        raise ValueError('Expected one source year header')
    year = int(years[0])
    month_day = re.search(r'([A-Za-z]+)\s+(\d{1,2}),', header)
    if not month_day:
        raise ValueError('Missing source period month/day')
    month = list(calendar.month_name).index(month_day.group(1))
    end = date(year, month, int(month_day.group(2)))
    fiscal = reference['fiscal_calendar']
    if (month, end.day) != (fiscal['year_end_month'], fiscal['year_end_day']):
        raise ValueError('Source header outside selected fiscal-calendar scope')
    if header.startswith('Three Months Ended '):
        start, quarter = date(year, month - 2, 1), 4
    elif header.startswith('Twelve Months Ended '):
        start, quarter = date(year - 1, month + 1, 1), None
    else:
        if header != year_header:
            raise ValueError('Unsupported duration or conflicting instant headers')
        return dict(period_start=None, period_end=None, as_of_date=end.isoformat(),
                    period_kind='instant', duration_days=None, fiscal_year=year,
                    fiscal_quarter=None)
    return dict(period_start=start.isoformat(), period_end=end.isoformat(), as_of_date=None,
                period_kind='duration', duration_days=(end - start).days + 1,
                fiscal_year=year, fiscal_quarter=quarter)


def parse_number(cell):
    found = list(NUMBER_TOKEN.finditer(cell))
    if len(found) != 1:
        raise ValueError('Expected exactly one numeric token in source cell')
    token = found[0]
    if cell[:token.start()].strip() or cell[token.end():].strip():
        raise ValueError('Unparsed source value-cell material')
    raw = token.group(0)
    if raw.startswith('(') != raw.endswith(')'):
        raise ValueError('Unbalanced source accounting parentheses')
    signed = Decimal(raw.replace('$', '').replace(',', '').replace('(', '-').replace(')', ''))
    if not signed.is_finite():
        raise ValueError('Nonfinite source value')
    return raw, signed, token.start(), token.end()


def check_evidence(packet, evidence):
    """Check packet/index correspondence; do not assert a fresh DOM audit."""
    selected = [evidence[key] for key in packet['evidence_refs']]
    for row in selected:
        for field, expected in [('doc_id', packet['doc_id']), ('revision_id', packet['revision_id']),
                                ('source_sha256', packet['source_sha256'])]:
            if row[field] != expected:
                raise ValueError('Evidence identity mismatch: ' + field)
        if row['offset_unit'] != 'unicode_code_point' or row['offset_mapping'] != 'identity':
            raise ValueError('Unsupported evidence offsets')
    raw_to_kind = {'row_label': 'row_label', 'period_header': 'period_header',
                  'year_header': 'year_header', 'unit_header': 'unit'}
    for raw_key, kind in raw_to_kind.items():
        matching = [row for row in selected if row['evidence_kind'] == kind]
        # Balance date uses the same source header as both period and year.
        if not matching and raw_key == 'period_header' and packet['raw']['period_header'] == packet['raw']['year_header']:
            matching = [row for row in selected if row['evidence_kind'] == 'year_header']
        if not any(compact_whitespace(row['selected_text']) == compact_whitespace(packet['raw'][raw_key])
                   for row in matching):
            raise ValueError('Source header/label reference mismatch: ' + raw_key)
    return selected


def null_reasons(facts):
    reasons = {}
    for field, value in facts.items():
        if value is not None:
            continue
        if field == 'published_at':
            reason = 'Exact release time is unavailable; only the source publication date is provided.'
        elif field in {'effective_period_start', 'effective_period_end', 'valid_from', 'valid_to'}:
            reason = 'Selected reporting table does not establish actual business validity or effective dates.'
        elif field == 'as_of_date':
            reason = 'Not applicable to a duration flow; period_start and period_end are used.'
        elif field in {'period_start', 'period_end', 'duration_days'}:
            reason = 'Not applicable to an instant balance; as_of_date is used.'
        elif field == 'fiscal_quarter':
            reason = 'Not applicable to an annual duration or an instant balance in this selection.'
        else:
            raise ValueError('Unexplained null: ' + field)
        reasons['facts.' + field] = reason
    return reasons


def annotate(packet, phase, ordinal, reference, clarifications, contract, evidence, exposure, previously_annotated=False):
    started = utc_now()
    raw = packet['raw']
    refs = check_evidence(packet, evidence)
    period = parse_period(raw, reference)
    segment = raw['scope_label'] in reference['segment_label_to_entity_id']
    if not segment and raw['scope_label'] != 'company financial statement total':
        raise ValueError('Unregistered raw scope label')
    scope = (reference['segment_label_to_entity_id'][raw['scope_label']] if segment
             else reference['company_scope_id'])
    facts = {key: packet[key] for key in ['source_claim_id', 'doc_id', 'revision_id', 'event_id', 'event_family_id']}
    facts.update(company_id=reference['company_id'], scope_id=scope, modality='actual_reported',
                 **{key: packet['publication'][key] for key in ['published_date', 'published_at', 'time_precision']})
    facts.update(evidence_status=clarifications['evidence_status'][packet['item_type']],
                 speaker=clarifications['speaker'],
                 scope_status_as_of=clarifications['scope_status_as_of']['segment' if segment else 'corporate'])
    uncertainty = ['date_only_release_time', 'selected_table_packet_only_no_fresh_DOM_or_whole_body_audit',
                   'shared_curator_metadata_not_independent_end_to_end_extraction',
                   'guide_contains_post_cutoff_context']
    if segment:
        uncertainty.append('segment_presentation_comparability_requires_separate_review')
    else:
        uncertainty.append('historical_consolidated_scope_unresolved_retrospective_dependency')
    provenance = dict(doc_sha256=packet['source_sha256'], source_record_ref=packet['source_record_ref'],
                      offset_basis=contract['provenance_rules']['offset_basis'],
                      availability_dependency_refs=packet['scope_dependency_refs'],
                      source_effective_period=None,
                      source_presentation_id=packet['source_presentation_id'],
                      evidence_location_audit='packet/index correspondence checked; original DOM not reopened')
    if packet['item_type'] == 'numeric_claim':
        metric = reference['segment_table_metric_id'] if segment else reference['metric_label_to_id'][raw['metric_label']]
        if segment and raw['metric_label'] != 'segment revenue':
            raise ValueError('Unrecognized selected segment metric')
        value_raw, signed, start, end = parse_number(raw['value_cell'])
        matching = [row for row in refs if row['evidence_kind'] == 'numeric_value']
        if len(matching) != 1 or (matching[0]['start'], matching[0]['end'], matching[0]['selected_text']) != (start, end, value_raw):
            raise ValueError('Independently parsed numeric span differs from supplied evidence index')
        if compact_whitespace(raw['unit_header']).casefold() != 'millions':
            raise ValueError('Unsupported source scale')
        scale = Decimal('1000000')
        capex = metric == 'positive_cash_capex'
        if capex and signed >= 0:
            raise ValueError('Cash PP&E addition is not an outflow in the selected raw cell')
        normalized = -signed if capex else signed
        definition = clarifications['definition_version']['corporate']
        if segment:
            # This release identifier supplies presentation version only, never reporting dates.
            match = re.fullmatch(r'US-MSFT-FY(\d{4})-Q4-RELEASE', packet['source_presentation_id'])
            if match is None:
                raise ValueError('Unrecognized source presentation identifier')
            definition = clarifications['definition_version']['segment'].format(source_release_fiscal_year=match.group(1))
        balance = metric in {'total_assets', 'cash_and_equivalents'}
        if balance != (period['period_kind'] == 'instant'):
            raise ValueError('Metric and source header disagree on balance/flow')
        facts.update(period)
        facts.update(metric_id=metric, definition_version=definition, value_raw=value_raw,
                     numeric_value=str(normalized), scale=str(scale), numeric_value_base_units=str(normalized * scale),
                     currency=clarifications['currency'], canonical_unit=clarifications['canonical_unit'],
                     sign_policy=clarifications['sign_policy']['cash_ppe_additions' if capex else 'default'],
                     balance_or_flow='balance' if balance else 'flow', value_span_start=start, value_span_end=end,
                     accounting_basis=clarifications['accounting_basis'],
                     period_start_derivation=clarifications['period_start_derivation'][period['period_kind']])
        uncertainty.append('GAAP_and_USD_from_curator_selected_financial_statement_context_not_numeric_cell')
        provenance['accounting_and_currency_basis'] = clarifications['source_metadata_basis']
        provenance['accounting_basis_limit'] = clarifications['accounting_basis_limit']
        provenance['source_effective_period_null_reason'] = 'Not applicable to a numeric claim; no relation input period.'
    elif packet['item_type'] == 'reporting_relation':
        if not segment or period['period_kind'] != 'duration':
            raise ValueError('Reporting relation lacks segment/duration evidence')
        facts.update(source_relation_id=packet['source_relation_id'], relation_type=clarifications['relation_type'],
                     subject_entity_id=reference['company_id'], object_entity_id=scope,
                     subject_role=clarifications['subject_role'], object_role=clarifications['object_role'],
                     direction=clarifications['direction'], negation=False, conditions=[],
                     reference_period_start=period['period_start'], reference_period_end=period['period_end'],
                     effective_period_start=None, effective_period_end=None, valid_from=None, valid_to=None)
        provenance['source_effective_period'] = {'start': period['period_start'], 'end': period['period_end']}
        provenance['source_effective_period_basis'] = 'Original input reporting-period history retained through packet headers; not actual business validity.'
        uncertainty.extend(['business_effective_and_validity_dates_unknown',
                            'negation_false_and_conditions_empty_limited_to_selected_positive_table_membership'])
    else:
        raise ValueError('Unsupported item type')
    record = dict(annotation_id=f'{phase}-{AUTHOR}-v1_2-{ordinal:03d}', annotator_id=AUTHOR, annotator_kind='agent',
                  method='agent_authored_deterministic_annotation', item_id=packet['item_id'],
                  item_type=packet['item_type'], guide_version=contract['guide_version'], registry_version='us-p2-0.1.0',
                  facts=facts, evidence_refs=list(packet['evidence_refs']), uncertainty_reasons=uncertainty,
                  started_at=started, completed_at=utc_now(), status='agent_draft', exposure_log=copy.deepcopy(exposure),
                  provenance=provenance, field_missing_reasons=null_reasons(facts))
    if previously_annotated:
        record['exposure_log']['flags'].append('item_previously_annotated_in_practice')
    return record


def assess(annotation, contract):
    facts = annotation['facts']
    corporate = facts['scope_status_as_of'] == 'unresolved_retrospective_dependency'
    support = ('Packet values/labels, period headers, hashes and location references support checking the selected source assertion. ')
    support += ('Historical consolidated scope remains unresolved because the supplemental reference is not established at the release cutoff; this missing scope support makes the location/period/scope link insufficient as a whole.'
                if corporate else 'The selected table directly names this reported segment and links it to the stated period and source location; this narrowly defined link is sufficient. Historical presentation comparability remains unreviewed and is separate from this question.')
    support += ' This does not assert a fresh DOM audit, whole-document completeness or externally verified performance.'
    questions = [dict(question_id=f'MQ{i:02d}', response='unknown',
                      reason='Minimal selected table facts do not provide the prior business assumptions, forecasts and financial context needed for this materiality judgment.')
                 for i in range(1, 6)]
    questions.extend([
        dict(question_id='MQ06', response='insufficient' if corporate else 'sufficient', reason=support),
        dict(question_id='MQ07', response='unknown', reason='prior_not_provided; no explicitly matched comparison claim and definition/scope conditions were supplied for this independent assessment.'),
        dict(question_id='MQ08', response='investigate', reason='Obtain an as-of-available prior claim and verify period, definition and scope before historical comparison; retain this selected table assertion as an agent draft.'),
    ])
    return dict(assessment_id=annotation['annotation_id'] + '-assessment', annotation_id=annotation['annotation_id'],
                item_id=annotation['item_id'], annotator_id=AUTHOR, annotator_kind='agent', guide_version=contract['guide_version'],
                purpose='historical_comparison', as_of_date=facts['published_date'], as_of_precision='date',
                questions=questions, review_readiness='needs_review',
                reasons=['prior_not_provided', 'historical_scope_or_definition_comparability_not_resolved',
                         'retrospective_cutoff_simulation_with_guide_post_cutoff_exposure', 'agent_judgment_not_human_materiality_gold'],
                created_at=utc_now(), exposure_log=copy.deepcopy(annotation['exposure_log']))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase', choices=['practice', 'main'], required=True)
    parser.add_argument('--authorization-reference', help='Root follow-up authorization; required for main.')
    args = parser.parse_args()
    if args.phase == 'main' and not args.authorization_reference:
        parser.error('main is gated until root explicitly authorizes it')
    started, timer = utc_now(), time.monotonic()
    input_paths = [BASE / name for name in INPUT_NAMES] + [ROOT / name for name in CODE_INPUTS]
    before_hashes = {str(path.relative_to(ROOT)).replace('\\', '/'): sha(path) for path in input_paths}
    contract = read_json('annotation_output_contract_v1_2.json')
    reference = read_json('annotation_reference.json')
    clarification = read_json('annotation_clarifications_v1_1.json')
    freeze = read_json('annotation_freeze_v1_2.json')
    for entry in freeze['files']:
        if sha(BASE / entry['path']) != entry['sha256']:
            raise ValueError('Frozen annotation input hash mismatch: ' + entry['path'])
    if read_json('stage_reviews/stage_02_final.json')['gate'] != 'passed_with_explicit_limitations':
        raise ValueError('Stage 2 gate has not passed')
    if contract['clarification_ref'] != 'annotation_clarifications_v1_1.json':
        raise ValueError('Unexpected clarification reference')
    packets = {row['item_id']: row for row in read_lines('source_packets.jsonl')}
    evidence = {row['evidence_id']: row for row in read_lines('evidence_index.jsonl')}
    practice = read_json('practice_selection.json')['item_ids']
    with (BASE / 'annotation_assignments.csv').open(encoding='utf-8-sig', newline='') as stream:
        assignments = [row for row in csv.DictReader(stream) if row['phase'] == args.phase and row['annotator_id'] == AUTHOR]
    selected = [row['item_id'] for row in assignments]
    if len(selected) != len(set(selected)) or (args.phase == 'practice' and selected != practice):
        raise ValueError('Assignment selection is inconsistent')
    exposure = {'flags': list(contract['exposure_flags_required']) + ['shared_curator_currency_accounting_and_enum_context',
                'cross_release_development_packets_available', 'minimal_nonexpressive_source_packets_only',
                'guide_contains_prior_practice_response_vocabulary_examples',
                'source_prose_and_reserved_document_not_opened', 'other_reviewer_outputs_not_opened'],
                'inputs': list(before_hashes)}
    practice_exposed_ids = set()
    previous_by_item = {}
    prior_paths = [DEST / 'practice_annotations.jsonl']
    if args.phase == 'main':
        prior_paths.append(DEST / 'practice_annotations_v1_2.jsonl')
    for own_practice in prior_paths:
        # Read own previous practice to preserve exposure/revision history, never another reviewer.
        prior = [json.loads(line) for line in own_practice.read_text(encoding='utf-8').splitlines() if line.strip()]
        exposure['inputs'].append(str(own_practice.relative_to(ROOT)).replace('\\', '/'))
        practice_exposed_ids.update(row['item_id'] for row in prior)
        previous_by_item.update({row['item_id']: row for row in prior})
        input_paths.append(own_practice)
        before_hashes[str(own_practice.relative_to(ROOT)).replace('\\', '/')] = sha(own_practice)
    suffix = '_v1_2' if args.phase == 'practice' else ''
    outputs = {kind: DEST / f'{args.phase}_{kind}{suffix}.{ext}' for kind, ext in
               [('annotations', 'jsonl'), ('assessments', 'jsonl'), ('execution_log', 'json'), ('selfreview', 'json')]}
    if any(path.exists() for path in outputs.values()):
        raise FileExistsError('Refusing to overwrite prior AGENT-A outputs')
    annotations = [annotate(packets[item], args.phase, n, reference, clarification, contract, evidence, exposure,
                            previously_annotated=item in practice_exposed_ids)
                   for n, item in enumerate(selected, 1)]
    if args.phase == 'practice':
        for row in annotations:
            previous = previous_by_item[row['item_id']]
            if row['facts'] != previous['facts']:
                raise ValueError('Unexpected fact drift during assessment-vocabulary revision')
            row['annotation_revision'] = dict(previous_annotation_id=previous['annotation_id'],
                                              reason='guide_1_2_response_vocabulary_and_MQ06_question_scope_clarification',
                                              kind='agent_reannotation', facts_recomputed_from_raw_and_unchanged=True)
    assessments = [assess(row, contract) for row in annotations]
    if args.phase == 'practice':
        for row in assessments:
            row['assessment_revision'] = dict(previous_assessment_id=previous_by_item[row['item_id']]['annotation_id'] + '-assessment',
                                              reason='MQ06 single allowed response; partial support retained in reason',
                                              kind='agent_reassessment')
    annotation_map = {row['annotation_id']: row for row in annotations}
    annotation_errors = {row['annotation_id']: validate_annotation(row, packets, contract) for row in annotations}
    assessment_errors = {row['assessment_id']: validate_assessment(row, annotation_map, contract) for row in assessments}
    annotation_errors = {key: value for key, value in annotation_errors.items() if value}
    assessment_errors = {key: value for key, value in assessment_errors.items() if value}
    if annotation_errors or assessment_errors:
        failure = dict(at=utc_now(), annotation_errors=annotation_errors, assessment_errors=assessment_errors)
        write_json(DEST / f'{args.phase}_failure_{time.time_ns()}.json', failure)
        raise ValueError('Validation failed; failure evidence preserved')
    after_hashes = {str(path.relative_to(ROOT)).replace('\\', '/'): sha(path) for path in input_paths}
    if before_hashes != after_hashes:
        raise ValueError('Inputs changed during annotation')
    numeric = [row for row in annotations if row['item_type'] == 'numeric_claim']
    relations = [row for row in annotations if row['item_type'] == 'reporting_relation']
    counts = dict(annotations=len(annotations), assessments=len(assessments), numeric_claims=len(numeric),
                  reporting_relations=len(relations), unique_items=len(set(selected)),
                  unique_source_claims=len({row['facts']['source_claim_id'] for row in annotations}),
                  unique_documents=len({row['facts']['doc_id'] for row in annotations}),
                  unique_events=len({row['facts']['event_id'] for row in annotations}),
                  unique_families=len({row['facts']['event_family_id'] for row in annotations}),
                  unique_relation_objects=len({row['facts']['object_entity_id'] for row in relations}), human_annotations=0,
                  source_DOM_reaudits=0, numeric_span_roundtrips_passed=len(numeric),
                  annotation_validation_passed=len(annotations), assessment_validation_passed=len(assessments),
                  question_responses=dict(Counter(question['response'] for row in assessments for question in row['questions'])))
    checks = dict(all_assigned_items_present=True, contract_validation_passed=True,
                  source_header_and_evidence_identity_checks_passed=True,
                  numeric_dates_derived_from_raw_headers_not_identifiers=True,
                  decimal_values_and_original_unicode_spans=True,
                  relation_reporting_period_not_business_validity=True,
                  all_null_facts_have_field_reasons=True, original_inputs_unchanged=True,
                  all_required_exposures_recorded=True, no_prose_or_reserved_content_read=True,
                  no_other_reviewer_or_normalized_answer_read=True,
                  practice_main_overlap_not_independent=True, no_human_gold_claim=True)
    limitations = ['No independent human annotations or full-document manual audit.',
                   'Published time remains date-only; same-day order is unknown.',
                   'Corporate historical scope has an unavailable retrospective dependency.',
                   'Segment presentation comparability and all prior-dependent materiality judgments remain unresolved.',
                   'Currency and GAAP are shared curator context for selected financial tables, not independent cell-level evidence.',
                   'Guide and cross-release packet exposure prevent claiming unexposed historical assessment.']
    selfreview = dict(reviewer=AUTHOR, phase=args.phase, checked_at=utc_now(), guide_version=contract['guide_version'],
                      gate='passed_with_explicit_limitations', counts=counts, checks=checks,
                      annotation_errors=annotation_errors, assessment_errors=assessment_errors, limitations=limitations,
                      improvement='v1.2 specifies allowed assessment responses; MQ06 now separates corporate missing scope support from sufficient selected segment reporting links. Facts independently recomputed unchanged; prior practice and code retained.',
                      next_phase_authorized=args.phase == 'main')
    for kind, values in [('annotations', annotations), ('assessments', assessments)]:
        write_new(outputs[kind], ''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in values))
    write_json(outputs['selfreview'], selfreview)
    execution = dict(annotator_id=AUTHOR, annotator_kind='agent', method=contract['method'], phase=args.phase,
                     started_at=started, completed_at=utc_now(), elapsed_seconds=time.monotonic() - timer,
                     time_interpretation='Machine execution only, not human annotation duration.',
                     model_name=None, model_version=None,
                     model_missing_reason='Exact runtime model identifier/version not exposed; not fabricated.',
                     contract_version=contract['contract_version'], guide_version=contract['guide_version'],
                     input_hashes_before=before_hashes, input_hashes_after=after_hashes,
                     output_hashes={str(path.relative_to(ROOT)).replace('\\', '/'): sha(path) for kind, path in outputs.items() if kind != 'execution_log'},
                     exposure_log=exposure, authorization_reference=args.authorization_reference,
                     counts=counts, status='completed_agent_draft')
    write_json(outputs['execution_log'], execution)
    print(json.dumps({'phase': args.phase, 'counts': counts, 'gate': selfreview['gate']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
