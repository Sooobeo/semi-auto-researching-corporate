# P04 contract migration

P02 v0.1 schema hash `a738b85f769df93e267c94cdf2b8d70f3fb811ba72455ce32eddc1ceb81aa2f3` is preserved. P04 `1.0.0-agent-pilot` retains raw/normalized/assessment/derived and adds explicit source hash, source record reference, guide version, false human_gold, definition_version and availability dependencies. reports_segment is a directed company → reported segment relation with fixed roles.

33 numeric source claims produce 33 event_claim records. Six reporting relations reference six of those same claim IDs and produce six distinct business_relation records. Thus records=39, unique source claims=33, families/events=2; record_id is the primary key, never claim_id alone.

Original values, signs and source scale are retained. Normalized monetary values use base USD scale=1. Derived calculation records disclose exact scale/sign conversion and prior model output exposure. Balance observations use as_of_date and null duration; source duration zero is not a zero-day flow. Evidence offsets are original DOM-cell Unicode code points, 0-based [start,end), with independent period/year/unit/row-header references.

Publication dates remain date-only, published_at/available_at/timezone/UTC offset are null. source publication refs use manifest locations; no exact time is invented. Annual-report scope support has only 2026 observation availability, recorded separately from release publication. The mapper assessment is current-as-of. Release-cutoff judgments must exclude that supplemental support.

P03 relation effective_period merely copied the financial reporting period. P04 moves it to temporal.reference_period and preserves the original in raw.source_effective_period. Effective business period, valid_from and valid_to remain unknown/not_disclosed. Reports_segment cannot establish business-effect magnitude, customer/supply relationships or segment policy details.

source_packets contains selected raw numeric/period/year/unit/standard-label references, with no mapped normalized answers. annotation_reference supplies common ID and calendar rules. These are existing adaptation documents, not blind test sources. Reserved FY2026 Q1 content is never read by this builder.

All 39 records are agent_draft; independent human annotation, human gold and full-body audit remain absent. Outputs are exclusively created; rerun into a fresh --output-dir.
