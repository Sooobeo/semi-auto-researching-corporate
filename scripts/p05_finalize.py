"""Review gates, candidate-store adapter and immutable P05 development handoff."""
from __future__ import annotations
import argparse
from collections import Counter
from pathlib import Path
from p05_common import *
from p05_validate_predictions import ValidationContext, validate_run

def stage4(out,run):
    require_stage(3,out)
    comparison=read_json(run/'comparison_manifest.json'); validation=read_json(run/'validation_report.json')
    tests=read_json(out/'stage_reviews/stage_04_adverse_tests.json')
    rules=read_json(out/'stage_reviews/stage_04_rules_after_fix.json')
    checks=dict(validation=all(validation['checks'].values()),one_to_one=comparison['reference_keys_unique'],
                match_39=comparison['matching_status']=={'matched':39},no_field_errors=comparison['field_errors']==0,
                no_unmatched_candidates=comparison['unmatched_candidate_count']==0,
                adverse_cases=tests['passed']==tests['total'],corrected_rule_cases=rules['passed']==rules['total'],
                reference_after_freeze=comparison['reference_read_at']>comparison['predictions_frozen_at'])
    write(out/'stage_reviews/stage_04_improvements.md','''# 4단계 검증·개선

비교기의 초기 dict 문법 오류를 수정하고 이전 코드를 보존했다. m0_002의 실제 비교에서 숫자/단위/기간/관계는 일치했으나 사업부 숫자 9개의 미감사 표시가 company_reported_table로 약화되어 있었다. P0 source_conditions의 숫자표 Unaudited 기록을 근거로 입력 adapter와 qualifier 정책을 고쳤다. 답 숫자를 복사하거나 기존 참조를 수정하지 않았다.

이전 입력·규칙은 revisions/qualifier_001, 최초 비교 9건은 runs/m0_002/error_analysis.csv에 보존했다. M0 0.1.0→0.1.1로 올려 새 run을 생성했다. 숫자 33·관계 6 전부 재비교했고 미감사 표시를 포함한 필드 불일치는 0이다. 무감사·외부확인 과장, 숫자/단위/기간/근거 변조, 누락/중복, ID 변경, 미상 분모 등 합성 검증 37/37을 통과했다. 이는 독립 정확도 측정이 아니다.
''')
    write(out/'fallback_policy.md','''# 실패·보류·격리 및 호출 정책

지원하는 입력은 고정된 Microsoft 2문서의 선택 셀·머리글이다. 다른 문서, 지표의 모호한 이름, 알려지지 않은 단위/기간/회계기준, 양수로 들어온 capex 원표현은 abstained로 남긴다. 0은 유효 값, 빈칸/dash/unknown은 서로 다른 보류 사유다. 입력 근거 연결·hash·schema 오류는 quarantined, 예기치 못한 실행 오류는 failed다. 오류를 낮은 중요성으로 바꾸지 않는다.

input_results에는 모든 입력의 terminal 결과와 후보 ID/실패 단계/사유/시도가 남는다. 운영 검증 실패 후보는 저장소용 후보에서 제외하고 withheld_results에 둔다. 성공 후보도 review_readiness=needs_review다. 보고 사업부 문맥은 숫자 파싱 성공과 별개로 처리한다. 숫자 후보가 없어도 관계 후보는 유지하며 연결 불가 사유를 남긴다.

외부 LLM, 검색, 재수집, 모델 다운로드 fallback은 disabled; 호출 예산 0이다. 확률은 null이고 score_type=uncalibrated_rule이다. 인간 gold와 독립 자료가 없는 현재 참조 일치율을 신뢰 확률이나 중요성 정답으로 전환하지 않는다.
''')
    stage_report(4,'final',checks,dict(run_id=read_json(run/'run_manifest.json')['run_id'],input_count=39,
                 numeric_candidates=33,relation_candidates=6,unique_source_locations=84,field_mismatches=0,
                 tests=tests['total'],hashes=hashes([run/'predictions.jsonl',run/'comparison_manifest.json'])),out)
    if not all(checks.values()):raise ValueError('Stage 4 failed')

def export_candidates(out,run):
    ctx=ValidationContext(out);preds=rows(run/'predictions.jsonl');results=rows(run/'input_results.jsonl')
    validation=validate_run(ctx,preds,results)
    if not all(validation['checks'].values()):raise ValueError('Cannot export an invalid batch')
    docs={d['doc_id']:d for d in rows(SOURCE/'document_manifest_v0_3.csv')}
    valid=[p for p in preds if p['status']=='predicted' and not ctx.check(p)]
    jsonl(out/'validated_candidates.jsonl',valid)
    jsonl(out/'withheld_results.jsonl',[r for r in results if r['status']!='predicted'])
    store=[]
    for p in valid:
        n=p['normalized'];relation=p['record_kind']=='reporting_relation'
        normalized=dict(n)
        if not relation:
            normalized['financial_context']=dict(statement_type=n['statement_type'],balance_or_flow=n['balance_or_flow'],
                period_duration=n['temporal']['reference_period']['duration_days'])
            normalized['consolidation']='segment' if n['scope_id'] in ctx.rules['segment_labels'].values() else 'consolidated'
        store.append(dict(adapter_version='us-p4-common-candidate-0.1',
            contract_basis='structure/DATA_CONTRACTS.md v1.2; candidate extension, not P04 annotation schema',
            record_id=p['candidate_relation_id'] if relation else p['candidate_claim_id'],
            record_kind='business_relation' if relation else 'event_claim',record_status='candidate_needs_review',
            event_family_id=docs[p['doc_id']]['event_family_id'],doc_id=p['doc_id'],revision_id=p['revision_id'],
            raw=p['raw'],normalized=normalized,assessment=p['assessment'],derived=p['derived'],
            provenance=dict(p['provenance'],prediction_id=p['prediction_id'],input_id=p['input_id'],run_id=p['run_id'],
                            schema_version=p['schema_version'],registry_version=p['registry_version'],rule_version=p['rule_version']),
            evidence_refs=p['evidence_refs'],field_missing_reasons=p['field_missing_reasons'],human_gold=False))
    jsonl(out/'candidate_store_records.jsonl',store)
    def anchor(p):
        r=ctx.inputs[p['input_id']]
        return (p['doc_id'],p['revision_id'],tuple(sorted((e['kind'],e['location'],e['start'],e['end'])
                for e in r['evidence'] if e['kind'] in ('row_label','period_header','year_header'))))
    links=[]
    for p in valid:
        if p['record_kind']!='reporting_relation':continue
        matches=[n for n in valid if n['record_kind']=='numeric_claim' and anchor(n)==anchor(p)]
        links.append(dict(candidate_relation_id=p['candidate_relation_id'],candidate_claim_id=matches[0]['candidate_claim_id'] if len(matches)==1 else None,
                          link_status='shared_selected_row_and_reporting_period' if len(matches)==1 else 'numeric_candidate_unavailable_or_ambiguous',
                          event_family_id=docs[p['doc_id']]['event_family_id'],not_independent_evidence=True))
    jsonl(out/'relation_claim_links.jsonl',links)
    return dict(candidates=len(valid),store_records=len(store),relations=len(links),linked_relations=sum(x['candidate_claim_id'] is not None for x in links))

def stage5(out,run,repro):
    require_stage(4,out)
    primary=rows(run/'predictions.jsonl');repeated=rows(repro/'predictions.jsonl')
    first=read_json(run/'run_manifest.json');second=read_json(repro/'run_manifest.json')
    source=read_json(out/'input_snapshot.json')
    checks=dict(semantic_reproduction=[semantic(p) for p in primary]==[semantic(p) for p in repeated],
                primary_39=len(primary)==39,reproduction_39=len(repeated)==39,
                all_terminal_39=len(rows(run/'input_results.jsonl'))==len(rows(repro/'input_results.jsonl'))==39,
                upstream_preserved=all(sha(ROOT/x['path'])==x['sha256'] for x in source['inputs']),
                current_code_hashes=first['code_sha256']==second['code_sha256']==code_hashes(),
                no_external_calls=first['external_calls']==second['external_calls']==0,
                reference_free_inference=first['reference_read_at'] is None and second['reference_read_at'] is None,
                reproduction_valid=all(read_json(repro/'validation_report.json')['checks'].values()),
                reproduction_comparison=read_json(repro/'comparison_manifest.json')['field_errors']==0)
    stage_report(5,'initial',checks,dict(primary_run=first['run_id'],reproduction_run=second['run_id']),out)
    if not all(checks.values()):raise ValueError('Stage 5 reproduction failed')
    export=export_candidates(out,run)
    runtime=first['inference_seconds']
    numeric=[p for p in primary if p['record_kind']=='numeric_claim'];relations=[p for p in primary if p['record_kind']=='reporting_relation']
    fields=rows(run/'reference_match_results.jsonl')
    observed=[f for row in fields for f in row['fields'] if f['origin']=='observed_or_rule_derived']
    provided=[f for row in fields for f in row['fields'] if f['origin']=='curator_provided']
    states=[f for row in fields for f in row['fields'] if f['origin']=='state_only']
    json_file(out/'active_run.json',dict(run_id=first['run_id'],run_dir=run.relative_to(ROOT).as_posix(),
        reproduction_run=second['run_id'],rule_version=read_json(out/'rules_v0_1.json')['rule_version'],
        status='development_baseline_ready',formal_p05_benchmark_complete=False,human_gold=0,independent_test_items=0))
    write(out/'development_report.md',f'''# P05 개발 결과 — 2026-10-06

상태는 development_baseline_ready다. Microsoft 실적표의 선택 항목을 구조화하는 M0 규칙 baseline을 구현·실행·오류 수정·재현했다. 원문 전체에서 중요한 사건을 찾거나 미래 실적/투자 중요성을 판단한 결과가 아니다.

| 단위 | 이번 실제 결과 |
| --- | ---: |
| 기업 / 숫자 문서 / 발표 family | 1 / 2 / 2 |
| 숫자 입력 / 관계 문맥 입력 | 33 / 6 |
| terminal 결과 | 39 / 39 |
| 숫자 묶음 개발 참조 일치 | 33 / 33 |
| 관계 묶음 개발 참조 일치 | 6 / 6 |
| 관측·규칙 파생 필드 일치 | {sum(f['matched'] for f in observed)} / {len(observed)} |
| 사전 제공 문맥 필드 일치 | {sum(f['matched'] for f in provided)} / {len(provided)} |
| 미상·해당 없음 상태 일치 | {sum(f['matched'] for f in states)} / {len(states)} |
| 숫자 셀 span exact / 겹친 문자 | 33 / 33 · 230 / 230 code point |
| 고유 기존 근거 위치 / 역할별 근거 | 84 / 88 |
| 근거 사용 횟수 | 189 (독립 근거 수 아님) |
| 같은 원문 숫자 후보에 연결한 관계 | 6 / 6 (고유 endpoint tuple 3) |
| 신규 수집·외부 호출·모델 다운로드 | 0 / 0 / 0 |
| 전체 본문·날짜충돌 수동 감사 | 미실행 |
| 인간 gold / 독립 test | 0 / 0, 성능 지표 null |

발표는 FY2024 Q4(2024-07-30), FY2025 Q4(2025-07-30)다. 숫자 대상 기간은 FY2024/FY2025의 Q4·연간·6월30일 잔액이다. 2025 발표의 2024 비교열 3개는 2025 발표/표시 정의로 남겼다. 한국 기사·매체 표현 비교는 수행 범위가 아니다. 비교한 39쌍은 프로그램 후보와 기존 agent 참조 쌍이며 기사 쌍이 아니다.

숫자 표에서 원문 64,727과 millions, Three Months Ended June 30, 2024 및 Total revenue를 읽으면 64,727,000,000 USD, 2024-04-01~2024-06-30의 매출 후보를 만든다. 숫자와 기간을 ID 문자열에서 가져오지 않는다. 1달러 기본 단위로 변환했으며 원 배율과 원 부호는 별도 보존했다.

첫 검증에서 잔액 날짜 셀의 이중 역할, 실행 manifest의 상대경로, 비교기의 문법 오류, 사업부 숫자 9개에서 빠진 미감사 qualifier를 발견했다. 이전 자료/실패/예측은 보존했다. qualifier 수정은 P0의 기존 미감사 표 기록을 근거로 했으며 규칙을 0.1.0→0.1.1로 올려 재실행했다. 최종 비교의 필드 오류 0, 매칭 누락 0, 추가 후보 0이다. 오류가 없는 것은 이 선택된 공유 개발 표본에서의 회귀 결과다.

최종 합성 검증은 입력 23, 규칙 37, 비교/검증 37로 총 97개다. 실제 source 표본과 별도이며 문서 수를 늘리지 않는다. primary {first['run_id']}와 reproduction {second['run_id']}의 semantic payload가 39/39 동일하다. run ID/후보 ID는 실행별로 달라진다. 주 실행의 추출 {runtime:.6f}초, Python peak allocation {first['peak_python_allocation_bytes']} bytes; 초기화/CPU는 run_manifest에 별도 기록했다. OS 전체 peak RSS와 대량 처리 용량은 미측정이다.

전사 scope 후향 의존성 24개, 사업부 표시 정의 9개, 관계 실제 유효기간 6개, prior 미확인 39개를 유지한다. 날짜는 일 정밀도이며 정확 시각/시간대를 만들지 않았다. 모든 review_readiness는 needs_review이고 확률은 null이다. M1/M2/M3, 독립 precision/recall/F1·관련성·NER·중요성·일반화는 not_evaluated다.

출처는 Microsoft 공식 IR의 기존 로컬 최소 숫자/표준 라벨 참조이며 권리 근거는 ../p0/available_20261005/source_conditions.md(확인일 2026-10-05)다. 원문 AI 입력/학습·공유 권리 unresolved를 변경하지 않았다. private 원문은 로컬 위치 검증에만 쓰고 공개 산출물에 복제하지 않았다. FY2026 Q1 예약 본문/숫자는 추출 입력에서 제외했다.
''')
    write(out/'execution_briefing.md',f'''# P05 실행 브리핑 — 처음 보는 사람을 위한 설명

**실적표에서 숫자의 뜻과 근거를 함께 정리하는 첫 프로그램을 만들고, 현재 개발 자료에서 작동하는 것을 확인했습니다.** 현재 상태는 `development_baseline_ready`입니다. 정식 독립 성능평가까지 완료했다는 뜻은 아닙니다.

프로젝트는 기업이 새로 발표한 내용을 과거 자료와 비교해 사람이 검토하도록 돕는 도구를 만들고 있습니다. P04가 개발에 쓸 선택 자료와 검토 초안을 준비했다면, 이번 P05는 그 자료를 실제로 읽고 구조화하는 프로그램을 만드는 단계입니다.

예를 들어 표에 **64,727**이 적혀 있어도 그것만으로는 뜻을 알 수 없습니다. 이번 프로그램은 단위 ‘백만 달러’, 행 이름 ‘매출’, 기간 ‘2024년 4~6월’을 함께 읽어 **647억 2,700만 달러의 분기 매출**이라는 기록으로 만듭니다. 원문에서 어느 셀을 읽었는지도 남깁니다. 회사가 어떤 사업부를 보고했는지에 대한 관계도 별도 기록합니다.

| 확인한 것 | 결과 |
| --- | --- |
| 사용 자료 | Microsoft 공식 실적 발표 2건 |
| 숫자 처리 | 33개 입력 → 33개 후보, 기존 참조와 33/33 일치 |
| 사업부 관계 처리 | 6개 입력 → 6개 후보, 기존 참조와 6/6 일치 |
| 누락 확인 | 39개 입력 모두에 결과가 남음 |
| 잘못된 입력·결과에 대한 검사 | 최종 합성 반례 97/97 통과 |
| 같은 입력으로 다시 실행 | 39/39 같은 내용 재현 |

실행 중에는 같은 날짜 셀의 역할이 하나로 사라지는 문제와 사업부 숫자 9개의 ‘미감사’ 표시 누락 등을 찾아 수정했습니다. 따라서 숫자만 맞추는 데 그치지 않고, 숫자의 의미·출처 상태가 보존되는지도 확인했습니다. 이전 실패 기록은 남겨 두었습니다.

**이 결과를 ‘새 문서를 읽는 정확도 100%’로 해석하면 안 됩니다.** 이번에는 읽을 셀과 머리글을 미리 골라 주었고, 비교 기준도 같은 자료를 보고 만든 agent 검토 초안입니다. 사람이 독립적으로 만든 정답과 처음 보는 시험 자료는 아직 없습니다.

지금 넘길 수 있는 것은 원문 근거가 연결된 숫자/사업부 관계 후보 39개와 실행·실패 기록입니다. 모든 후보는 ‘검토 필요’ 상태입니다. 사업부 정의 변화, 과거 시점에 확인 가능한 정보, 실제 사업 유효기간, 기존 자료와의 비교는 후속 작업입니다. 전망이나 투자 중요성은 판단하지 않았습니다.

다음 단계에서는 이 후보를 바탕으로 P06/P07의 과거 자료 비교·검토 기능을 개발할 수 있습니다. 별도로 자료 이용 범위와 독립 정답·새 표본을 확보하면 실제 추출 성능을 평가할 수 있습니다. 상세 수치와 재현 방법은 [개발 보고서](development_report.md), [인계서](handoff_p4.md), [실행 명령](verification_commands.md)에 있습니다.
''')
    write(out/'model_selection.md','''# 기본 처리기 선택

선택은 M0 exact-label + Decimal + 명시적 기간/문맥 규칙 0.1.1이다. 현재 오류는 입력 역할/qualifier/코드 계약에서 해결되었으며 더 큰 학습 모델의 필요성이 입증되지 않았다. 모델 학습·embedding·NER·관련성 분류는 실행하지 않았다. 이는 모델 성능 비교의 우승 선택이 아니라 현 자료의 개발 기본값이다.

독립 평가 착수에는 의도한 이용 목적의 권리 확인, 독립 사람 정답과 노출 기록, 새 문서의 본문/날짜/중복/비교열 감사, 실제 규모에 맞춘 split, 정답을 보기 전 규칙/매칭 정책 고정이 필요하다. 현재 두 family는 한 adaptation 누수 그룹이며 FY2026 Q1은 예약만 유지한다.
''')
    write(out/'handoff_p4.md','''# P05 → 후속 개발 인계

`active_run.json`이 최종 실행을 가리킨다. `validated_candidates.jsonl`은 검증 통과한 P05 envelope 39개, `candidate_store_records.jsonl`은 공통 raw/normalized/assessment/derived 규약으로 옮긴 개발 후보 39개다. P04 정답 ID를 부여하거나 P04 annotation schema 통과로 승격하지 않았다. 원문·schema·규칙·실행·근거 ID를 provenance로 유지한다.

`relation_claim_links.jsonl`은 같은 문서/행/보고기간의 숫자 후보에 연결한 보고 사업부 관계 6개다. 공유 근거이며 6개 추가 숫자 관측이 아니다. `withheld_results.jsonl`은 실패·보류·격리 결과용이며 이번 최종 실행은 0개다. 전체 결과와 분모는 run의 `input_results.jsonl`을 읽는다. 빈 파일을 미완료 작업 완료 증거로 해석하지 않는다.

숫자값은 Decimal 문자열, USD 기본 단위, scale=1이다. 원 숫자·source_scale·source_numeric_value·부호 정책은 별도다. 기준 기간은 normalized.temporal.reference_period, 발표일은 published_date다. 기간 시작은 derived이며 관계 실제 effective/valid 날짜는 null이다. 날짜는 일 정밀도로만 처리한다. evidence_map을 통해 원 P04 위치 84개로 돌아갈 수 있다.

모든 후보는 adaptation/needs_review, 미보정 규칙 신호, 확률 null이다. 전사 scope의 2026년 후향 의존성 24개는 과거 기준 검증 근거로 쓰지 않는다. 사업부 표시 정의는 발표별로 유지하며 같은 이름만으로 비교하지 않는다. prior·정의 정책·실제 관계 유효기간은 미완료다. 중요성 MQ·외부 사실 확인·예측 실적을 생성하지 않는다.

원문은 기존 private에 그대로 있고 공유 파일에 복제하지 않았다. 출처 조건 확인일은 2026-10-05이며 최소 사실 참조 범위다. prose AI 입력·학습·외부 전송은 허용으로 승격하지 않았다. 전체 표/본문 자동 발견, 다른 기업, M1/M2/M3, 사람 gold 및 독립 benchmark는 후속 조건이 충족될 때 실행한다.
''')
    tasks=[]
    for i in range(1,12):
        status='completed_development_scope' if i in (1,2,3,6,7,8,9,11) else 'not_evaluated'
        note={4:'No relevance labels or independent split',5:'No usable sentence/span gold; M2 deferred',6:'Exact label mapping only; embeddings deferred',
              8:'Shared adaptation regression only',9:'Uncalibrated rule signals; external fallback disabled',10:'No independent test',11:'M0 development handoff; no learned model comparison'}.get(i,'Selected-cell development scope')
        tasks.append(dict(task_id=f'P05-T{i:02}',status=status,scope=note))
    csv_file(out/'task_status.csv',tasks)
    write(out/'verification_commands.md',f'''# 실제 실행 및 재검증 명령

저장소 루트의 PowerShell에서 실행한다. Python 3.13.3과 requirements.lock의 기존 로컬 설치를 사용했다. jsonschema가 기본 경로에 없으면 %TEMP%/p02-jsonschema-20261005를 읽는다. 네트워크 설치/호출은 없다.

```powershell
$env:PYTHONIOENCODING='utf-8'
python scripts/p04_verify_package.py
python scripts/p05_verify_package.py
```

기존 파일 덮어쓰기를 거부한다. 아래 출력 폴더/보고서가 없을 때만 새 이름으로 실행한다.

```powershell
python scripts/p05_test_baseline.py --stage inputs --report artifacts/us_equity/p4_checks/inputs.json
python scripts/p05_test_baseline.py --stage rules --report artifacts/us_equity/p4_checks/rules.json
python scripts/p05_rule_baseline.py --run-id recheck_001 --output-dir artifacts/us_equity/p4_checks/recheck_001
python scripts/p05_validate_predictions.py --run-dir artifacts/us_equity/p4_checks/recheck_001
python scripts/p05_compare_reference.py --run-dir artifacts/us_equity/p4_checks/recheck_001
python scripts/p05_test_evaluation.py --run-dir artifacts/us_equity/p4_checks/recheck_001 --report artifacts/us_equity/p4_checks/evaluation.json
```

실제 단계 순서는 prepare_inputs --stage protocol → --stage inputs → 합성 입력 검사/2단계 gate → 규칙 검사/추출/3단계 gate → validate_predictions → compare_reference → qualifier-fix 및 재실행 → 비교 반례/4단계 gate → 별도 폴더 재현 → finalize --stage 5 → verify_package다. 실행별 파일에 시각과 code/input/schema/rule/dependency hash가 있다. 현재 최종 실행은 {first['run_id']}, 재현은 {second['run_id']}이다. 추출기 CLI는 명시적 stage_02_final을 요구하므로 검토 gate를 자동으로 가장하지 않는다.
''')
    write(out/'stage_reviews/stage_05_improvements.md','''# 5단계 최종 검토

현재 코드가 모두 준비된 후 별도 출력 폴더에서 같은 입력을 재실행했다. runtime ID를 제외한 semantic payload 39/39 동일, 양쪽 결과/후보/원문 위치 검증 통과를 확인했다. 저장소 adapter는 보고 관계의 원 숫자 후보 연결 6개를 별도로 제공한다. 추출 후보와 검토 완료/인간 gold를 구별한다. 기존 P0~P3 hash와 사용자의 P05 설계 파일을 보존했다. 현재 코드·입력·결과는 package_manifest에 동결하며 최종 검증 보고서는 자기 hash 순환을 피하도록 manifest에서 제외한다.
''')
    checks.update(export_39=export['candidates']==export['store_records']==39,relation_claim_links_6=export['linked_relations']==6)
    stage_report(5,'final',checks,dict(status='development_baseline_ready',primary_run=first['run_id'],reproduction_run=second['run_id'],
                  input_count=39,export=export,upstream_files=len(source['inputs']),input_hashes=hashes([out/'extractor_inputs.jsonl',out/'rules_v0_1.json'])),out)
    files=[p for p in out.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name not in ('package_manifest.json','package_validation.json')]
    files+=list((ROOT/'scripts').glob('p05_*.py'))
    files+=list((ROOT/'artifacts/us_equity/p4_attempts').rglob('*'))
    files=[p for p in files if p.is_file()]
    json_file(out/'package_manifest.json',dict(package_version='us-p4-m0-0.1.1',frozen_at=now(),
              status='development_baseline_ready',formal_p05_benchmark_complete=False,human_gold=0,independent_test_items=0,
              active_run=first['run_id'],reproduction_run=second['run_id'],
              files=[dict(path=k,sha256=v) for k,v in sorted(hashes(files).items())],
              exclude=['package_manifest.json self','package_validation.json post-freeze','private original HTML','__pycache__'],
              recorded_failures_retained=True,unresolved=['human gold','independent benchmark','scope/presentation/prior policies','full-body and date-conflict audit']))
    print(json.dumps(dict(status='development_baseline_ready',checks=sum(checks.values()),total=len(checks),export=export)))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--stage',choices=['4','5'],required=True)
    p.add_argument('--input-dir',type=Path,default=P4);p.add_argument('--run-dir',type=Path,required=True);p.add_argument('--reproduction-dir',type=Path)
    a=p.parse_args();run=a.run_dir.resolve()
    if a.stage=='4':stage4(a.input_dir,run)
    else:
        if a.reproduction_dir is None:p.error('--reproduction-dir is required for stage 5')
        stage5(a.input_dir,run,a.reproduction_dir.resolve())
