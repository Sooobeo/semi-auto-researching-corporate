// Verify publication universe, references, null states, mode denominators and safe assets.
import {readFileSync,existsSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import assert from 'node:assert/strict';
const root=fileURLToPath(new URL('./dist/',import.meta.url));
const data=JSON.parse(readFileSync(root+'phases.json','utf8'));
const html=readFileSync(root+'index.html','utf8'),js=readFileSync(root+'phases.js','utf8');
assert.equal(data.schema_version,'p06-p07-site-0.1');
assert.equal(data.sharing.source_prose_included,false);assert.equal(data.sharing.private_paths_included,false);
const ids=new Set(data.facts.map(f=>f.record_id));assert.equal(ids.size,data.facts.length);
assert.equal(data.facts.length,data.summary.P06.candidate_count);
assert.deepEqual(new Set(data.review.map(r=>r.record_id)),ids);assert.equal(data.review.length,ids.size);
assert.deepEqual(new Set(data.chronological_order),ids);
assert(data.review.every(r=>r.review_readiness==='needs_review'&&r.materiality_label===null&&r.materiality_score===null&&r.probability===null));
const decimal=v=>v===null||typeof v==='string'&&/^-?\d+(?:\.\d+)?$/.test(v);
for(const f of data.facts){assert(decimal(f.normalized.numeric_value));assert(f.normalized.scale==='1'||f.normalized.scale===null);assert.equal(f.published_at,null);assert(f.source_url.startsWith('https://www.microsoft.com/'));}
for(const c of data.changes){assert(ids.has(c.new_record_id));assert(c.prior_record_id===null||ids.has(c.prior_record_id));assert(decimal(c.delta)&&decimal(c.relative_delta));if(c.status!=='computed')assert(c.delta===null&&c.relative_delta===null);if(c.comparison_basis==='relation_state')assert(c.delta===null&&c.relative_delta===null);}
for(const c of data.calculations){assert(c.input_refs.every(id=>ids.has(id)));assert(decimal(c.output));if(c.status!=='computed')assert.equal(c.output,null);}
for(const [mode,s] of Object.entries(data.summary.P07.modes)){
  const changes=data.changes.filter(c=>c.cutoff_mode===mode),calcs=data.calculations.filter(c=>c.cutoff_mode===mode);
  assert.equal(changes.length,s.changes);assert.equal(changes.filter(c=>c.status==='computed').length,s.computed_changes);
  assert.equal(calcs.length,s.formula_attempts);assert.equal(calcs.filter(c=>c.status==='computed').length,s.formula_computed);
}
assert.equal(data.summary.P07.human_qrels,0);assert.equal(data.summary.P07.recall_at_k,null);assert.equal(data.summary.P07.change_accuracy,null);
assert(data.scenarios.every(c=>c.output===null&&c.status==='insufficient_inputs'));assert.equal(data.reconciliation_summary.complete,0);
for(const name of ['phases.js','phases.json','phase-schema.json'])assert(existsSync(root+name));
for(const name of ['review','changes','calculations'])assert(html.includes(`id="${name}-view"`));
assert(!/localStorage|sessionStorage/.test(js));assert(js.includes('BigInt('));
const text=JSON.stringify(data);assert(!/private[\\/]|password|api_key|bearer_token|raw_html|<html/i.test(text));
assert(!Object.keys(data).some(k=>['raw','source_prose','private_path','token'].includes(k)));
console.log(JSON.stringify({status:'passed',facts:ids.size,review:data.review.length,changes:data.changes.length,calculations:data.calculations.length,independent_test:0,browser_qa:'not_performed_by_static_check'}));
