'use strict';
const $ = id => document.getElementById(id);
const escapeHTML = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const metrics = {revenue:'매출',operating_income:'영업이익',net_income:'순이익',cfo:'영업활동 현금흐름',positive_cash_capex:'현금 설비투자',total_assets:'총자산',cash_and_equivalents:'현금 및 현금성 자산'};
const scopes = {'US-MSFT-CONSOLIDATED':'전사 · 연결','US-MSFT-SEG-PBP':'Productivity and Business Processes','US-MSFT-SEG-IC':'Intelligent Cloud','US-MSFT-SEG-MPC':'More Personal Computing'};
const evidenceNames = {numeric_value:'원문 숫자',row_label:'항목 이름',period_header:'기간 머리글',year_header:'연도 머리글',unit:'단위 머리글'};
const checks = {input_sources:'입력과 원문 위치 연결',unique_results:'처리 결과 중복 없음',all_inputs_have_terminal_result:'모든 입력의 처리 결과 보존',unique_predictions:'추출 후보 중복 없음',predictions_reference_known_inputs:'후보와 입력 연결',terminal_status_valid:'처리 상태 형식',terminal_prediction_links:'처리 결과와 후보 연결',predicted_result_has_candidate:'성공 결과의 후보 존재',candidate_status_matches_result:'후보와 처리 상태 일치',no_candidate_validation_errors:'후보 검증 오류 없음'};
const state = {data:null,kind:'all',doc:'all',selected:null,view:'results',running:false};

function exact(value) {
  if(value === null || value === undefined) return '알 수 없음';
  const [integer, decimal] = String(value).split('.');
  return integer.replace(/\B(?=(\d{3})+(?!\d))/g,',') + (decimal ? '.'+decimal : '');
}
function eok(value) {
  if(value == null) return '알 수 없음';
  if(!/^-?\d+$/.test(String(value))) return exact(value);
  const n=BigInt(value), negative=n<0n, a=negative?-n:n;
  const whole=a/100000000n, hundredths=(a%100000000n)/1000000n;
  return (negative?'−':'')+exact(whole.toString())+(hundredths?'.'+hundredths.toString().padStart(2,'0'):'');
}
function periodLabel(p) {return p.period_kind==='instant'?p.as_of_date:`FY${p.fiscal_year} ${p.period_kind==='quarter'?'Q'+p.fiscal_quarter:'연간'}`;}
function periodDetail(p) {return p.period_kind==='instant'?p.as_of_date:`${p.period_start} ~ ${p.period_end}`;}
function displayDate(value) {return new Intl.DateTimeFormat('ko-KR',{timeZone:'Asia/Seoul',year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',hour12:false}).format(new Date(value));}
function title(r) {return r.kind==='reporting_relation'?'사업부 보고 관계':metrics[r.normalized.metric_id]||r.raw.row_label;}
function filtered() {return state.data.records.filter(r=>(state.kind==='all'||r.kind===state.kind)&&(state.doc==='all'||r.doc_id===state.doc));}
function badge(r) {return r.comparison?.matched?'<span class="matched">일치</span>':'<span class="unmatched">검토 필요</span>';}
function notice(message,error=false) {$('notice').textContent=message;$('notice').classList.toggle('error',error);$('notice').hidden=false;}

async function load() {
  try {
    let data;
    // Hosted and local views use identical factual data. The hosted view has no execution endpoint.
    if(['127.0.0.1','localhost'].includes(location.hostname)) {
      try {const response=await fetch('/api/state',{cache:'no-store'});if(response.ok)data=await response.json();} catch {}
    }
    if(!data){const response=await fetch('/snapshot.json',{cache:'no-store'});if(!response.ok)throw new Error('결과 파일을 불러오지 못했습니다.');data=await response.json();}
    if(!Array.isArray(data.records)||!data.summary)throw new Error('결과 파일 형식을 확인해 주세요.');
    state.data=data;
    if(!state.selected||!data.records.some(r=>r.id===state.selected))state.selected=data.records[0]?.id;
    render();
  } catch(error) {notice(error.message||'화면을 불러오지 못했습니다. 잠시 후 새로고침해 주세요.',true);}
}
function render() {
  const d=state.data,s=d.summary;
  $('nav-count').textContent=s.candidates;$('version').textContent=d.rule_version;
  $('mode').textContent=d.local?.enabled?'내 PC · 실행 가능':'팀 공유 · 결과 보기';
  $('run-button').textContent=d.local?.enabled?'P05 추출 재실행':'실행 방법';
  $('run-label').textContent=`${d.run_id} · ${displayDate(d.completed_at)} 기준`;
  $('summary').innerHTML=[
    ['처리한 입력',s.inputs,'개',`${s.documents}개 발표 · ${s.families}개 발표 묶음`,'▦',false],
    ['숫자 후보',s.numeric,'개','값 · 단위 · 기간 · 사업 범위','₋',false],
    ['사업부 관계',s.relations,'개','회사 → 보고 사업부','↔',false],
    ['개발 참조 일치',s.matched,`/ ${s.references}`,'독립 성능 평가는 미측정','✓',true]
  ].map(([label,n,unit,foot,icon,focus])=>`<article class="stat-card ${focus?'focus-card':''}"><span class="stat-label">${label}</span><span class="stat-icon" aria-hidden="true">${icon}</span><div class="stat-number">${n}<small>${unit}</small></div><div class="stat-foot">${foot}</div></article>`).join('');
  $('document-filter').innerHTML='<option value="all">모든 발표</option>'+d.documents.map(doc=>`<option value="${escapeHTML(doc.id)}">${escapeHTML(doc.label)}</option>`).join('');
  $('document-filter').value=state.doc;renderList();renderDetail();renderValidation();renderAbout();
  if(window.renderPhaseReports)window.renderPhaseReports(state.view);
}
function renderList() {
  const records=filtered();$('filtered-count').textContent=records.length;
  $('list-footer').textContent=`${records.length}개 표시 / 전체 ${state.data.summary.candidates}개`;
  if(!records.some(r=>r.id===state.selected))state.selected=records[0]?.id||null;
  $('record-list').innerHTML=records.length?records.map(r=>{
    const n=r.normalized,p=n.temporal.reference_period;
    const scope=scopes[n.scope_id]||n.scope_id;
    const amount=r.kind==='reporting_relation'?'<span class="secondary">보고 관계</span>':`${eok(n.numeric_value)} <small>억 USD</small>`;
    return `<tr class="result-row ${r.id===state.selected?'selected':''}" data-record="${escapeHTML(r.id)}"><td><button class="record-button" aria-label="${escapeHTML(title(r)+' '+scope+' '+periodLabel(p)+' 상세 보기')}"><strong>${escapeHTML(title(r))}</strong><span class="row-sub">${escapeHTML(scope)}</span></button></td><td><span class="period">${escapeHTML(periodLabel(p))}</span><span class="row-sub">${r.doc_id==='US-MSFT-FY2024-Q4-RELEASE'?'2024 발표':'2025 발표'}</span></td><td class="amount">${amount}</td><td>${badge(r)}</td></tr>`;
  }).join(''):'<tr><td colspan="4"><div class="empty">이 조건에 해당하는 항목이 없습니다.</div></td></tr>';
  document.querySelectorAll('[data-record]').forEach(row=>row.addEventListener('click',()=>selectRecord(row.dataset.record)));
  renderDetail();
}
function selectRecord(id) {
  state.selected=id;
  document.querySelectorAll('[data-record]').forEach(row=>row.classList.toggle('selected',row.dataset.record===id));
  renderDetail();
}
function field(label,value,extra='') {return `<div class="detail-field"><dt>${label}</dt><dd>${escapeHTML(value??'알 수 없음')}${extra?'<small>'+escapeHTML(extra)+'</small>':''}</dd></div>`;}
function renderDetail() {
  const r=state.data.records.find(r=>r.id===state.selected);
  if(!r){$('detail').innerHTML='<div class="empty"><h2 id="detail-title">항목 상세</h2><p>표시된 항목이 없습니다.</p></div>';return;}
  const n=r.normalized,p=n.temporal.reference_period,relation=r.kind==='reporting_relation';
  const value=relation?`<strong class="relation-value">Microsoft <span class="relation-arrow">→</span><br>${escapeHTML(scopes[n.object_entity_id]||n.object_entity_id)}</strong>`:`<strong>${exact(n.numeric_value)}</strong>`;
  const note=relation?'이 표에서 해당 사업부를 보고했다는 뜻입니다. 실제 사업의 시작·종료 시점과 투자 영향은 별도 확인이 필요합니다.':n.sign_policy==='outflow_to_positive'?'원문의 괄호 음수는 보존하고, 현금 설비투자만 양수 지출로 변환했습니다.':n.scope_id==='US-MSFT-CONSOLIDATED'?'전사 연결 범위는 후향 참고 자료에 의존합니다. 당시 발표 시점의 근거로 소급하지 않습니다.':'사업부 표시 정의는 발표별로 유지합니다. 다른 연도와 비교하려면 정의 확인이 필요합니다.';
  const details=[field('사업 범위',scopes[n.scope_id]||n.scope_id),field('기준 기간',periodDetail(p),p.duration_days?`${p.duration_days}일 · ${p.period_kind==='quarter'?'분기 흐름':'연간 흐름'}`:p.period_kind==='instant'?'시점 잔액':''),field('발표 날짜',n.temporal.published_date,'정확 시각 미확인'),field('출처 상태',r.raw.source_qualifier==='company_reported_unaudited'?'회사 발표 · 미감사':'회사 보고 표')];
  if(!relation)details.push(field('회계기준',n.accounting_basis,'사전 제공 문맥'));
  $('detail').innerHTML=`<div class="detail-heading"><span class="detail-label">SELECTED RECORD</span><span class="review-chip">검토 필요</span><h2 id="detail-title">${escapeHTML(title(r))}</h2><p>${escapeHTML(r.raw.row_label.replace(/\s+/g,' '))}</p></div><div class="detail-value"><span class="value-label">${relation?'보고 회사와 사업부':'USD 기본 단위로 정리한 값'}</span>${value}<span class="unit-tag">${relation?'reports_segment · 회사 → 사업부':'USD · scale = 1'}</span></div><div class="details-body"><div><dl class="detail-fields">${details.join('')}</dl><div class="detail-note">${note}</div></div><section class="detail-section"><h3>원문 근거</h3><div class="evidence-list">${r.evidence.map(e=>`<div class="evidence"><span>${evidenceNames[e.kind]||escapeHTML(e.kind)}</span><code>${escapeHTML(e.selected_text)}</code><details><summary>원문 위치</summary><span class="xpath">${escapeHTML(e.location)}</span><span>Unicode code point [${e.start}, ${e.end})</span></details></div>`).join('')}</div></section><a class="source-link" href="${escapeHTML(r.source_url)}" target="_blank" rel="noopener noreferrer">Microsoft 공식 발표 열기</a><details class="detail-section"><summary class="secondary">정리 방식·참조 비교 자세히</summary><p class="secondary">시작일은 머리글의 3개월·12개월을 바탕으로 계산했습니다. 회사·사업 범위·USD·GAAP 문맥은 미리 제공되었습니다.</p><p class="secondary">표시 정의: ${escapeHTML(r.definition)}</p><p class="secondary">참조 비교: ${r.comparison?.matched?'필드 일치':'검토 필요'} · 독립 정답 평가 미실행</p><p class="secondary">원본 SHA-256</p><code class="run-meta">${escapeHTML(r.source_sha256)}</code></details></div>`;
}
function renderValidation() {
  const d=state.data,s=d.summary,totalTests=d.tests.reduce((a,t)=>a+t.total,0),passed=d.tests.reduce((a,t)=>a+t.passed,0);
  $('validation-view').innerHTML=`<div class="validation-grid"><section class="panel section-card"><div class="eyebrow">INPUT → EXTRACTION → VALIDATION</div><h2>이번 실행의 흐름</h2><p>선택한 숫자·머리글을 읽고, 추출 결과를 고정한 다음 참조 자료와 비교합니다.</p><div class="process-flow"><span>입력 ${s.inputs}개</span><span>후보 ${s.candidates}개</span><span>처리 결과 ${s.inputs}개</span><span>참조 ${s.matched}/${s.references}</span></div><div class="check-row"><span>숫자 / 사업부 관계</span><strong>${s.numeric} / ${s.relations}</strong></div><div class="check-row"><span>필드 비교 오류</span><strong>${s.field_errors}개</strong></div><div class="check-row"><span>재조회한 원문 위치</span><strong>${s.source_locations}개</strong></div><div class="check-row"><span>숫자 추출 처리시간</span><strong>${Number(s.inference_seconds).toFixed(3)}초</strong></div><p class="secondary">처리시간은 이번 작은 표본의 관측값입니다. 대량 운영 용량은 아직 측정하지 않았습니다.</p><div class="detail-section"><h3>실행 정보</h3><p class="run-meta">${escapeHTML(d.run_id)}<br>${escapeHTML(d.rule_version)}<br>${displayDate(d.completed_at)} KST</p></div></section><section class="panel section-card"><div class="eyebrow">CONTRACT CHECKS</div><h2>검증 결과 ${s.validation_passed}/${s.validation_total}</h2><p>형식·근거·단위·기간을 확인한 개발 검사입니다.</p>${Object.entries(d.validation.checks).map(([key,passed])=>`<div class="check-row"><span>${escapeHTML(checks[key]||key)}</span><span class="${passed?'check-result':'check-error'}">${passed?'통과':'검토 필요'}</span></div>`).join('')}</section><section class="panel section-card"><div class="eyebrow">SYNTHETIC CASES</div><h2>오류 상황 검사 ${passed}/${totalTests}</h2><p>잘못된 단위, 뒤바뀐 기간, 누락·중복·값 변조 등을 넣어 확인했습니다. 실제 문서 표본과는 별도입니다.</p>${d.tests.map(t=>`<div class="check-row"><span>${escapeHTML(t.label)}</span><strong>${t.passed}/${t.total}</strong></div><div class="test-bar"><i style="width:${t.total?t.passed/t.total*100:0}%"></i></div>`).join('')}</section><section class="panel section-card"><div class="eyebrow">REVIEW QUEUE</div><h2>처리 상태</h2>${Object.entries(s.statuses).map(([k,v])=>`<div class="check-row"><span>${escapeHTML({predicted:'후보 생성',abstained:'판단 보류',failed:'실행 실패',quarantined:'검증 격리'}[k]||k)}</span><strong>${v}개</strong></div>`).join('')}<p>파싱이 성공해도 모든 후보는 검토 필요 상태입니다. 중요성이나 실적 전망은 별도 단계에서 검토합니다.</p></section></div>`;
}
function renderAbout() {
  const d=state.data;
  $('about-view').innerHTML=`<div class="scope-grid"><section class="panel scope-card"><div class="eyebrow">WHAT YOU ARE LOOKING AT</div><h2>P05는 무엇을 하나요?</h2><p>기업 실적표의 숫자와 사업부 이름을 읽어, 값·단위·기준 기간·사업 범위·원문 위치를 구조화하는 첫 프로그램입니다.</p><p>예를 들어 <strong>64,727 × 백만 달러</strong>는 <strong>64,727,000,000 USD</strong>로 정리합니다. 어느 기간의 어떤 지표인지도 함께 남깁니다.</p><p>원문, 구조화한 값, 검토 상태, 계산 결과를 구분합니다. 회사 발표 주장은 외부에서 사실을 검증한 상태와 다릅니다.</p></section><section class="panel scope-card"><div class="eyebrow">CURRENT DATA</div><h2>현재 자료 범위</h2>${d.documents.map(doc=>`<div class="check-row"><span>${escapeHTML(doc.label)}<br><small class="secondary">발표 ${doc.published_date}</small></span><strong>${doc.count}개</strong></div>`).join('')}<p>사업부 관계 6개는 숫자 근거 일부를 함께 사용합니다. 같은 근거를 독립된 실적 관측으로 중복 계산하지 않습니다.</p><p>2025 발표의 2024 비교열은 2025 발표의 표시 정의를 유지합니다.</p></section>${d.limitations.map(l=>`<section class="panel scope-card"><div class="eyebrow">NEEDS REVIEW</div><h2>${escapeHTML(l.label)}</h2><p>${escapeHTML(l.detail)}</p></section>`).join('')}<section class="panel scope-card"><div class="eyebrow">NEXT STEPS</div><h2>다음 단계</h2><p>기존 실적과 새 발표의 비교, 사업부 정의 확인, 근거를 연결한 검토 카드로 확장할 수 있습니다. 실제 성능 평가에는 독립적인 사람 정답과 새로운 문서가 필요합니다.</p></section><section class="panel scope-card"><div class="eyebrow">SHARED VIEW</div><h2>공유한 내용</h2><p>최소 숫자·표준 라벨·기간·위치와 개발 결과를 보여줍니다. 출처 조건은 2026-10-05 확인한 기존 사실 참조 범위를 따릅니다.</p><p>공유 화면은 게시된 실행 결과입니다. 새 로컬 실행 결과를 팀 화면에 반영하려면 결과를 내보내고 다시 게시해야 합니다.</p></section></div>`;
}
function switchView(view) {
  const views=['review','changes','calculations','results','validation','about'];
  if(!views.includes(view))throw new Error('지원하지 않는 화면입니다.');
  state.view=view;views.forEach(name=>$(name+'-view').hidden=name!==view);
  document.querySelectorAll('[data-view]').forEach(b=>b.classList.toggle('active',b.dataset.view===view));
  $('page-title').textContent={review:'검토할 항목',changes:'이전 정보와 비교',calculations:'재무 계산',results:'실적 추출 결과',validation:'실행·검증',about:'범위와 남은 일'}[view];
  $('page-subtitle').textContent={review:'확인이 필요한 이유와 다음에 볼 근거를 살펴보세요.',changes:'시점과 정의가 맞는 값만 비교하고, 보류 이유를 함께 확인하세요.',calculations:'입력·기간·사업 범위가 맞는 공식만 계산합니다.',results:'표에 적힌 숫자가 무엇을 뜻하는지, 어디에서 왔는지 확인하세요.',validation:'입력부터 참조 비교까지, 이번 실행의 과정을 확인하세요.',about:'현재 확인한 내용과 추가 검토가 필요한 부분을 구분합니다.'}[view];
  if(window.renderPhaseReports)window.renderPhaseReports(view);
}
async function startRun() {
  if(!state.data?.local?.enabled){$('run-dialog').showModal();return;}
  if(state.running)return;
  state.running=true;$('run-button').disabled=true;$('run-button').textContent='실행 중…';
  try {
    const response=await fetch('/api/run',{method:'POST',headers:{'X-P05-Token':state.data.local.token}});
    const body=await response.json();if(!response.ok)throw new Error(body.error||'실행을 시작하지 못했습니다.');
    let job;
    do {
      await new Promise(resolve=>setTimeout(resolve,650));
      const status=await fetch('/api/job',{cache:'no-store'});if(!status.ok)throw new Error('실행 상태를 확인하지 못했습니다.');job=await status.json();
      notice({starting:'새 실행을 준비하고 있습니다.',extract:'숫자와 사업부 관계를 추출하고 있습니다.',validate:'원문 근거와 추출 결과를 검증하고 있습니다.',compare:'고정한 결과를 기존 참조와 비교하고 있습니다.',done:'새 실행이 완료되었습니다.'}[job.stage]||'실행 중입니다.');
    } while(job.busy);
    if(job.error)throw new Error('실행을 완료하지 못했습니다: '+job.error);
    await load();notice('새 실행이 완료되었습니다. 이 화면에 최신 로컬 결과를 반영했습니다.');
    return {run_id:state.data.run_id,inputs:state.data.summary.inputs,candidates:state.data.summary.candidates};
  } catch(error){notice(error.message,true);throw error;}
  finally{state.running=false;$('run-button').disabled=false;$('run-button').textContent=state.data?.local?.enabled?'P05 추출 재실행':'실행 방법';}
}
document.querySelectorAll('[data-view]').forEach(b=>b.addEventListener('click',()=>switchView(b.dataset.view)));
document.querySelectorAll('[data-kind]').forEach(b=>b.addEventListener('click',()=>{state.kind=b.dataset.kind;document.querySelectorAll('[data-kind]').forEach(t=>t.classList.toggle('selected',t===b));renderList();}));
$('document-filter').addEventListener('change',e=>{state.doc=e.target.value;renderList();});
$('run-button').addEventListener('click',()=>startRun().catch(()=>{}));
$('close-dialog').addEventListener('click',()=>$('run-dialog').close());$('dialog-done').addEventListener('click',()=>$('run-dialog').close());
load().then(()=>{
  if(!document.modelContext?.registerTool||!state.data)return;
  const life=new AbortController();window.addEventListener('pagehide',()=>life.abort(),{once:true});
  const register=tool=>{try{Promise.resolve(document.modelContext.registerTool(tool,{signal:life.signal})).catch(()=>{});}catch{}};
  register({name:'read_p05_summary',title:'P05 결과 요약',description:'현재 표시한 P05 실행의 처리 개수와 미측정 항목을 읽습니다.',inputSchema:{type:'object',properties:{},additionalProperties:false},annotations:{readOnlyHint:true},execute(input){if(!input||Object.keys(input).length)throw new Error('입력 필드가 없어야 합니다.');return {run_id:state.data.run_id,...state.data.summary};}});
  register({name:'show_p05_record',title:'추출 항목 보기',description:'현재 결과의 항목을 선택하고 근거를 표시합니다.',inputSchema:{type:'object',properties:{id:{type:'string'}},required:['id'],additionalProperties:false},annotations:{readOnlyHint:true},execute(input){if(!input||Object.keys(input).length!==1||typeof input.id!=='string')throw new Error('항목 ID가 필요합니다.');const r=state.data.records.find(r=>r.id===input.id);if(!r)throw new Error('찾을 수 없는 항목입니다.');state.kind='all';state.doc='all';$('document-filter').value='all';document.querySelectorAll('[data-kind]').forEach(b=>b.classList.toggle('selected',b.dataset.kind==='all'));state.selected=r.id;switchView('results');renderList();return {id:r.id,title:title(r),review:r.review,evidence_count:r.evidence.length};}});
  if(state.data.local?.enabled)register({name:'run_p05_local',title:'로컬 P05 다시 실행',description:'이 PC에서 고정된 P05 표본을 실제로 재실행하고 화면을 갱신합니다. 새 실행 파일을 저장합니다.',inputSchema:{type:'object',properties:{},additionalProperties:false},annotations:{readOnlyHint:false},execute(input){if(!input||Object.keys(input).length)throw new Error('입력 필드가 없어야 합니다.');return startRun();}});
});
