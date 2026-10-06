"""AGENT-B's independent, packet-only P04 development annotation.

No transformed answer files, other reviewers, private source prose, or network
are accessed. Inputs and immutable execution snapshots disclose assistance.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import sys
import time
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

from p04_common import OUT, ROOT, json_file, jsonl, now, rows, sha, write
from p04_annotation_validation_v1_2 import validate_annotation, validate_assessment

AUTHOR = 'AGENT-B'
DEST = OUT / 'reviewer_b'
READ_INPUTS = [
    'artifacts/us_equity/p3/annotation_guide_v1.md',
    'artifacts/us_equity/p3/annotation_output_contract.json',
    'artifacts/us_equity/p3/annotation_reference.json',
    'artifacts/us_equity/p3/source_packets.jsonl',
    'artifacts/us_equity/p3/evidence_index.jsonl',
    'artifacts/us_equity/p3/practice_selection.json',
    'artifacts/us_equity/p3/annotation_assignments.csv',
    'artifacts/us_equity/p3/contract_freeze_manifest.json',
    'artifacts/us_equity/p3/stage_reviews/stage_02_final.json',
    'scripts/p04_common.py',
    'scripts/p04_annotation_validation.py',
    'artifacts/us_equity/p3/annotation_guide_v1_1.md',
    'artifacts/us_equity/p3/annotation_output_contract_v1_1.json',
    'artifacts/us_equity/p3/annotation_clarifications_v1_1.json',
    'artifacts/us_equity/p3/annotation_freeze_v1_1.json',
    'artifacts/us_equity/p3/annotation_guide_v1_2.md',
    'artifacts/us_equity/p3/annotation_output_contract_v1_2.json',
    'artifacts/us_equity/p3/annotation_freeze_v1_2.json',
    'scripts/p04_annotation_validation_v1_2.py',
    'artifacts/us_equity/p3/reviewer_b/practice_annotations.jsonl',
    'artifacts/us_equity/p3/reviewer_b/practice_assessments.jsonl',
    'artifacts/us_equity/p3/reviewer_b/practice_execution.json',
    'artifacts/us_equity/p3/reviewer_b/practice_selfreview.json',
    'artifacts/us_equity/p3/reviewer_b/practice_script_snapshot.py',
    'scripts/p04_annotate_b.py',
]


def compact(text):
    return ' '.join(text.split())


def raw_year(raw):
    matches = re.findall(r'(?<!\d)(20\d\d)(?!\d)', raw['year_header'])
    if len(matches) != 1:
        raise ValueError('Exactly one fiscal year required in raw year header')
    return int(matches[0])


def parse_period(raw):
    """Read fiscal period from headers; identifiers never supply its year."""
    header = compact(raw['period_header'])
    year = raw_year(raw)
    if not re.search(r'June\s+30\s*,', header):
        raise ValueError('Unsupported or missing June 30 endpoint')
    end = date(year, 6, 30)
    if header.startswith('Three Months Ended'):
        start, quarter = date(year, 4, 1), 4
    elif header.startswith('Twelve Months Ended'):
        start, quarter = date(year - 1, 7, 1), None
    elif header.startswith('June 30,'):
        if raw_year({'year_header': header}) != year:
            raise ValueError('Instant and year headers disagree')
        return dict(period_start=None, period_end=None, as_of_date=end.isoformat(),
                    period_kind='instant', duration_days=None,
                    fiscal_year=year, fiscal_quarter=None)
    else:
        raise ValueError('Unsupported raw period header')
    return dict(period_start=start.isoformat(), period_end=end.isoformat(),
                as_of_date=None, period_kind='duration',
                duration_days=(end-start).days+1,
                fiscal_year=year, fiscal_quarter=quarter)


def parse_number(cell):
    """Trim outside whitespace only; Python indices are Unicode code points."""
    left = len(cell) - len(cell.lstrip())
    right = len(cell.rstrip())
    token = cell[left:right]
    if not re.fullmatch(r'\(?\$?-?\d{1,3}(?:,\d{3})*(?:\.\d+)?\)?|\(?\$?-?\d+(?:\.\d+)?\)?', token):
        raise ValueError('Unsupported number token')
    if token.startswith('(') != token.endswith(')'):
        raise ValueError('Unbalanced accounting parentheses')
    body = token.replace('$', '').replace(',', '')
    if body.startswith('('):
        number = -Decimal(body[1:-1])
    else:
        number = Decimal(body)
    if not number.is_finite():
        raise ValueError('Nonfinite source number')
    assert cell[left:right] == token
    return token, number, left, right


def decimal_text(number):
    return format(number, 'f')


def exposure(contract, phase, item_id, practice_ids):
    flags = list(contract['exposure_flags_required']) + [
        'shared_curator_currency_accounting_and_naming_metadata',
        'all_development_packets_available_during_code_authorship',
        'no_other_reviewer_answers_read',
        'no_private_source_or_reserved_content_read',
        'same_practice_items_previously_annotated_under_guide_1_1',
    ]
    if phase == 'main' and item_id in practice_ids:
        flags.append('same_item_previously_annotated_in_practice')
    return {'flags': flags, 'inputs': list(READ_INPUTS)}


def check_packet_evidence(packet, evidence):
    """Cross-check the packet's raw fragments against referenced evidence."""
    refs = [evidence[key] for key in packet['evidence_refs']]
    for evidence_row in refs:
        assert evidence_row['doc_id'] == packet['doc_id']
        assert evidence_row['revision_id'] == packet['revision_id']
        assert evidence_row['source_sha256'] == packet['source_sha256']
    raw = packet['raw']
    for key, kind in [('row_label', 'row_label'), ('year_header', 'year_header'),
                      ('unit_header', 'unit')]:
        assert any(e['evidence_kind'] == kind and e['selected_text'] == raw[key]
                   for e in refs), (key, packet['item_id'])
    assert any(e['evidence_kind'] in {'period_header', 'year_header'} and
               e['selected_text'] == raw['period_header'] for e in refs)
    if packet['item_type'] == 'numeric_claim':
        token, _, start, end = parse_number(raw['value_cell'])
        assert any(e['evidence_kind'] == 'numeric_value' and
                   (e['selected_text'], e['start'], e['end']) == (token,start,end)
                   for e in refs), 'Independently computed numeric span mismatch'


def make_annotation(packet, phase, reference, contract, clarification, practice_ids):
    started = now()
    raw = packet['raw']
    label = compact(raw['row_label'])
    segment_map = reference['segment_label_to_entity_id']
    is_segment = label in segment_map
    scope = segment_map[label] if is_segment else reference['company_scope_id']
    if is_segment:
        assert label == compact(raw['scope_label'])
        metric = reference['segment_table_metric_id']
    else:
        assert raw['scope_label'] == 'company financial statement total'
        metric = reference['metric_label_to_id'][label]
        assert label == compact(raw['metric_label'])
    period = parse_period(raw)
    common = {key: packet[key] for key in
              ['source_claim_id','doc_id','revision_id','event_id','event_family_id']}
    common.update(company_id=reference['company_id'], scope_id=scope,
                  modality='actual_reported',
                  **{k:packet['publication'][k] for k in
                     ['published_date','published_at','time_precision']},
                  speaker=clarification['speaker'],
                  scope_status_as_of=clarification['scope_status_as_of'][
                      'segment' if is_segment else 'corporate'],
                  evidence_status=clarification['evidence_status'][packet['item_type']])
    uncertainty = [
        'Exact publication time unavailable; observed time is not publication time.',
        'Evidence coordinate metadata was cross-checked to packets; original HTML was not reopened.',
        'Shared guide contains post-cutoff context; historical cutoff is retrospective simulation.',
    ]
    if is_segment:
        uncertainty.append('Selected-table segment membership is supported; definition comparability across source presentations remains unverified.')
    else:
        uncertainty.append('Consolidated scope identifier retained; supporting annual-reference dependency is unavailable at historical release cutoff.')
    if packet['item_type'] == 'numeric_claim':
        token, signed, left, right = parse_number(raw['value_cell'])
        assert compact(raw['unit_header']).lower() == 'millions'
        scale = Decimal('1000000')
        capex = metric == 'positive_cash_capex'
        normalized = -signed if capex else signed
        if capex and normalized < 0:
            raise ValueError('Cash capex outlay is unexpectedly negative after sign inversion')
        if is_segment:
            # Presentation identity alone may supply the release definition tag.
            # Fiscal year and period values above always come from raw headers.
            release = re.fullmatch(r'US-MSFT-FY(\d{4})-Q4-RELEASE',
                                   packet['source_presentation_id'])
            if release is None:
                raise ValueError('Unrecognized source presentation metadata')
            definition = clarification['definition_version']['segment'].format(
                source_release_fiscal_year=release.group(1))
        else:
            definition = clarification['definition_version']['corporate']
        balance = metric in {'total_assets', 'cash_and_equivalents'}
        assert balance == (period['period_kind'] == 'instant')
        common.update(metric_id=metric, definition_version=definition,
                      value_raw=token, numeric_value=decimal_text(normalized),
                      scale=decimal_text(scale), numeric_value_base_units=decimal_text(normalized*scale),
                      currency=clarification['currency'], canonical_unit=clarification['canonical_unit'],
                      sign_policy=clarification['sign_policy']['cash_ppe_additions' if capex else 'default'],
                      **period, balance_or_flow='balance' if balance else 'flow',
                      value_span_start=left, value_span_end=right,
                      accounting_basis=clarification['accounting_basis'],
                      period_start_derivation=clarification['period_start_derivation'][period['period_kind']])
        source_effective = None
        uncertainty.append('USD and GAAP are curator-provided selected-financial-table context; company accounting-policy prose was not audited.')
        if capex:
            uncertainty.append('Cash PP&E additions only; noncash additions, finance leases and total investing cash flow are not covered.')
    else:
        assert is_segment and period['period_kind'] == 'duration'
        common.update(source_relation_id=packet['source_relation_id'],
                      relation_type=clarification['relation_type'],
                      subject_entity_id=reference['company_id'], object_entity_id=scope,
                      subject_role=clarification['subject_role'], object_role=clarification['object_role'],
                      direction=clarification['direction'], negation=False, conditions=[],
                      reference_period_start=period['period_start'], reference_period_end=period['period_end'],
                      effective_period_start=None, effective_period_end=None, valid_from=None, valid_to=None)
        source_effective = {'start':period['period_start'], 'end':period['period_end']}
        uncertainty.append('No negation or conditions are expressed in the selected table membership; whole-document negation and conditions were not audited.')
        uncertainty.append('Reference reporting period does not establish actual business effective period or historical validity.')
    reasons = {}
    for key, value in common.items():
        if value is not None:
            continue
        if key == 'published_at':
            reason = 'unknown: source provides date precision only'
        elif key in {'period_start','period_end','duration_days'}:
            reason = 'not_applicable: instant balance has no duration interval'
        elif key == 'as_of_date':
            reason = 'not_applicable: flow has a reporting duration'
        elif key == 'fiscal_quarter':
            reason = 'not_applicable: annual flow or fiscal-year-end balance is not a quarter duration'
        else:
            reason = 'unknown: selected reporting table does not establish business effective or validity dates'
        reasons['facts.' + key] = reason
    if source_effective is None:
        reasons['provenance.source_effective_period'] = 'not_applicable: numeric fact; reporting interval is represented in facts'
    return {
        'annotation_id': f'{AUTHOR}-{phase}-{contract["guide_version"]}-{packet["item_id"]}',
        'annotator_id':AUTHOR, 'annotator_kind':'agent',
        'method':'agent_authored_deterministic_annotation',
        'item_id':packet['item_id'], 'item_type':packet['item_type'],
        'guide_version':contract['guide_version'], 'registry_version':'us-p2-0.1.0',
        'facts':common, 'evidence_refs':list(packet['evidence_refs']),
        'uncertainty_reasons':uncertainty, 'started_at':started, 'completed_at':now(),
        'status':'agent_draft',
        'exposure_log':exposure(contract,phase,packet['item_id'],practice_ids),
        'provenance':{'doc_sha256':packet['source_sha256'],
                      'source_record_ref':packet['source_record_ref'],
                      'offset_basis':contract['provenance_rules']['offset_basis'],
                      'availability_dependency_refs':list(packet['scope_dependency_refs']),
                      'source_effective_period':source_effective},
        'field_missing_reasons':reasons,
    }


def make_assessment(annotation):
    facts = annotation['facts']
    corporate = facts['scope_status_as_of'] == 'unresolved_retrospective_dependency'
    questions = [dict(question_id=f'MQ{i:02d}', response='unknown',
                      reason='Minimal selected fact lacks prior business assumptions, outlook and financial decision context; missing evidence is not low importance.')
                 for i in range(1,6)]
    questions.append(dict(question_id='MQ06', response='insufficient' if corporate else 'sufficient', reason=(
        'Packet coordinates, value and period permit a narrow fact check; historical consolidated scope remains unresolved because the supplement is a retrospective dependency.'
        if corporate else
        'Selected table label, evidence coordinates and reporting period sufficiently connect the fact to its reported segment scope. This narrow sufficiency excludes whole-document completeness, external truth and historical cross-presentation comparability.')))
    questions.append(dict(question_id='MQ07', response='unknown',
                          reason='prior_not_provided: no authorized prior comparison object and matched definition conditions are available.'))
    questions.append(dict(question_id='MQ08', response='investigate',
                          reason='Obtain a contemporaneously available scope/definition basis and explicit prior comparison; defer historical materiality judgment until then.'))
    return {'assessment_id':annotation['annotation_id']+'-assessment',
            'annotation_id':annotation['annotation_id'], 'item_id':annotation['item_id'],
            'annotator_id':AUTHOR, 'annotator_kind':'agent', 'guide_version':annotation['guide_version'],
            'purpose':'historical_comparison', 'as_of_date':facts['published_date'],
            'as_of_precision':'date', 'questions':questions, 'review_readiness':'needs_review',
            'reasons':['prior_not_provided','source_presentation_comparability_unverified',
                       'historical_scope_unresolved' if corporate else 'selected_table_scope_only',
                       'retrospective_cutoff_simulation_not_blind_as_of'],
            'created_at':now(), 'exposure_log':copy.deepcopy(annotation['exposure_log'])}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--phase', required=True, choices=['practice','main'])
    args = parser.parse_args()
    started, clock_start = now(), time.perf_counter()
    phase = args.phase
    if phase == 'main':
        # These are this author's preserved practice inputs only. The other
        # reviewer's outputs and implementation remain outside the read scope.
        READ_INPUTS.extend('artifacts/us_equity/p3/reviewer_b/' + name for name in [
            'practice_annotations_v1_2.jsonl', 'practice_assessments_v1_2.jsonl',
            'practice_execution_v1_2.json', 'practice_selfreview_v1_2.json',
            'practice_script_snapshot_v1_2.py', 'practice_postcheck_v1_2.json'])
    suffix = '_v1_2' if phase == 'practice' else ''
    output_names = [phase+'_annotations'+suffix+'.jsonl', phase+'_assessments'+suffix+'.jsonl',
                    phase+'_execution'+suffix+'.json', phase+'_selfreview'+suffix+'.json']
    DEST.mkdir(parents=True, exist_ok=True)
    if any((DEST/name).exists() for name in output_names):
        raise FileExistsError('Immutable output already exists; do not rerun over originals')
    input_hashes = {path:sha(ROOT/path) for path in READ_INPUTS}
    contract = json.loads((OUT/'annotation_output_contract_v1_2.json').read_text(encoding='utf-8'))
    clarification = json.loads((OUT/'annotation_clarifications_v1_1.json').read_text(encoding='utf-8'))
    reference = json.loads((OUT/'annotation_reference.json').read_text(encoding='utf-8'))
    freeze = json.loads((OUT/'annotation_freeze_v1_2.json').read_text(encoding='utf-8'))
    stage2 = json.loads((OUT/'stage_reviews/stage_02_final.json').read_text(encoding='utf-8'))
    assert stage2['gate'] == 'passed_with_explicit_limitations'
    assert contract['guide_version'] == freeze['guide_version'] == 'us-p3-guide-1.2'
    assert contract['clarification_ref'] == 'annotation_clarifications_v1_1.json'
    freeze_checks = {item['path']:sha(OUT/item['path']) == item['sha256'] for item in freeze['files']}
    assert all(freeze_checks.values()), 'Frozen annotation input changed'
    # Read guide bytes as part of runtime provenance; its instructions were read by this agent.
    (OUT/'annotation_guide_v1_2.md').read_text(encoding='utf-8')
    all_packets = rows(OUT/'source_packets.jsonl')
    packets = {p['item_id']:p for p in all_packets}
    assert len(packets) == len(all_packets)
    evidence = {e['evidence_id']:e for e in rows(OUT/'evidence_index.jsonl')}
    practice = json.loads((OUT/'practice_selection.json').read_text(encoding='utf-8'))['item_ids']
    assigned = [a['item_id'] for a in rows(OUT/'annotation_assignments.csv')
                if a['annotator_id'] == AUTHOR and a['phase'] == phase]
    selected_ids = practice if phase == 'practice' else assigned
    assert len(assigned) == len(set(assigned)) and set(selected_ids) == set(assigned)
    selected = [packets[key] for key in selected_ids]
    annotations, assessments = [], []
    for packet in selected:
        check_packet_evidence(packet,evidence)
        annotation = make_annotation(packet,phase,reference,contract,clarification,set(practice))
        annotations.append(annotation)
        assessments.append(make_assessment(annotation))
    index = {a['annotation_id']:a for a in annotations}
    validation_errors = []
    for row in annotations:
        validation_errors.extend({'item_id':row['item_id'],'error':err}
                                 for err in validate_annotation(row,packets,contract))
    for row in assessments:
        validation_errors.extend({'item_id':row['item_id'],'error':err}
                                 for err in validate_assessment(row,index,contract))
    # Boundary checks target observed whitespace, accounting sign and leap-year risks.
    synthetic_checks = {
        'unicode_whitespace_preserves_offsets':parse_number('\r\n  \u00a0$123,456 \r\n  ') == ('$123,456',Decimal('123456'),5,13),
        'parentheses_preserve_signed_raw':parse_number('(13,873)')[1] == Decimal('-13873'),
        'annual_leap_year_is_366_days':parse_period({'period_header':'Twelve Months Ended\u00a0June 30,','year_header':'2024'})['duration_days'] == 366,
        'annual_nonleap_year_is_365_days':parse_period({'period_header':'Twelve Months Ended June 30,','year_header':'2025'})['duration_days'] == 365,
        'quarter_has_91_days':parse_period({'period_header':'Three Months Ended June 30,','year_header':'2024'})['duration_days'] == 91,
    }
    assert all(synthetic_checks.values()), 'Parser boundary check failed'
    previous_annotations = {a['item_id']:a for a in rows(DEST/'practice_annotations.jsonl')}
    original_practice_facts_unchanged = all(a['facts'] == previous_annotations[a['item_id']]['facts']
                                          for a in annotations if a['item_id'] in previous_annotations)
    assert original_practice_facts_unchanged, 'Guide response revision must not alter numeric facts'
    assert not {a['annotation_id'] for a in annotations}.intersection(
        a['annotation_id'] for a in previous_annotations.values()), 'New revision needs new annotation IDs'
    if phase == 'main':
        practice_v1_2 = {a['item_id']:a for a in rows(DEST/'practice_annotations_v1_2.jsonl')}
        assert all(a['facts'] == practice_v1_2[a['item_id']]['facts']
                   for a in annotations if a['item_id'] in practice_v1_2)
        for row in annotations + assessments:
            if row['item_id'] in practice_v1_2:
                row['exposure_log']['flags'].append('same_item_previously_annotated_under_guide_1_2')
    assert all(sha(ROOT/path) == digest for path,digest in input_hashes.items())
    script_snapshot = f'{phase}_script_snapshot{suffix}.py'
    write(DEST/script_snapshot, Path(__file__).read_text(encoding='utf-8'))
    # Even failed validation retains the authored draft and error report.
    jsonl(DEST/output_names[0],annotations)
    jsonl(DEST/output_names[1],assessments)
    numeric = [a for a in annotations if a['item_type']=='numeric_claim']
    relation = [a for a in annotations if a['item_type']=='reporting_relation']
    counts = {'assigned_items':len(selected),'annotations':len(annotations),'assessments':len(assessments),
              'numeric_annotations':len(numeric),'relation_annotations':len(relation),
              'unique_source_claims':len({a['facts']['source_claim_id'] for a in annotations}),
              'unique_events':len({a['facts']['event_id'] for a in annotations}),
              'unique_event_families':len({a['facts']['event_family_id'] for a in annotations}),
              'human_annotations':0,'human_gold':0,'numeric_span_roundtrips':len(numeric)}
    selfreview = {
        'annotator_id':AUTHOR,'phase':phase,'checked_at':now(),
        'gate':'passed_with_explicit_limitations' if not validation_errors else 'failed',
        'counts':counts,'validation_errors':validation_errors,
        'checks':{'contract_schema_valid':not validation_errors,'frozen_inputs_verified':all(freeze_checks.values()),
                  'raw_values_and_evidence_coordinates_crosschecked':True,
                  'fiscal_period_derived_from_raw_headers':True,'decimal_exact_arithmetic':True,
                  'null_fields_have_reasons':True,'source_identity_and_revision_preserved':True,
                  'private_sources_other_reviewers_and_network_not_used':True,
                  'same_item_main_practice_exposure_recorded':True,
                  'agent_and_retrospective_status_disclosed':True,
                  'original_practice_facts_unchanged':original_practice_facts_unchanged,
                  'prior_practice_outputs_and_snapshot_preserved':True,
                  'assessment_response_enums_checked':True},
        'parser_boundary_checks':synthetic_checks,'frozen_input_checks':freeze_checks,
        'improvements_before_execution':['Applied guide 1.2 assessment response vocabulary while preserving 1.1 original annotations and executable snapshot.',
                                         'MQ06 distinguishes sufficient selected-table segment linkage from insufficient historical corporate scope.',
                                         'MQ08 records investigate as the single action and deferral rationale in its reason.',
                                         'Retained raw-value algorithm and independently recalculated all facts.'],
        'unresolved':['Prior comparison object absent; historical importance remains unknown.',
                      'Consolidated scope supplement not historically available.',
                      'Full prose, visual source audit and separate GAAP policy audit not performed.',
                      'Segment definition comparability across presentations unresolved.',
                      'Release times have date precision only.',
                      'Relation reference periods do not establish business validity.'],
        'main_executed':phase=='main', 'human_independence_claim':False,
    }
    json_file(DEST/output_names[3],selfreview)
    json_file(DEST/output_names[2],{
        'annotator_id':AUTHOR,'annotator_kind':'agent','phase':phase,
        'method':contract['method'],'guide_version':contract['guide_version'],
        'started_at':started,'completed_at':now(),
        'elapsed_seconds':round(time.perf_counter()-clock_start,6),
        'elapsed_time_kind':'deterministic_script_execution_not_human_annotation_time',
        'model_version':None,'model_version_missing_reason':'Runtime model identifier was not independently available; no inferred version.',
        'input_sha256':input_hashes,'script_snapshot':script_snapshot,
        'output_sha256':{name:sha(DEST/name) for name in [output_names[0],output_names[1],output_names[3],script_snapshot]},
        'counts':counts,'errors':validation_errors,'network_used':False,
        'prior_input_hashes_unchanged':all(sha(ROOT/path)==digest for path,digest in input_hashes.items()),
        'exposure_log':exposure(contract,phase,'',set(practice)),
    })
    print(json.dumps({'phase':phase,'counts':counts,'validation_errors':validation_errors,
                      'selfreview_gate':selfreview['gate']},ensure_ascii=False))
    return 0 if not validation_errors else 1


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as error:
        DEST.mkdir(parents=True,exist_ok=True)
        stamp = now().replace(':','').replace('.','')
        json_file(DEST/f'failure_{stamp}.json', {'created_at':now(), 'error_type':type(error).__name__,
                                              'error':str(error),'annotator_id':AUTHOR})
        raise
