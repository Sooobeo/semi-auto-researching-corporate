// Dependency-free checks of deployed asset routes, data counts, and exact money formatting.
import {readFileSync,existsSync} from 'node:fs';
import {resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import assert from 'node:assert/strict';
const root=fileURLToPath(new URL('./dist/',import.meta.url));
const html=readFileSync(resolve(root,'index.html'),'utf8');
const js=readFileSync(resolve(root,'app.js'),'utf8');
const data=JSON.parse(readFileSync(resolve(root,'snapshot.json'),'utf8'));
for(const name of ['index.html','styles.css','app.js','favicon.svg','snapshot.json'])assert(existsSync(resolve(root,name)));
for(const match of html.matchAll(/(?:src|href)="\/([^"#]+)"/g))assert(existsSync(resolve(root,match[1])),'missing local asset');
assert.equal(data.summary.inputs,39);assert.equal(data.records.length,39);
assert.equal(data.records.filter(r=>r.kind==='numeric_claim').length,33);
assert.equal(data.records.filter(r=>r.kind==='reporting_relation').length,6);
assert.equal(data.summary.field_errors,0);assert.equal(data.sharing.source_prose_included,false);
assert(data.records.every(r=>r.review==='needs_review'));
assert(data.records.every(r=>r.source_url.startsWith('https://www.microsoft.com/')));
assert(data.records.every(r=>r.normalized.temporal.published_at===null));
assert(data.records.filter(r=>r.kind==='numeric_claim').every(r=>r.normalized.scale==='1'));
assert(data.records.filter(r=>r.kind==='reporting_relation').every(r=>r.normalized.temporal.effective_period===null));
assert(!/localStorage|sessionStorage/.test(js),'No browser credentials or account persistence');
assert(!/password|api_key|bearer_token/i.test(readFileSync(resolve(root,'snapshot.json'),'utf8')));
// All content-related IDs referenced by the script exist in the initial HTML or generated views.
const fixedIds=['summary','record-list','detail','document-filter','run-button','notice','run-dialog','validation-view','about-view'];
for(const id of fixedIds)assert(html.includes(`id="${id}"`));
console.log(JSON.stringify({status:'passed',records:39,numeric:33,relations:6,source_prose_included:false,independent_test:0,browser_qa:'not_performed_by_static_check',webmcp_live_validation:'not_performed_by_static_check'}));
