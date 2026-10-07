// P08/P09 data contract and safe UI checks; these are not a browser usability study.
import {readFileSync,existsSync} from 'node:fs';
import assert from 'node:assert/strict';
import {fileURLToPath} from 'node:url';
const root=fileURLToPath(new URL('./dist/',import.meta.url));
const d=JSON.parse(readFileSync(root+'integration.json','utf8'));
const js=readFileSync(root+'integration.js','utf8'),html=readFileSync(root+'index.html','utf8');
assert.equal(d.schema_version,'p08-p09-site-0.1');assert.equal(d.P08.summary.candidates,39);assert.equal(d.P08.cards.length,33);
assert.equal(new Set(d.P08.cards.flatMap(c=>c.candidate_refs)).size,39);
assert(d.P08.cards.every(c=>c.review_readiness==='needs_review'&&c.human_gold===false));
assert(d.P09.independent_metrics.every(m=>m.value===null&&m.denominator===0));
assert.equal(d.P09.cost.observed_operating_cost,null);assert.equal(d.P09.cost.cost_per_1000_documents,null);
assert.equal(d.P09.summary.actual_participants,0);
assert.deepEqual(d.P09.systems.filter(s=>s.status==='executed_development').map(s=>s.system),['S0','S1','S3']);
assert(d.P09.systems.filter(s=>s.status==='not_evaluated').every(s=>s.records===null&&s.materialization_seconds===null));
assert(d.P08.pipeline.stages.every(s=>s.counts.input===s.counts.normal+s.counts.failed+s.counts.held));
assert.equal(d.P09.failure_cases.length,d.P09.withheld_change_count+d.P09.withheld_calculation_count);
for(const id of ['card-summary','card-list','card-detail','card-date','card-mode','pipeline-list','feedback-import','feedback-export','evaluation-systems','evaluation-failures','failure-stage'])assert(html.includes(`id="${id}"`));
for(const m of html.matchAll(/(?:src|href)="\/([^"#]+)"/g))assert(existsSync(root+m[1]));
assert(!/eval\(|new Function|innerHTML\s*=\s*(?:payload|event|e\.(?:after|before|rationale))(?:[;\s]|$)/.test(js));
assert(js.includes('esc(JSON.stringify(e.after))'));
assert(!/private[/\\]|(?:^|["\s])[A-Z]:[\\/]|api_key|password|bearer_token|<script|actor_id|owner_id/i.test(JSON.stringify(d)));
assert.equal(d.sharing.automatic_shared_save,false);
assert(js.includes('공유 반영은 소유자 가져오기·재게시 후 완료됩니다.'));
assert(js.includes('조건에 맞는 카드가 없습니다.'));
console.log(JSON.stringify({status:'passed',cards:d.P08.cards.length,candidates:d.P08.summary.candidates,
  systems:3,independent_metrics:'not_evaluated',browser_qa:'separate',failure_cases:d.P09.failure_cases.length}));
