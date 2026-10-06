"""Build source-linked sampling and exposure manifests, before later stages."""
from p04_common import *

def main():
    facts = rows(SOURCE / 'facts_v0_3.jsonl')
    relations = rows(REGISTRY / 'business_relations.jsonl')
    documents = rows(SOURCE / 'document_manifest_v0_3.csv')
    inputs = [SOURCE / 'facts_v0_3.jsonl', SOURCE / 'document_manifest_v0_3.csv',
              SOURCE / 'extraction_audit_v0_3.csv', SOURCE / 'source_registry.csv',
              SOURCE / 'source_conditions.md', SOURCE / 'scope_corroboration.json',
              REGISTRY / 'business_relations.jsonl', REGISTRY / 'registry_v0.1_manifest.json',
              REGISTRY / 'entity_catalog.csv', REGISTRY / 'metric_catalog.csv',
              REGISTRY / 'definition_history.csv', REGISTRY / 'applied_002/comparability_results.jsonl',
              ROOT / 'artifacts/us_equity/p1/event_schema_v0.1.json',
              ROOT / 'artifacts/us_equity/p1/annotation_guide_v0.1.md']
    json_file(OUT / 'input_snapshot.json', {'created_at': now(), 'inputs': [
        {'path': p.relative_to(ROOT).as_posix(), 'sha256': sha(p)} for p in inputs],
        'legacy_inputs': [], 'source_revision': 'v0_3', 'registry_version': 'us-p2-0.1.0'})
    family_ids = sorted({f['event_family_id'] for f in facts})
    family_rows = []
    for family in family_ids:
        fs = [f for f in facts if f['event_family_id'] == family]
        rs = [r for r in relations if r['event_family_id'] == family]
        family_rows.append(dict(event_family_id=family, event_id=event_id(family),
            event_type='earnings_release', company_id='US-MSFT', doc_id=fs[0]['doc_id'],
            published_date=fs[0]['published_date'], numeric_claim_count=len(fs),
            relation_claim_count=len(rs), split='adaptation',
            leakage_group_id='LG-MSFT-EXPOSED-FY2024-FY2025-EARNINGS',
            grouping_basis='same_company_earnings_announcement; atomic_claims_preserved',
            status='agent_structural_grouping_not_human_gold'))
    csv_file(OUT / 'event_families.csv', family_rows)
    links = [dict(item_id=f['claim_id'], item_type='numeric_claim', doc_id=f['doc_id'],
                  event_family_id=f['event_family_id'], event_id=event_id(f['event_family_id'])) for f in facts]
    links += [dict(item_id=r['relation_id'], item_type='reporting_relation', doc_id=r['evidence_refs'][0]['doc_id'],
                   event_family_id=r['event_family_id'], event_id=event_id(r['event_family_id'])) for r in relations]
    csv_file(OUT / 'event_claim_links.csv', links)
    csv_file(OUT / 'exposure_manifest.csv', [dict(doc_id=d['doc_id'], revision_id=d['revision_id'],
        event_family_id=d['event_family_id'], source_hash=d['sha256'], split='adaptation',
        exposure_reason='P03_registry_development_and_retrospective_comparison',
        is_numeric_sample=str(bool(d['event_family_id'])).lower(),
        support_only=str(not bool(d['event_family_id'])).lower()) for d in documents])
    csv_file(OUT / 'coverage_gaps.csv', [dict(stratum=s, available_independent_families=n, status=status, next_action=action)
        for s,n,status,action in [
            ('earnings_and_reporting_membership', 2, 'available_exposed', 'build_adaptation_packet'),
            ('unused_later_period', 0, 'candidate_not_yet_accessed', 'reserve_FY2026_Q1_metadata_only'),
            ('plan_execution_correction_denial', 0, 'unavailable_in_selected_sample', 'source_rights_and_new_sample_required'),
            ('customer_supplier_product_nonquantitative', 0, 'unavailable_in_selected_sample', 'source_rights_and_new_sample_required'),
            ('irrelevant_documents_and_no_change_controls', 0, 'not_sampled', 'classification_recall_not_evaluable'),
            ('independent_human_annotations', 0, 'not_performed', 'assign_actual_human_annotators_before_gold'),
            ('company_holdout', 0, 'not_acquired', 'separate_company_required_for_that_evaluation')]])
    json_file(OUT / 'execution_authorization.json', {
        'recorded_at': now(), 'user_request': '5번까지 쭉 진행하고, 각 순서 번호 마무리할 때마다 자가검증하고 개선할 점 업데이트한 다음 다음 번호로 넘어간다',
        'authorized_scope': 'execute five P04 work packages with sequential review and improvement',
        'execution_mode': 'available_evidence_and_explicitly_labeled_agent_work',
        'human_annotation_authorized_or_observed_by_this_record': False,
        'human_gate_waiver_inherited_as_completion': False,
        'rule': 'No invented human identity, annotation, agreement, adjudication, or gold; proceed with useful automated work and record pending human components.'})
    write(OUT / 'sampling_protocol.md', '''# P04 표본 계획 1.0

기준일 2026-10-06. P04=Phase 3. 현재 관측 자료에 한정한 실행 표본이며 대표성·최적 표본 수를 주장하지 않는다.

- 개발 표본: Microsoft FY2024 Q4/FY2025 Q4 release 2문서·2 발표 family, 원자 숫자 주장 33개, 보고 사업부 관계 주장 6개(고유 endpoint 3개).
- 회계범위 참고 문서 1개는 숫자/발표 표본 분모에 넣지 않는다. 발행일 미상과 2026년 관측을 유지한다.
- 발표 사건은 각 release에서 함께 공표한 재무 결과를 묶는 2개 agent 사건 그룹이다. 숫자 33개나 관계 6개를 독립 사건 수로 바꾸지 않는다. claim의 scope/기간/정의는 계속 개별 보존한다.
- 기존 자료 전체를 adaptation으로 고정한다. FY2025 비교열과 FY2024 발표 사이 연결은 두 family를 하나의 누수 점검 그룹에 둔다. 새 자료의 비교열은 기존 주장 재등장 여부를 검사해야 한다.
- 후속 미사용 후보는 Microsoft FY2026 Q1 공식 release 1문서이다. 정책·robots·최종 호스트 확인 뒤 원본은 private에 예약하며 이번 개발 과정에는 메타데이터만 노출한다. 확보 실패를 대체 후보로 조용히 교체하지 않는다. 아직 확보했다고 세지 않는다.
- 실적/계획/실행/정정/부인/반복/정성/무관 유형은 coverage_gaps.csv로 관리한다. 현재 두 release로 전 유형·관련성 분류 성능을 평가할 수 없다.
- 표본 확대량, 인간 중복 주석 비율·인력·시간은 미측정이다. 옛 한국 자료 quota나 임의 정확도 목표를 가져오지 않는다. 초기 개발은 확보된 39개 숫자/관계 레코드 전부를 대상으로 한다.
- agent 주석은 작성 주체와 기존 입력 노출을 기록한다. 독립 인간 주석·gold·사람 일치도는 실제 수행 전까지 미완료다. agent 검토 두 개가 인간 두 명을 대신하지 않는다.
- 원문 prose의 AI 입력/학습 권리는 미확인이다. 허용 범위의 최소 수치·기간·표 좌표·표준 라벨만 사용하고 원본은 기존 private 위치를 유지한다.

순서: 1 표본/노출 → 자가검증/개선 → 2 계약/가이드 → 자가검증/개선 → 3 주석 실행 → 자가검증/개선 → 4 비교/조정 → 자가검증/개선 → 5 분할/검증/인계. 각 단계 최종 검사 파일이 있어야 다음 단계 실행을 허용한다.
''')
    checks = {'unique_claim_ids': len({x['item_id'] for x in links}) == len(links),
        'source_claims_preserved': len(links) == len(facts)+len(relations),
        'all_existing_adaptation': all(d['split_exposure']=='adaptation' for d in documents),
        'no_legacy_inputs': all('us_equity' in str(p) for p in inputs),
        'source_events_separate_from_claims': len(family_ids)==2 and len(facts)==33,
        'support_doc_not_family': sum(bool(d['event_family_id']) for d in documents)==2,
        'snapshot_hashes_match': all(sha(ROOT / item['path']) == item['sha256'] for item in
            __import__('json').loads((OUT / 'input_snapshot.json').read_text(encoding='utf-8'))['inputs'])}
    json_file(OUT / 'stage_reviews/stage_01_initial.json', {'stage':1,'checked_at':now(),'checks':checks,
        'counts':{'numeric_claims':len(facts),'relation_claims':len(relations),'events_agent_grouped':len(family_ids),
                  'numeric_documents':2,'support_documents':1,'independent_human_gold':0},
        'status':'awaiting_independent_review_and_source_reservation'})
    print(json.dumps({'stage':1,'checks':checks,'records':len(links)}))

if __name__ == '__main__':
    main()
