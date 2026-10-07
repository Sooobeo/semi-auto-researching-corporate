"""Single-writer transactional feedback journal. Imported text is never executed/exported."""
from __future__ import annotations
import re
from contextlib import contextmanager
from p08_common import *

ACTIONS = ('confirm','correct_fact','irrelevant','investigate','update_assumption')
FIELDS = ('review_status','numeric_value','reference_period','scope_id','assumption_status')
MAX_BYTES = 512_000
MAX_EVENTS = 200
EVENT_KEYS = {'feedback_id','idempotency_key','source_run','card_id','card_version','actor_id',
    'action','field','before','after','evidence_refs','reason_code','created_at'}

@contextmanager
def locked(store):
    store = Path(store); store.mkdir(parents=True, exist_ok=True); lock = store/'.writer.lock'
    try: fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError: raise ValueError('feedback_writer_locked')
    try: yield
    finally: os.close(fd); lock.unlink()

def base_value(card, field):
    f = card['facts'][0]
    return {'review_status': 'needs_review','numeric_value': f['normalized']['numeric_value'],
        'scope_id': f['normalized']['scope_id'],'reference_period': f['period'],
        'assumption_status': None}[field]

def validate_event(e, cards, run_id):
    if not isinstance(e, dict) or set(e) != EVENT_KEYS: raise ValueError('event_fields_not_allowlisted')
    c = cards.get(e['card_id'])
    if not c: raise ValueError('unknown_card')
    if e['source_run'] != run_id: raise ValueError('wrong_source_run')
    if e['card_version'] != c['card_version']: raise ValueError('stale_card_version')
    if e['action'] not in ACTIONS or e['field'] not in FIELDS: raise ValueError('unsupported_action_or_field')
    if e['before'] != base_value(c, e['field']): raise ValueError('forged_before')
    if not all(isinstance(e[k], str) and re.fullmatch(r'[A-Za-z0-9_.:-]{1,100}',e[k]) for k in ('actor_id','feedback_id','idempotency_key')):
        raise ValueError('invalid_identity')
    from datetime import datetime
    t = datetime.fromisoformat(e['created_at'].replace('Z','+00:00'))
    if not t.tzinfo: raise ValueError('time_offset_required')
    ev = {x['evidence_id'] for f in c['facts'] for x in f['evidence']}
    if not isinstance(e['evidence_refs'], list) or not set(e['evidence_refs']) <= ev: raise ValueError('unknown_evidence')
    if e['reason_code'] not in ('source_checked','value_mismatch','scope_or_period_mismatch','needs_more_evidence','not_relevant','assumption_changed'):
        raise ValueError('reason_not_allowlisted')
    allowed = {'confirm': {'review_status'}, 'irrelevant': {'review_status'}, 'investigate': {'review_status'},
               'correct_fact': {'numeric_value','scope_id','reference_period'}, 'update_assumption': {'assumption_status'}}
    if e['field'] not in allowed[e['action']]: raise ValueError('action_field_mismatch')
    expected = {'confirm':'confirmed_candidate','irrelevant':'irrelevant_candidate','investigate':'investigate_candidate'}
    if e['action'] in expected and e['after'] != expected[e['action']]: raise ValueError('invalid_review_value')
    if e['field'] == 'numeric_value':
        if not isinstance(e['after'],str) or not re.fullmatch(r'-?\d{1,30}(\.\d{1,28})?',e['after']): raise ValueError('invalid_decimal')
        if not ev.intersection(e['evidence_refs']): raise ValueError('correction_evidence_required')
    if e['field'] == 'scope_id' and e['after'] not in ('US-MSFT-CONSOLIDATED','US-MSFT-SEG-PBP','US-MSFT-SEG-IC','US-MSFT-SEG-MPC'):
        raise ValueError('unknown_scope')
    if e['field'] == 'reference_period':
        if not isinstance(e['after'],dict) or set(e['after']) != set(c['facts'][0]['period']): raise ValueError('period_fields')
        from datetime import date
        for key in ('period_start','period_end','as_of_date'):
            if e['after'][key] is not None: date.fromisoformat(e['after'][key])
        if e['after']['period_kind'] not in ('quarter','annual','instant') or e['after']['period_basis'] != 'fiscal': raise ValueError('period_type')
        if e['after']['period_start'] and e['after']['period_end'] and e['after']['period_start'] > e['after']['period_end']: raise ValueError('period_order')
        if not ev.intersection(e['evidence_refs']): raise ValueError('correction_evidence_required')
    if e['field'] == 'assumption_status' and e['after'] not in ('proposed','withheld','needs_review'): raise ValueError('assumption_value')
    if e['after'] == e['before']: raise ValueError('no_change')
    return True

def journal(store):
    p = Path(store)/'feedback_journal.json'
    return read(p) if p.exists() else {'schema_version':'p08-feedback-0.1','revision':0,'events':[],'conflicts':[],'resolutions':[],'imports':[]}

def projections(store, j):
    # The atomic journal is authoritative; these are rebuildable append-history projections.
    write_rows(Path(store)/'feedback_events.jsonl',j['events'])
    write_rows(Path(store)/'feedback_conflicts.jsonl',j['conflicts'])
    write_rows(Path(store)/'feedback_resolutions.jsonl',j['resolutions'])
    write_rows(Path(store)/'feedback_imports.jsonl',j['imports'])

def import_payload(payload, run_dir, store):
    run_dir = Path(run_dir); run_id = run_dir.name
    cards = {c['card_id']:c for c in rows(run_dir/'review_cards.jsonl')}
    if not isinstance(payload,dict) or set(payload) != {'schema_version','source_run','events'} or payload['schema_version'] != 'p08-feedback-export-0.1':
        raise ValueError('invalid_export_envelope')
    if payload['source_run'] != run_id or not isinstance(payload['events'],list) or len(payload['events']) > MAX_EVENTS: raise ValueError('wrong_run_or_size')
    if len(json.dumps(payload).encode()) > MAX_BYTES: raise ValueError('file_too_large')
    result = {'accepted':0,'duplicates':0,'rejected':[],'conflicts':0,'source_run':run_id,'received_at':now()}
    with locked(store):
        j = journal(store); keys = {e['idempotency_key']:e for e in j['events']}
        fids = {e['feedback_id'] for e in j['events']}
        for index, e in enumerate(payload['events']):
            try:
                validate_event(e,cards,run_id)
                if e['idempotency_key'] in keys:
                    prev = {k: keys[e['idempotency_key']][k] for k in EVENT_KEYS}
                    if prev != e: raise ValueError('idempotency_payload_conflict')
                    result['duplicates'] += 1; continue
                if e['feedback_id'] in fids: raise ValueError('feedback_id_collision')
                record = dict(e,actor_verification='self_declared',time_source='client_self_reported',
                    received_at=now(),owner_verified_by=None,review_status='candidate',training_eligibility='excluded_current_cycle',human_gold=False)
                rivals = [x for x in j['events'] if (x['card_id'],x['card_version'],x['field']) ==
                    (e['card_id'],e['card_version'],e['field']) and x['after'] != e['after']]
                if rivals:
                    record['review_status'] = 'conflict_candidate'
                    conflict = {'conflict_id':stable('CONFLICT',*[x['feedback_id'] for x in rivals],e['feedback_id']),
                        'source_run':run_id,'card_id':e['card_id'],'field':e['field'],
                        'feedback_ids':[x['feedback_id'] for x in rivals]+[e['feedback_id']],'status':'unresolved'}
                    j['conflicts'].append(conflict); result['conflicts'] += 1
                j['events'].append(record); keys[e['idempotency_key']] = record; fids.add(e['feedback_id']); result['accepted'] += 1
            except (ValueError,KeyError,TypeError) as exc:
                result['rejected'].append({'event_index':index,'reason':str(exc) if isinstance(exc,ValueError) else type(exc).__name__})
        j['revision'] += 1; result['revision'] = j['revision']; j['imports'].append(result)
        atomic(Path(store)/'feedback_journal.json',j); projections(store,j)
    return result

def resolve(store, conflict_id, decision, selected, owner):
    if decision not in ('adopt','merge','defer') or not re.fullmatch(r'[A-Za-z0-9_.:-]{1,100}',owner): raise ValueError('invalid_resolution')
    with locked(store):
        j = journal(store); c = next((x for x in j['conflicts'] if x['conflict_id']==conflict_id),None)
        if not c or not set(selected) <= set(c['feedback_ids']): raise ValueError('unknown_conflict_or_feedback')
        if decision == 'adopt' and len(selected) != 1: raise ValueError('select_one_feedback')
        if decision == 'merge':
            if len(selected) < 2: raise ValueError('merge_requires_multiple')
            values = [x['after'] for x in j['events'] if x['feedback_id'] in selected]
            if any(v != values[0] for v in values): raise ValueError('merge_requires_equal_values_submit_new_revision_for_other_values')
        r = {'resolution_id':stable('RES',conflict_id,j['revision']+1),'conflict_id':conflict_id,'decision':decision,
            'selected_feedback_ids':selected,'owner_id':owner,'owner_verification':'local_operator_asserted','created_at':now(),
            'human_gold':False,'training_eligibility':'excluded_current_cycle'}
        j['resolutions'].append(r); j['revision'] += 1
        atomic(Path(store)/'feedback_journal.json',j); projections(store,j)
    return r

def snapshot_feedback(store, run_id, cards):
    j = journal(store); versions = {c['card_id']:c['card_version'] for c in cards}
    # A rerun does not reset review history when the logical card version is identical.
    ev = [e for e in j['events'] if versions.get(e['card_id'])==e['card_version']]
    compatible_ids={e['feedback_id'] for e in ev}
    conflicts=[c for c in j['conflicts'] if set(c['feedback_ids']) & compatible_ids]
    return {'schema_version':'p08-feedback-snapshot-0.1','revision':j['revision'],
        'journal_hash':digest(j),'events':ev,'compatible_source_runs':sorted({e['source_run'] for e in ev}),
        'conflicts':conflicts,
        'resolutions':[r for r in j['resolutions'] if r['conflict_id'] in {c['conflict_id'] for c in conflicts}],
        'original_predictions_preserved':True,'human_gold':0,'shared_auto_save':False}
