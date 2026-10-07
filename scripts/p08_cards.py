"""Compose candidate-based cards using the verified P06/P07 factual projection."""
import sys
from collections import defaultdict
from p08_common import *
sys.path.insert(0, str(ROOT/'web/p05'))
from phase_snapshot import make

QUESTIONS = {
    'human_review_missing': '숫자·기간·사업 범위를 원문 위치와 대조했나요?',
    'selected_evidence_only': '선택 표 셀 밖의 문맥에 추가 조건이 있나요?',
    'publication_time_unknown': '정확한 발표 시각을 확인할 수 있나요?',
    'date_conflict_not_audited': '원문 날짜와 페이지 날짜가 일치하나요?',
    'retrospective_scope_dependency': '전사 범위의 발표 당시 근거가 있나요?',
    'presentation_definition_requires_review': '발표별 사업부 정의가 같은가요?',
    'relation_validity_unknown': '보고 관계의 실제 유효기간이 확인됐나요?',
    'shared_numeric_evidence': '숫자와 관계가 같은 근거를 사용함을 확인했나요?',
    'comparison_conditions_checked': '시점별 계산·보류 이유를 확인했나요?',
}

def build(p06, p07, run_id):
    d = make(Path(p06), Path(p07)); groups = defaultdict(list)
    review = {r['record_id']: r for r in d['review']}
    for f in d['facts']: groups[review[f['record_id']]['review_group_id']].append(f)
    cards = []; failures = []
    for group, facts in sorted(groups.items()):
        try:
            ids = sorted(f['record_id'] for f in facts)
            facts.sort(key=lambda f: (f['kind'] != 'event_claim', f['record_id']))
            reasons = sorted({x for i in ids for x in review[i]['review_reasons']})
            changes = [x for x in d['changes'] if x['new_record_id'] in ids]
            card = {
                'schema_version': 'p08-card-0.1', 'card_id': stable('CARD',group), 'run_id': run_id,
                'event_id': None, 'event_id_missing_reason': 'candidate_based_no_confirmed_event',
                'review_group_id': group, 'candidate_refs': ids,
                'event_family_ids': sorted({f['event_family_id'] for f in facts}),
                'facts': facts, 'changes': changes,
                'prior_fact_refs': sorted({x['prior_record_id'] for x in changes if x['prior_record_id']}),
                'priors': [x for x in d['priors'] if x['new_record_id'] in ids],
                'calculations': [x for x in d['calculations'] if set(x['input_refs']) & set(ids)],
                'business_relation_refs': [f['record_id'] for f in facts if f['kind'] == 'business_relation'],
                'source_runs': d['source_runs'], 'policies': d['policies'],
                'review_readiness': 'needs_review', 'evidence_status': 'company_reported',
                'pipeline_status': 'succeeded', 'review_reasons': reasons,
                'review_questions': [QUESTIONS[x] for x in reasons],
                'comparison_readiness': 'not_comparable' if any(x['compatibility']['decision']=='not_comparable' for x in changes) else 'needs_review',
                'materiality_assessment': {'label': None,'score': None,'probability': None,'status': 'not_evaluated'},
                'uncertainty_fields': {i: review[i]['missing_features'] for i in ids},
                'analyst_memo_refs': [], 'assumption_refs': [],
                'financial_reconciliation_status': 'incomplete',
                'exposure_status': 'adaptation', 'human_gold': False,
            }
            card['card_version'] = digest({k:v for k,v in card.items() if k != 'run_id'})
            cards.append(card)
        except (KeyError, ValueError, TypeError) as exc:
            failures.append({'review_group_id': group,'candidate_refs': [f['record_id'] for f in facts],
                             'status': 'failed','reason': type(exc).__name__})
    return cards, failures, d
