"""Independent integration checks and a frozen annotation contract."""
from p04_common import *

def main():
    previous = require_stage(1)
    report = json.loads((OUT/'contract_validation_final.json').read_text(encoding='utf-8'))
    records = rows(OUT/'contract_records.jsonl')
    packets = rows(OUT/'source_packets.jsonl')
    evidence = {e['evidence_id']:e for e in rows(OUT/'evidence_index.jsonl')}
    facts = {f['claim_id']:f for f in rows(SOURCE/'facts_v0_3.jsonl')}
    guide = (OUT/'annotation_guide_v1.md').read_text(encoding='utf-8')
    annotation = json.loads((OUT/'annotation_output_contract.json').read_text(encoding='utf-8'))
    snapshot = json.loads((OUT/'input_snapshot.json').read_text(encoding='utf-8'))
    reservation = json.loads((OUT/'source_reservation/reservation_summary.json').read_text(encoding='utf-8'))
    checks = {
        'contract_validation_passed':report['status']=='passed_with_explicit_limitations' and not report['findings'],
        'validated_current_schema':report['schema_sha256']==sha(OUT/'event_schema_v1.json'),
        'validated_current_records':report['records_sha256']==sha(OUT/'contract_records.jsonl'),
        'all_packets_resolve_evidence':all(set(p['evidence_refs']) <= evidence.keys() for p in packets),
        'packet_preserves_input_revision':all(p['revision_id']==evidence[p['evidence_refs'][0]]['revision_id'] for p in packets),
        'raw_packets_omit_normalized_answer_object':all('normalized' not in p for p in packets),
        'numeric_values_match_original_source_base_units':all(r['normalized']['numeric_value']==facts[r['claim_id']]['numeric_value_base_units'] for r in records if r['record_kind']=='event_claim'),
        'relation_business_effective_period_unknown':all(r['normalized']['temporal']['effective_period']['period_start'] is None and r['normalized']['temporal']['effective_period']['period_end'] is None for r in records if r['record_kind']=='business_relation'),
        'date_only_preserved':all(r['normalized']['temporal']['published_at'] is None for r in records),
        'current_agent_status_honest':all(r['annotation_status']=='agent_draft' and not r['human_gold'] for r in records),
        'guide_post_cutoff_exposure_disclosed':'guide_contains_post_cutoff_context' in guide and 'guide_contains_post_cutoff_context' in annotation['exposure_flags_required'],
        'field_null_reasons_required':'field_missing_reasons' in annotation['required_top_level'],
        'provenance_required':'provenance' in annotation['required_top_level'],
        'original_input_hashes_unchanged':all(sha(ROOT/x['path'])==x['sha256'] for x in snapshot['inputs']),
        'new_reserved_document_not_in_development':all(p['doc_id']!=reservation['doc_id'] for p in packets),
        'reservation_hash_unchanged':sha(OUT/'source_reservation/reservation_summary.json')==previous['source_reservation_summary_sha256'],
        'stage_sequence':previous['checked_at'] < report['checked_at']}
    json_file(OUT/'stage_reviews/stage_02_initial.json', {'stage':2,'checked_at':now(),'checks':checks,
        'adapter_initial_review':'../contract_validation_initial.json','adapter_final_review':'../contract_validation_final.json',
        'status':'passed' if all(checks.values()) else 'needs_improvement'})
    if not all(checks.values()): raise AssertionError(checks)
    write(OUT/'stage_reviews/stage_02_improvements.md', '''# 2번 자가검증·개선

실자료 39레코드의 계약/원문 위치 검사와 독립 통합 검사를 수행했다. 초기 mapper 실패와 초기 가이드 원본은 contract_revisions/initial 및 stage_02_before_improvement에 보존했다.

- 현금흐름 statement_type의 P1 enum 불일치를 수정했다.
- capex source_numeric_value가 이미 부호 변환된 값이었던 문제를 수정하고 원 괄호 음수와 양의 cash outlay 변환을 함께 보존했다.
- 보고 사업부의 보고기간을 실제 관계 유효기간으로 사용하지 않도록 reference/effective를 분리했다.
- company_reported의 원 unaudited qualifier와 기간 시작일 유도 방식을 별도로 보존했다. 날짜 충돌 수동 감사 미실시를 완료로 표현하지 않도록 수정했다.
- 가이드 자체의 후속정보 노출 때문에 A/B도 엄밀한 미노출 as-of 평가자가 아니라는 점을 기록했다. 현재 결과는 retrospective cutoff simulation이다.
- 주석 계약에 provenance와 필드별 null 사유, scope의 과거 근거 상태를 추가했다. annotator_kind 명칭과 instant duration=null을 통일했다.

반례는 원문 span·없는 ID·scope·정의·가짜 시각·미래 근거·관계 방향/효력·null·허위 gold·배율/부호·헤더·hash·unaudited 누락·기간 유도·미실시 감사 오표시를 포함한다. 숫자는 최종 validation JSON에서 재계산한다.

다음 단계: 고정된 raw packet과 공통 가이드만 A/B agent에 배정하고, 연습 결과를 먼저 검사한 후 본작업을 수행한다. 인간 주석·gold·본문 완전성은 별도 미완료 항목이다.
''')
    paths = ['event_schema_v1.json','annotation_guide_v1.md','annotation_output_contract.json',
        'annotation_reference.json','source_packets.jsonl','evidence_index.jsonl','contract_records.jsonl',
        'schema_migration.md','contract_validation_final.json','event_claim_links.csv','dependency_edges.csv']
    code = ['p04_build_contract.py','p04_contract_validation.py','p04_annotation_validation.py','p04_common.py']
    json_file(OUT/'contract_freeze_manifest.json',{'frozen_at':now(),'guide_version':'us-p3-guide-1.0',
        'registry_version':'us-p2-0.1.0','freeze_kind':'agent_development_annotation_contract',
        'files':[{'path':name,'sha256':sha(OUT/name)} for name in paths],
        'code':[{'path':'scripts/'+name,'sha256':sha(ROOT/'scripts'/name)} for name in code],
        'human_approval_observed':False,'reserved_content_exposed':False})
    json_file(OUT/'stage_reviews/stage_02_final.json',{'stage':2,'checked_at':now(),
        'gate':'passed_with_explicit_limitations','checks':checks,
        'counts':report['counts'],'negative_cases':report['negative_cases'],
        'freeze_sha256':sha(OUT/'contract_freeze_manifest.json'),'next_stage':3,
        'limitations':report['limitations']})
    print(json.dumps({'stage':2,'checks_passed':sum(checks.values()),'checks_total':len(checks),
        'records':len(records),'negative_cases':report['negative_cases']}))

if __name__=='__main__': main()
