'use strict';
(() => {
  let data=null, facts=new Map(), reviewId=null, changeId=null, calcId=null;
  const esc=escapeHTML;
  const groups={scope_availability:'발표 당시 범위 근거',segment_definition:'사업부 표시 정의',relation_validity:'관계 유효기간',evidence_review:'근거 확인'};
  const basisNames={yoy:'전년 대비',same_period_revision:'동일 기간 수정 차이 · 정정 미확인',within_release_comparison:'해당 발표의 비교열',relation_state:'보고 관계 상태',prior_search:'이전 정보 미확인'};
  const reasonNames={definition_version_mismatch:'표시 정의가 다릅니다.',actual_relation_validity_unknown:'관계 실제 유효기간은 미확인입니다.',scope_unresolved_at_cutoff:'당시 사업 범위 근거가 미확인입니다.',current_only_dependency:'사후 참고자료를 과거 정보로 사용할 수 없습니다.',publication_unknown:'공개시점 근거가 없습니다.',same_day_order_unknown:'날짜만 있어 같은 날 순서를 알 수 없습니다.',future_information:'기준 시점 뒤의 정보입니다.',query_unavailable:'새 항목의 당시 문맥이 충분하지 않습니다.',all_candidates_incompatible:'이전 후보의 비교 조건이 맞지 않습니다.',all_candidates_time_excluded:'제한 corpus의 이전 후보가 시점 검사에서 제외됐습니다.',no_hit_in_limited_corpus:'제한 corpus 안에서 이전 후보를 찾지 못했습니다.',zero_denominator:'이전 값이 0이어서 상대 변화율을 계산하지 않았습니다.',prior_not_available:'이전 값이 미확인입니다.',same_release_not_independent_prior:'현재 발표의 비교열은 과거 독립 발표로 선택하지 않습니다.',actual_period_mismatch:'실제 대상 기간이 다릅니다.',nonactual_numeric_comparison_not_supported:'계획·전망을 실적 변화로 계산하지 않습니다.'};
  const fieldNames={company_id:'기업',scope_id:'사업 범위',definition_version:'표시 정의',modality:'실적/계획 상태',metric_id:'지표',accounting_basis:'회계기준',currency:'통화',canonical_unit:'단위',scale:'기본 배율',balance_or_flow:'잔액/흐름',statement_type:'재무제표',consolidation:'연결 범위',sign_policy:'부호',period_kind:'기간 종류',period_basis:'회계 기간',actual_period_alignment:'실제 기간 대응',fiscal_quarter:'회계분기',relation_type:'관계 종류',subject_entity_id:'관계 주체',object_entity_id:'관계 대상',direction:'관계 방향',subject_role:'주체 역할',object_role:'대상 역할',negation:'부정',conditions:'조건',actual_validity_known:'실제 유효기간 확인'};
  const reason = code => {
    if(!code)return '해당 없음';
    if(code.startsWith('dependency:'))return '필요 문맥: '+reason(code.slice(11));
    if(code.startsWith('observed:'))return '시스템 관측: '+reason(code.slice(9));
    if(reasonNames[code])return reasonNames[code];
    const field=code.replace(/_(mismatch|unknown|mismatch_or_unknown)$/,'');
    return fieldNames[field]?fieldNames[field]+' 조건을 확인해야 합니다.':code;
  };
  const factTitle = r => r.kind==='business_relation'?'사업부 보고 관계':metrics[r.normalized.metric_id]||r.normalized.metric_id;
  const factScope = r => scopes[r.normalized.scope_id]||r.normalized.scope_id;
  const factValue = r => !r?'미확인':r.kind==='business_relation'?'Microsoft → '+factScope(r):exact(r.normalized.numeric_value)+' USD';
  const factPeriod = r => periodLabel(r.period);
  const stats = entries => entries.map(([label,note,value,unit])=>`<article class="stat-card"><span class="stat-label">${esc(label)}</span><div class="stat-number">${esc(value)}<small>${esc(unit||'')}</small></div><div class="stat-foot">${esc(note)}</div></article>`).join('');
  function percent(v) {
    if(v==null)return '미측정';
    const m=String(v).match(/^(-?)(\d+)(?:\.(\d+))?$/);if(!m)return exact(v);
    const digits=(m[3]||'');let numerator=BigInt(m[2]+digits)*10000n,denominator=10n**BigInt(digits.length);
    let q=numerator/denominator,rem=numerator%denominator;
    if(rem*2n>denominator||(rem*2n===denominator&&q%2n))q+=1n;
    return (m[1]?'−':'')+(q/100n).toString()+'.'+(q%100n).toString().padStart(2,'0')+'%';
  }
  function options(id,values,label) {$(id).innerHTML='<option value="all">전체</option>'+[...new Set(values)].map(v=>`<option value="${esc(v)}">${esc(label(v))}</option>`).join('');}
  function selectionRows(body,kind,values,render,selected) {
    $(body).innerHTML=values.length?values.map(r=>`<tr class="result-row ${selected===r.id?'selected-row':''}">${render(r)}</tr>`).join(''):'<tr><td colspan="3" class="empty">조건에 맞는 항목이 없습니다.</td></tr>';
    $(body).querySelectorAll('button[data-id]').forEach(b=>b.addEventListener('click',()=>{if(kind==='review'){reviewId=b.dataset.id;renderReview();}else if(kind==='change'){changeId=b.dataset.id;renderChanges();}else{calcId=b.dataset.id;renderCalculations();}}));
  }
  const buttons=(id,heading,sub)=>`<td class="record-main"><button class="record-button" data-id="${esc(id)}"><strong>${esc(heading)}</strong><small>${esc(sub)}</small></button></td>`;
  function sourceCard(r,label) {
    if(!r)return `<section class="comparison-source"><h3>${esc(label)}</h3><p>이전 정보 미확인</p></section>`;
    return `<section class="comparison-source"><h3>${esc(label)}</h3><strong>${esc(factValue(r))}</strong><dl class="detail-fields">${field('대상 기간',periodDetail(r.period))}${field('사업 범위',factScope(r))}${field('표시 정의',r.normalized.definition_version)}${field('발표 날짜',r.published_date,'정확 시각 미확인')}${field('시스템 관측',r.observed_at)}</dl><a class="source-link" href="${esc(r.source_url)}" target="_blank" rel="noopener noreferrer">공식 발표 열기</a><details><summary>문서·revision·원문 위치</summary><p class="run-meta">${esc(r.doc_id)}<br>${esc(r.revision_id)}</p>${r.evidence.map(e=>`<p class="xpath">${esc(e.kind)} · ${esc(e.location)}<br>Unicode code point [${e.start}, ${e.end})</p>`).join('')}</details></section>`;
  }
  function renderReview() {
    if(!data)return;
    const sum=data.summary.P06;
    $('review-summary').innerHTML=stats([['검토 후보','숫자 33개 · 보고 관계 6개',sum.candidate_count,'개'],['검토 묶음','공유 근거 관계는 숫자와 연결',sum.review_groups,'개'],['독립 발표','Microsoft 실적 release 2개',sum.families,'family'],['중요성·확률','독립 사람 정답 0개','미평가','']]);
    let items=data.review.filter(r=>{const f=facts.get(r.record_id);return ($('review-date').value==='all'||r.published_date===$('review-date').value)&&($('review-scope').value==='all'||f.normalized.scope_id===$('review-scope').value)&&($('review-metric').value==='all'||(f.normalized.metric_id||f.normalized.relation_type)===$('review-metric').value)&&($('review-reason').value==='all'||r.reason_group===$('review-reason').value);});
    if($('review-order').value==='date'){const order=new Map(data.chronological_order.map((id,i)=>[id,i]));items.sort((a,b)=>order.get(a.record_id)-order.get(b.record_id));}
    $('review-count').textContent=items.length;if(!items.some(r=>r.review_item_id===reviewId))reviewId=items[0]?.review_item_id;
    selectionRows('review-list','review',items.map(r=>({...r,id:r.review_item_id})),r=>{const f=facts.get(r.record_id);return buttons(r.id,factTitle(f),factScope(f))+`<td>${esc(factPeriod(f))}<small class="cell-sub">발표 ${esc(f.published_date)}</small></td><td><span class="unmatched">${esc(groups[r.reason_group])}</span><small class="cell-sub">검토 필요${f.kind==='business_relation'?' · 공유 근거':''}</small></td>`;},reviewId);
    const r=items.find(x=>x.review_item_id===reviewId);
    if(!r){$('review-detail').innerHTML='<div class="empty">표시할 항목이 없습니다.</div>';return;}
    const f=facts.get(r.record_id);
    const missingLabels={prior:'중요성 feature의 prior',novelty:'새로움',financial_impact:'재무 영향 규모',change:'P07 변화 연결'};
    $('review-detail').innerHTML=`<div class="detail-heading"><span class="detail-label">P06 · REVIEW REASONS</span><span class="review-chip">검토 필요</span><h2>${esc(factTitle(f))}</h2><p>${esc(factScope(f))} · ${esc(factPeriod(f))}</p></div><div class="details-body"><div><strong class="phase-value">${esc(factValue(f))}</strong><h3>왜 확인해야 하나요?</h3><ul class="reason-list">${r.review_reasons.map(code=>`<li>${esc(data.reason_templates[code])}</li>`).join('')}</ul><h3>부족한 정보</h3><dl class="detail-fields">${Object.entries(r.missing_features).map(([k,v])=>field(missingLabels[k]||k,v===null?'연결됨 · 판단은 별도':v==='not_estimated'?'미측정':v==='prior_not_available'?'이 feature에서는 미확인':reason(v))).join('')}</dl><h3>다음 확인</h3><p>원문 위치와 기간을 확인하고, 사업 범위·표시 정의의 근거를 검토하세요. 비교 화면에서 이전 값과 보류 이유를 확인할 수 있습니다.</p><dl class="detail-fields">${field('검토 묶음',r.review_group_id)}${field('중요성 점수','미측정 · null')}${field('확률','미보정 · null')}${field('당시 feature 조건',r.historical_eligible?'공개된 표 문맥 후보 · 비교는 별도 검사':'사후 문맥으로 과거 사용 불가')}</dl><button class="source-link" id="review-to-extraction">원래 추출 후보와 근거 보기</button><button class="source-link" id="review-to-change">이 항목의 비교 보기</button></div></div>`;
    $('review-to-extraction').onclick=()=>{state.selected=f.prediction_id;state.kind='all';state.doc='all';$('document-filter').value='all';document.querySelectorAll('[data-kind]').forEach(b=>b.classList.toggle('selected',b.dataset.kind==='all'));renderList();switchView('results');};
    $('review-to-change').onclick=()=>{$('change-mode').value='current_review';$('change-status').value='all';$('change-scope').value='all';changeId=data.changes.find(c=>c.new_record_id===f.record_id&&c.cutoff_mode==='current_review')?.change_id;renderChanges();switchView('changes');};
  }
  function renderChanges() {
    if(!data)return;
    const mode=$('change-mode').value,s=data.summary.P07.modes[mode];
    $('change-summary').innerHTML=stats([['検索'.replace('検索','검색 시도'),'39개 항목 × 2개 방식',s.queries,'회'],['선택한 독립 prior','방식별 시도 수 · 고유 사건 수 아님',s.selected_queries,'/ '+s.queries],['계산한 변화','해당 발표 비교열 3쌍 별도 포함',s.computed_changes,'/ '+s.changes],['비교 보류','미상·정의 불일치·시점 제외',s.withheld_changes,'개']]);
    $('change-mode-note').textContent={current_review:'현재 자료로 재검토: 사후 범위 참고자료를 포함합니다. 과거 예측·검색 성과로 보고하지 않습니다.',historical_public:'당시 공개 정보 기준: 독립 이전 발표로 선택된 항목은 0개입니다. 계산 3개는 현재 발표 안의 비교열이며 독립 prior 검색 성과가 아닙니다.',observed_live:'시스템 관측 기준: 자료는 2026년에 관측했습니다. 2024·2025년 실시간 정보로 사용하지 않으며 모든 계산을 보류합니다.'}[mode];
    const items=data.changes.filter(c=>c.cutoff_mode===mode&&($('change-status').value==='all'||c.status===$('change-status').value)&&($('change-scope').value==='all'||facts.get(c.new_record_id).normalized.scope_id===$('change-scope').value));
    $('change-count').textContent=items.length;if(!items.some(c=>c.change_id===changeId))changeId=items[0]?.change_id;
    selectionRows('change-list','change',items.map(c=>({...c,id:c.change_id})),c=>{const f=facts.get(c.new_record_id);return buttons(c.id,factTitle(f),basisNames[c.comparison_basis]+' · '+factScope(f))+`<td class="phase-number">${c.old_value===null?'미확인':esc(exact(c.old_value))}<small class="cell-sub">→ ${c.new_value===null?'보고 관계':esc(exact(c.new_value))}</small></td><td>${c.status==='computed'?'<span class="matched">계산 완료</span><small class="cell-sub">Δ '+esc(exact(c.delta))+' '+esc(c.unit)+'</small>':'<span class="unmatched">보류</span>'}</td>`;},changeId);
    const c=items.find(x=>x.change_id===changeId);
    if(!c){$('change-detail').innerHTML='<div class="empty">표시할 비교가 없습니다.</div>';return;}
    $('change-detail').innerHTML=`<div class="detail-heading"><span class="detail-label">P07 · ${esc(c.cutoff_mode)}</span><span class="review-chip">검토 필요</span><h2>${esc(basisNames[c.comparison_basis])}</h2><p>기준 시점 ${esc(c.cutoff)} · ${c.compatibility.decision==='comparable'?'조건 호환':c.compatibility.decision==='not_comparable'?'비교 불가':'조건 미확인'}</p></div><div class="phase-details"><div class="comparison-pair">${sourceCard(facts.get(c.prior_record_id),'이전 정보')}${sourceCard(facts.get(c.new_record_id),'새 정보')}</div><section class="detail-section"><h3>무엇이 바뀌었나요?</h3>${c.status==='computed'?`<strong class="phase-value">Δ ${esc(exact(c.delta))} ${esc(c.unit)}</strong><p>상대 변화: ${esc(percent(c.relative_delta))}</p><details><summary>정확한 Decimal 값·공식</summary><p class="run-meta">${esc(c.relative_delta??'null')}<br>delta = new − old<br>relative = delta / abs(old) · fraction<br>표시 비율: 소수 2자리 HALF_EVEN</p></details>`:'<p>숫자 결과 null · 계산 보류</p>'}<ul class="reason-list">${c.reasons.map(r=>`<li>${esc(reason(r))}</li>`).join('')}${c.relative_delta_missing_reason?'<li>'+esc(reason(c.relative_delta_missing_reason))+'</li>':''}</ul>${c.interpretation==='negative_base_or_loss_transition'?'<p>음수 기준 또는 손익 전환입니다. 일반 성장률 해석을 적용하지 않습니다.</p>':''}<p class="secondary">당시 비교 적합: ${c.historical_eligible?'조건 충족 후보':'미확인/부적합'} · 회사 보고 주장 · 독립 사실 확인 미실행</p></section><details class="detail-section"><summary>비교 조건·입력 ID</summary>${Object.entries(c.compatibility.checks).map(([k,v])=>`<div class="check-row"><span>${esc(fieldNames[k]||k)}</span><strong>${v===null?'미상':v?'일치/확인':'불일치/미확인'}</strong></div>`).join('')}<p class="run-meta">${esc(c.source_record_refs.join('\n'))}<br>${esc(c.formula_id??'관계는 숫자 공식 없음')}</p></details></div>`;
  }
  function renderCalculations() {
    if(!data)return;
    const mode=$('calc-mode').value,items=data.calculations.filter(c=>c.cutoff_mode===mode);
    $('calc-summary').innerHTML=stats([['공식 계산','기간·scope·단위·입력 검사',items.filter(c=>c.status==='computed').length,'/ '+items.length],['완전 대사','조정 항목이 부족해 incomplete',0,'/ '+data.reconciliation_summary.attempts],['전망 scenario','입력과 사람 가정 미제공',0,'/ 1'],['독립 평가','사람 정답·독립 test 0개','미실행','']]);
    if(!items.some(c=>c.calculation_id===calcId))calcId=items[0]?.calculation_id;
    const fname=c=>c.formula_id==='operating_margin'?'프로젝트 영업이익률':'프로젝트 FCF';
    selectionRows('calc-list','calc',items.map(c=>({...c,id:c.calculation_id})),c=>buttons(c.id,fname(c),factPeriod(facts.get(c.input_refs[0])))+`<td class="phase-number">${c.output===null?'미계산':esc(c.output_unit==='fraction'?percent(c.output):exact(c.output)+' USD')}</td><td><span class="${c.status==='computed'?'matched':'unmatched'}">${c.status==='computed'?'계산 완료':'보류'}</span></td>`,calcId);
    $('scenario-state').innerHTML='<h3>계산을 중단한 항목</h3><p>순이익 → CFO 대사: 비현금·운전자본 조정과 보고 target 감사가 부족합니다. 잔차는 null입니다.</p><p>매출 scenario: 출하량·ASP·미래 기간·사업 범위·통화·검토된 사람 가정이 없습니다. 계산 0/1건, output=null.</p>';
    const c=items.find(x=>x.calculation_id===calcId);if(!c){$('calc-detail').innerHTML='<div class="empty">계산 없음</div>';return;}
    $('calc-detail').innerHTML=`<div class="detail-heading"><span class="detail-label">P07 · FINANCIAL FORMULA</span><span class="review-chip">검토 필요</span><h2>${esc(fname(c))}</h2><p>기준 시점 ${esc(c.cutoff)} · ${esc(c.cutoff_mode)}</p></div><div class="phase-details"><p class="formula-display">${c.formula_id==='operating_margin'?'영업이익 ÷ 매출':'CFO − 양의 현금 설비투자 지출'}</p><strong class="phase-value">${c.output===null?'미계산 · null':esc(c.output_unit==='fraction'?percent(c.output):exact(c.output)+' USD')}</strong><p>${esc(c.definition)}</p><p class="secondary">프로젝트 계산 정의입니다. 회사 발표 FCF·회사 전망과 구분합니다. 계산 성공도 사람 검토 완료를 뜻하지 않습니다.</p><ul class="reason-list">${c.reasons.map(r=>`<li>${esc(reason(r))}</li>`).join('')}</ul>${c.input_refs.map(id=>sourceCard(facts.get(id),factTitle(facts.get(id)))).join('')}<details><summary>정확한 출력·공식 버전</summary><p class="run-meta">output=${esc(c.output??'null')}<br>${esc(c.formula_id)} v${esc(c.formula_version)}<br>${esc(c.rounding)}<br>당시 이용 가능: ${c.historical_eligible?'조건 충족 후보':'미확인/부적합'}</p></details></div>`;
  }
  function reports(view) {
    if(!data)return;
    if(['review','changes','calculations'].includes(view)) {
      $('version').textContent=view==='review'?data.policies.P06:data.policies.P07;
      $('run-label').textContent=`P06 ${data.source_runs.P06} · P07 ${data.source_runs.P07} · ${displayDate(data.generated_at)} snapshot`;
      $('mode').textContent='P06·P07 · 게시 결과 조회';
    } else if(state.data) {
      $('version').textContent=state.data.rule_version;
      $('run-label').textContent=`P05 ${state.data.run_id} · ${displayDate(state.data.completed_at)} 기준`;
      $('mode').textContent=state.data.local?.enabled?'P05 · 내 PC 실행 가능':'팀 공유 · 결과 보기';
    }
    if(view==='validation'&&!$('phase-validation'))$('validation-view').insertAdjacentHTML('afterbegin',`<section class="panel section-card" id="phase-validation"><div class="eyebrow">P06 · P07 DEVELOPMENT CHECKS</div><h2>검토·비교 엔진 검증</h2><p>P06 합성 반례 ${data.verification.P06.synthetic_cases}개, P07 ${data.verification.P07.synthetic_cases}개 통과. 같은 입력 별도 run 의미 결과 재현을 확인했습니다.</p><p>P03 동결 후 비교 회귀 ${data.verification.p03_regression.matched}/${data.verification.p03_regression.total}행 일치. 같은 개발 자료의 회귀이며 검색 Recall·정확도가 아닙니다.</p><p>사람 gold·독립 qrels·중요성 정답: 모두 0개. 정식 성능·효용·보정 미평가.</p></section>`);
    if(view==='about'&&!$('phase-about'))$('about-view').insertAdjacentHTML('afterbegin',`<section class="panel section-card" id="phase-about"><h2>P06·P07 현재 실행</h2><p>검토 사유와 확인 목록, 세 시점 모드, 이전/새 정보 비교, 조건부 재무 공식과 중단 결과를 추가했습니다.</p><p>동일한 Microsoft 개발 발표 2건·family 2개입니다. 기존 한국기업 자료·예약 FY2026 Q1 본문은 실행 입력에 사용하지 않았습니다.</p><p>신규 원문 수집 0건. 기존 최소 사실 참조 범위를 유지합니다. 원문 prose·private 파일·키는 게시하지 않습니다.</p><p>미실행: ${esc(data.unperformed.join(' · '))}</p><p class="run-meta">P06 ${esc(data.source_runs.P06)} · P07 ${esc(data.source_runs.P07)}<br>snapshot ${esc(displayDate(data.generated_at))} · Asia/Seoul</p></section>`);
  }
  window.renderPhaseReports=reports;
  for(const id of ['review-order','review-date','review-scope','review-metric','review-reason'])$(id).addEventListener('change',renderReview);
  for(const id of ['change-mode','change-status','change-scope'])$(id).addEventListener('change',renderChanges);
  $('calc-mode').addEventListener('change',renderCalculations);
  fetch('/phases.json',{cache:'no-store'}).then(r=>{if(!r.ok)throw new Error('P06·P07 결과를 불러오지 못했습니다.');return r.json();}).then(d=>{
    if(d.schema_version!=='p06-p07-site-0.1'||!d.facts||!d.review)throw new Error('P06·P07 결과 형식을 확인하세요.');
    data=d;facts=new Map(d.facts.map(r=>[r.record_id,r]));
    options('review-date',d.facts.map(r=>r.published_date),v=>v);options('review-scope',d.facts.map(r=>r.normalized.scope_id),v=>scopes[v]||v);
    options('review-metric',d.facts.map(r=>r.normalized.metric_id||r.normalized.relation_type),v=>metrics[v]||'사업부 보고 관계');options('review-reason',d.review.map(r=>r.reason_group),v=>groups[v]);
    options('change-scope',d.facts.map(r=>r.normalized.scope_id),v=>scopes[v]||v);
    renderReview();renderChanges();renderCalculations();switchView(state.view);
  }).catch(error=>notice(error.message,true));
})();
