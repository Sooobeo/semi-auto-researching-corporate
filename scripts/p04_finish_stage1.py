"""Apply and record stage-1 review findings, then establish the next-stage gate."""
import shutil
from p04_common import *

def main():
    for name in ['event_families.csv', 'event_claim_links.csv']:
        path = OUT / name
        backup = OUT / 'stage_reviews/stage_01_before_improvement' / name
        backup.parent.mkdir(parents=True, exist_ok=True)
        if backup.exists():
            raise FileExistsError(backup)
        shutil.copy2(path, backup)
        text = path.read_text(encoding='utf-8').replace('EV-US-MSFT-', 'US-MSFT-')
        path.write_text(text, encoding='utf-8', newline='')
    facts = rows(SOURCE / 'facts_v0_3.jsonl')
    relations = rows(REGISTRY / 'business_relations.jsonl')
    documents = rows(SOURCE / 'document_manifest_v0_3.csv')
    links = rows(OUT / 'event_claim_links.csv')
    edges = []
    for f in facts:
        if f['occurrence_note'] == 'comparative_prior_year':
            previous = [old for old in facts if old['scope_id']==f['scope_id'] and
                        old['fiscal_year']==f['fiscal_year'] and old['period_label']==f['period_label'] and
                        old['doc_id'] != f['doc_id'] and old['metric_id']==f['metric_id']]
            for old in previous:
                edges.append(dict(edge_id=f'OVERLAP-{len(edges)+1:03d}',from_id=old['claim_id'],to_id=f['claim_id'],
                    edge_type='representation_overlap',same_family='false',
                    basis='same_scope_metric_reference_period_different_presentation',
                    consequence='same_development_leakage_group; not_a_confirmed_correction'))
        for ref in f.get('scope_evidence_refs', []):
            edges.append(dict(edge_id=f'SCOPE-{len(edges)+1:03d}',from_id=ref['doc_id'],to_id=f['claim_id'],
                edge_type='retrospective_scope_dependency',same_family='not_applicable',
                basis='publication_unknown_observed_2026_10_05',
                consequence='exclude_dependency_from_2024_2025_asof_packets'))
    csv_file(OUT / 'dependency_edges.csv', edges)
    snapshot = json.loads((OUT / 'input_snapshot.json').read_text(encoding='utf-8'))
    ids = {f['claim_id'] for f in facts}
    checks = {
        'numeric_claim_mapping_33_of_33':len([l for l in links if l['item_type']=='numeric_claim'])==len(facts)==33,
        'relation_source_claims_6_of_6':all(r['claim_id'] in ids for r in relations) and len(relations)==6,
        'stable_existing_event_ids':all(next(l['event_id'] for l in links if l['item_id']==r['relation_id'])==r['event_id'] for r in relations),
        'comparatives_remain_later_publication':all(l['event_id']==l['event_family_id'] for l in links),
        'exposure_documents_3_of_3':len(rows(OUT / 'exposure_manifest.csv'))==len(documents)==3,
        'support_doc_excluded_from_event_quota':sum(bool(d['event_family_id']) for d in documents)==2,
        'scope_dependency_edges_24':sum(e['edge_type']=='retrospective_scope_dependency' for e in edges)==24,
        'representation_overlap_edges_3':sum(e['edge_type']=='representation_overlap' for e in edges)==3,
        'source_hashes_unchanged':all(sha(ROOT/i['path'])==i['sha256'] for i in snapshot['inputs']),
        'all_existing_documents_adaptation':all(d['split']=='adaptation' for d in rows(OUT/'exposure_manifest.csv'))}
    reservation = OUT / 'source_reservation/reservation_summary.json'
    if not reservation.exists():
        raise SystemExit('Source reservation outcome must be recorded before finalizing stage 1.')
    reserved = json.loads(reservation.read_text(encoding='utf-8'))
    write(OUT / 'stage_reviews/stage_01_improvements.md', '''# 1번 자가검증·개선

초기 검사와 별도 agent 검토를 대조했다. 사람 검토가 아니다.

1. 새 EV 접두사 대신 P03 관계의 기존 event_id를 유지했다. 원본 자료는 변경하지 않았다. 수정 전 mapping은 stage_01_before_improvement에 보존했다.
2. 39는 annotation 작업 항목 수다. 고유 source claim_id는 33, relation_id는 6, endpoint는 3, 잠정 발표 event/family는 각 2다.
3. FY2025의 FY2024 비교열 3개는 FY2025 발표에 남겼다. 이전 표시와의 representation_overlap 3개를 추가했으며 correction_of로 단정하지 않았다.
4. annual reference는 family가 없는 보완 문서다. 전사 claim 24개의 retrospective_scope_dependency를 기록해 과거 cutoff에서 제외하도록 했다.
5. 초기 hash 검사가 hash의 존재만 검사하던 부분을 실제 snapshot과의 동등성 검사로 수정했다.
6. 새 평가 후보는 source_reservation 결과로 별도 관리한다. 문서 예약은 정답 확보·test 인증이 아니다. 표본의 음성/비정량/계획·부인/타기업 결측은 유지한다.

다음 단계 개선 과제: raw/normalized/assessment/derived 계약에 실제 표본을 매핑하고, 원문 위치·기간 헤더를 재조회한 후 가이드·스키마를 고정한다.
''')
    if not all(checks.values()):
        raise AssertionError(checks)
    json_file(OUT / 'stage_reviews/stage_01_final.json', {'stage':1,'checked_at':now(),
        'gate':'passed_with_explicit_limitations','checks':checks,'source_reservation_summary_sha256':sha(reservation),
        'counts':{'source_numeric_claims':33,'relation_records':6,'annotation_items':39,'events_agent_grouped':2,
            'human_gold':0,'human_annotation_time_measured':False},
        'limitations':['Human sampling workload and adjudication unmeasured','Coverage gaps remain explicit',
                       'Reserved new document is unlabeled, not certified test data'],
        'next_stage':2})
    print(json.dumps({'stage':1,'checks':checks,'gate':'passed_with_explicit_limitations'}))

if __name__ == '__main__': main()
