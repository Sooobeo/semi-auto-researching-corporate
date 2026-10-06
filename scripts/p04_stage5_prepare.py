"""Freeze adaptation assignments and an unlabeled reservation, without opening it."""
from p04_common import *

def main():
    require_stage(4)
    documents=rows(SOURCE/'document_manifest_v0_3.csv')
    families=rows(OUT/'event_families.csv')
    groups={f['event_family_id']:f['leakage_group_id'] for f in families}
    group=next(iter(groups.values())); assert len(set(groups.values()))==1
    reserved=json.loads((OUT/'source_reservation/reservation_summary.json').read_text('utf-8'))
    reviewed=rows(OUT/'reviewed_agent_claims.jsonl')+rows(OUT/'reviewed_agent_relations.jsonl')
    version='us-p3-split-1.0'; output=[]; by_doc={d['doc_id']:d for d in documents}
    def base(d):
        return {'row_id':'DOC:'+d['doc_id'],'row_kind':'document','item_id':'','item_type':'',
            'doc_id':d['doc_id'],'revision_id':d['revision_id'],'event_family_id':d.get('event_family_id',''),
            'event_id':d.get('event_family_id',''),'company_id':'US-MSFT','leakage_group_id':group,
            'split':'adaptation','exposure_status':'development_exposed','published_date':d.get('published_date',''),
            'time_precision':d['time_precision'],'observed_at':d['observed_at'],'source_hash':d['sha256'],
            'human_gold':'false','test_eligible':'false','annotation_ids':'',
            'exclusion_reason':'prior_registry_and_guide_development_exposure','split_version':version}
    for d in documents:
        r=base(d)
        if not d['event_family_id']:r['exclusion_reason']='support_only_publication_unknown_historical_ineligible'
        output.append(r)
    for item in reviewed:
        r=base(by_doc[item['facts']['doc_id']]);r.update(row_id='ITEM:'+item['item_id'],row_kind='annotation_item',
            item_id=item['item_id'],item_type=item['record_kind'],annotation_ids=';'.join(item['source_annotation_ids']))
        output.append(r)
    r=base(reserved);r.update(leakage_group_id='PENDING-US-MSFT-FY2026-Q1',split='reserved_unlabeled',
        exposure_status='metadata_only_inspected',exclusion_reason='unlabeled_rights_AI_unresolved_overlap_and_body_audit_pending')
    output.append(r)
    csv_file(OUT/'split_manifest.csv',output)
    policy={'version':version,'frozen_at':now(),'status':'development_and_reservation_only',
        'stage_04_gate_sha256':sha(OUT/'stage_reviews/stage_04_final.json'),
        'split_definitions':{'adaptation':'Existing guide/registry development inputs and agent drafts; not independent evaluation',
            'reserved_unlabeled':'Metadata inspected; no labels or certified test eligibility'},
        'counts':{'rows':43,'annotation_items':39,'source_numeric_claims':33,'reporting_relations':6,'documents':4,
            'adaptation_rows':42,'reserved_rows':1,'adaptation_documents':3,'reserved_documents':1,
            'labeled_development_families':2,'reserved_unlabeled_families':1,'human_gold':0,
            'train_items':0,'dev_items':0,'test_items':0},
        'development_leakage_group':group,'reserved_leakage_group':'PENDING-US-MSFT-FY2026-Q1',
        'reserved_group_status':'provisional_not_proof_of_independence',
        'chronology':{'development_release_dates':['2024-07-30','2025-07-30'],
            'candidate_boundary_after':'2025-07-30','candidate_published_date':'2025-10-29','date_precision':'date',
            'train_dev_test_boundaries':None,'reason':'Only two exposed release families and zero independent gold; no evaluation split allocated',
            'date_only_rule':'No invented midnight; same-day exact as-of availability remains unknown'},
        'dependency_policy':{'representation_overlap':'All three cross-presentation edges retained inside one adaptation group',
            'retrospective_scope_dependency':'All 24 scope edges recorded; support publication unknown and excluded from 2024/2025 historical evidence',
            'guide_exposure':'All annotations disclose retrospective_cutoff_simulation and guide_contains_post_cutoff_context'},
        'support_document':{'doc_id':'US-MSFT-ANNUAL-FY2025-SCOPE-REFERENCE','published_date':None,
            'time_precision':'unknown','observed_at':by_doc['US-MSFT-ANNUAL-FY2025-SCOPE-REFERENCE']['observed_at'],
            'historical_eligible':False,'event_family_id':None,'event_quota':0},
        'reserved_document':{'doc_id':reserved['doc_id'],'labels_created':False,'test_eligible':False,
            'source_prose_exposed':False,'numeric_values_exposed':False,'parser_adaptation_performed':False,
            'untouched_test_claimed':False,'comparison_overlap_audited':False,
            'promotion_requires':['source rights for intended use','body/date/scope/numeric audit','comparison/revision/family overlap audit',
                'independent annotation and adjudication','model/policy freeze before test answers are opened'],
            'summary_sha256':sha(OUT/'source_reservation/reservation_summary.json')},
        'answer_access':'No test answers exist. Reserved content separation is procedural and gitignored, not OS-enforced ACL.',
        'legacy_korean_inputs':[],'permitted_handoff':'adaptation_only_no_benchmark_claim'}
    json_file(OUT/'split_policy.json',policy)
    json_file(OUT/'stage_reviews/stage_05_initial.json',{'stage':5,'created_at':now(),
        'status':'awaiting_independent_split_and_package_validation','counts':policy['counts']})
    print(json.dumps(policy['counts']))

if __name__=='__main__':main()
