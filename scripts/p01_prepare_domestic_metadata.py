"""Prepare a body-free, provisional P01 review queue from saved search metadata.

No network requests, article text processing, ontology, or final labels. Refuses
to overwrite derived artifacts. The input retains every returned search link.
"""
import argparse
import csv
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit


SOURCES = {
    'www.hankyung.com': 'HANKYUNG', 'www.etnews.com': 'ETNEWS',
    'm.etnews.com': 'ETNEWS', 'zdnet.co.kr': 'ZDNET_KR',
    'www.newspim.com': 'NEWSPIM', 'search.newspim.com': 'NEWSPIM',
    'm.newspim.com': 'NEWSPIM', 'ir.newspim.com': 'NEWSPIM',
    'www.edaily.co.kr': 'EDAILY', 'www.mk.co.kr': 'MK',
    'www.dt.co.kr': 'DT', 'www.ebn.co.kr': 'EBN',
}


def read_csv(path):
    with path.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir', required=True, type=Path)
    args = parser.parse_args()
    run = args.run_dir.resolve()
    data = json.loads((run / 'discovery_metadata.json').read_text(encoding='utf-8'))
    anchors = {r['event_family_id']: r for r in read_csv(run / 'official_anchors.csv')}
    registry = {r['source_id']: r for r in read_csv(run / 'source_registry.csv')}
    now = datetime.now(timezone.utc).isoformat(timespec='seconds')
    inventory = []
    by_id = {}
    for batch in data['batches']:
        for result in batch['results']:
            result_id = result.get('result_id', result.get('search_reference'))
            row = {
                'discovery_id': f'DISC-{len(inventory)+1:04d}',
                'batch_id': batch['batch_id'], 'result_id': result_id,
                'query': batch.get('q') or ' | '.join(batch.get('queries', [])),
                'query_family_hint': batch.get('family', 'multiple_queries'),
                'source_url': result['url'], 'title_raw_search': result['title'],
                'search_published_raw': result['search_published_raw'],
                'discovery_date': data['discovery_date'],
                'discovery_time_precision': 'date', 'metadata_recorded_at': now,
                'selected_for_primary_sample': 'false',
                'screening_status': 'unselected_metadata_not_adjudicated',
                'body_access_status': 'not_requested',
            }
            inventory.append(row)
            by_id[result_id] = row
    candidates, labels, links, body_audit = [], [], [], []
    seen = set()
    for family, result_ids in data['selections'].items():
        if family not in anchors:
            raise ValueError(f'Anchor missing: {family}')
        if len(result_ids) != 3:
            raise ValueError(f'Expected three originally selected candidates: {family}')
        outlets = set()
        for result_id in result_ids:
            hit = by_id[result_id]
            url = hit['source_url']
            if url in seen:
                raise ValueError('A candidate URL cannot fill two primary quotas')
            seen.add(url)
            source = SOURCES[urlsplit(url).hostname]
            if source not in registry or source in outlets:
                raise ValueError(f'Missing registry or duplicate outlet in family: {family}')
            outlets.add(source)
            suffix = hashlib.sha256(url.encode('utf-8')).hexdigest()[:16]
            cid, did = 'CAND-' + suffix, 'NEWS-' + suffix
            hit['selected_for_primary_sample'] = 'true'
            hit['screening_status'] = 'selected_title_url_only_body_unverified'
            anchor = anchors[family]
            candidate = {
                'candidate_id': cid, 'doc_id': did,
                'doc_identity_status': 'provisional_url_based_canonical_unverified',
                'source_id': source, 'source_url': url,
                'title_raw_search': hit['title_raw_search'],
                'discovery_id': hit['discovery_id'],
                'discovery_method': 'public_web_search_title_url_only',
                'discovery_date': data['discovery_date'],
                'discovery_time_precision': 'date', 'metadata_recorded_at': now,
                'search_published_raw': hit['search_published_raw'],
                'publisher_published_raw': '', 'provider_published_raw': '',
                'published_missing_reason': 'publisher_metadata_not_verified',
                'published_time_precision': 'unknown',
                'event_family_id': family, 'primary_sampling_family_id': family,
                'company_id': family.split('-')[0],
                'company_match_status': 'candidate_title_query_only',
                'scope_id': 'unknown_pending_article_body',
                'reference_period': '',
                'anchor_scope_id': anchor.get('scope_id', ''),
                'anchor_reference_period': anchor.get('reference_period', anchor.get('reference_quarter', '')),
                'selection_basis': 'title_topic_match_and_distinct_outlet; full_body_pending',
                'selection_status': 'frozen_before_rights_gate',
                'body_status': 'not_acquired_rights_unresolved',
                'rights_status': registry[source]['rights_status'],
                'canonical_duplicate_status': 'not_yet_checked',
                'production_independence': 'unknown',
                'schema_version': 'p01-pilot-provisional-0.1',
            }
            candidates.append(candidate)
            labels.append({'candidate_id': cid, 'doc_id': did, 'eligibility': 'unverified',
                           'reason_code': 'body_rights_and_body_unverified',
                           'editorial_genre': 'unknown', 'urgency_format': 'unknown',
                           'production_origin': 'unclear', 'evidence_span': '',
                           'reviewer': '', 'review_status': 'not_performed',
                           'guide_version': 'P01-news-design-0.1'})
            links.append({'candidate_id': cid, 'doc_id': did, 'event_family_id': family,
                          'is_primary_sampling_link': 'true',
                          'link_status': 'provisional_title_query_candidate',
                          'article_event_role': 'uncertain', 'coverage_stage': 'unknown',
                          'article_scope_id': 'unknown', 'article_action_raw': '',
                          'article_reference_period': '', 'claim_modality': 'unknown',
                          'link_evidence_span': '',
                          'uncertainty_reason': 'No licensed body, no claim alignment'})
            body_audit.append({'candidate_id': cid, 'doc_id': did,
                               'body_completeness': 'not_assessed',
                               'omission_contamination': 'not_assessed',
                               'date_scope_number_review': 'not_assessed',
                               'offset_round_trip': 'not_measured',
                               'audit_status': 'not_performed_rights_unresolved'})
    # One candidate per family before second candidates: balanced pending queue.
    first_twenty = []
    for rank in range(3):
        for family in data['selections']:
            same = [r for r in candidates if r['event_family_id'] == family]
            if len(first_twenty) < 20:
                first_twenty.append(same[rank])
    review = [{'candidate_id': row['candidate_id'], 'doc_id': row['doc_id'],
               'event_family_id': row['event_family_id'], 'reviewer_slot': slot,
               'actual_reviewer_id': '', 'assignment_status': 'unassigned',
               'review_status': 'blocked_pending_licensed_body',
               'body_completeness': '', 'production_origin': '',
               'editorial_genre': '', 'event_link_judgment': '', 'evidence_ref': '',
               'completed_at': ''}
              for row in first_twenty for slot in ('human_A', 'human_B')]
    tables = {
        'discovered_links.csv': (inventory, list(inventory[0])),
        'article_candidates.csv': (candidates, list(candidates[0])),
        'article_classification.csv': (labels, list(labels[0])),
        'article_event_links.csv': (links, list(links[0])),
        'body_audit.csv': (body_audit, list(body_audit[0])),
        'human_review_queue.csv': (review, list(review[0])),
        'claim_alignment.csv': ([], ['anchor_claim_id', 'article_claim_id', 'doc_id', 'event_family_id', 'claim_relation', 'evidence_span', 'review_status']),
        'sentence_spans.csv': ([], ['doc_id', 'revision_id', 'claim_id', 'segment_position', 'speaker_type', 'start_codepoint', 'end_codepoint', 'evidence_ref', 'review_status']),
        'chunk_spans.csv': ([], ['doc_id', 'revision_id', 'claim_id', 'start_codepoint', 'end_codepoint', 'chunk_type', 'evidence_ref', 'review_status']),
    }
    targets = [run / name for name in tables] + [run / 'metadata_summary.json']
    if any(p.exists() for p in targets):
        raise FileExistsError('Derived output exists; use a new run directory')
    for name, (rows, fields) in tables.items():
        with (run / name).open('x', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
    summary = {
        'run_id': data['run_id'], 'prepared_at': now,
        'search_batches': len(data['batches']),
        'returned_link_occurrences': len(inventory),
        'unique_returned_urls_including_nonarticles': len({r['source_url'] for r in inventory}),
        'selected_unique_candidate_urls': len(candidates),
        'candidate_doc_ids_identity_provisional': len({r['doc_id'] for r in candidates}),
        'primary_sampling_links': len(links), 'selected_anchor_families_provisional': len(data['selections']),
        'outlet_candidate_counts': dict(Counter(r['source_id'] for r in candidates)),
        'publisher_body_access_attempts': 0, 'acquired_bodies': 0,
        'verified_complete_bodies': 0, 'verified_independent_articles': 0,
        'verified_claim_comparison_pairs': 0,
        'human_review_candidate_queue': len(first_twenty),
        'human_review_slots_pending': len(review), 'human_reviews_completed': 0,
        'ontology_status': 'deferred_by_user',
        'label_status': 'unverified_placeholders_only',
    }
    with (run / 'metadata_summary.json').open('x', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == '__main__':
    main()
