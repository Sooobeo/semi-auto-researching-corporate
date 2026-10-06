# P02 실행 인계

2026-10-05 · schema/guide 0.1.0 · **초안 인계**, Phase 종료·팀 확정 아님.

실행한 것은 문헌 확인 → 설계 선택 → 실제 JSON Schema/가이드 구현 → 합성 정상·오류 사례 검증이다. 실제 미국 기업 본문은 P01 접근 조사에서 확보되지 않아 source-supported claim/seed 0건, 인간 독립 주석·조정·gold 0건이다. 기존 한국기업 데이터·등록부·뉴스 4건/186블록은 입력으로 사용하지 않았다. Microsoft/NVIDIA는 접근 조사 후보이며 선정 범위·회계기간·quota·팀 역할은 미확정이다.

## 산출물과 검사 결과

- literature_matrix.csv: primary 자료 14개, 읽은 절/페이지·상태·적용 규칙·한계. literature_map.csv는 동일 내용 호환 이름, events/materiality/metrics는 축별 부분집합이다.
- event_unit_decision.md·event_schema.md·relation_schema.md·event_schema_v0.1.json: claim/event/family와 관계 tuple, 시간·scope·숫자·누락·근거·권리·revision을 분리했다.
- schema_examples.jsonl: 합성 6건. 계획/실적 두 제품, 수치 0, null prior의 상대 변화, 공급 계획/실행 후속을 포함했다. 실제 사례 수에 포함하지 않는다.
- schema_validation_cases.json/schema_validation_report.json: 정상 6건과 거부해야 할 오류 22건, 총 28건. 날짜에 가짜 midnight, 사유 없는 null, 입력 부족 계산 output, stale missing reason, product/entity 불일치, raw action mismatch, 권리 미확인 발췌, Unicode offset 등을 검사했다. 최종 수치는 report에서 재계산한다.
- annotation_guide_v0.1.md·financial_annotation_notes.md·materiality_questions.md·prior_state_policy.md: 독립 작성/시점 제한·재무 문맥·질문·as_of 비교 규칙이다.
- research_map.md·decisions.md·guideline_questions.md·task_status.csv: 결정 근거와 완료 수준, 후속 확인을 연결한다.

합성 계약 검사는 source 원문 감사·권리 확정·NLP 성능·인간 일치도·gold를 인증하지 않는다. actual extraction/audit denominator는 0이며 성공률을 100%로 표시하지 않는다. 날짜·scope·숫자의 실제 unresolved 항목은 원문 미확보로 조사하지 못했으며 개별 실제 사실 오류로 숫자를 만들지 않았다.

## 재현

스키마·합성 fixture 재생성은 생성 파일을 이미 갖고 있으므로 기본 명령이 덮어쓰기를 거부한다. 변경 내용을 검토한 후 `python scripts/p02_build_schema.py --replace-generated`를 실행한다. markdown 가이드는 생성기가 덮어쓰지 않는다.

프로젝트 전역 Python을 변경하지 않으려면 PowerShell에서 다음을 각각 실행한다.

```powershell
python -m pip install --target "$env:TEMP\p02-jsonschema-20261005" -r scripts/p02_requirements.txt
python scripts/p02_validate_schema.py --dependency-path "$env:TEMP\p02-jsonschema-20261005"
```

검사 dependency는 jsonschema 4.26.0이다. 표본/가이드/스키마 hash는 artifacts_manifest.csv에 있다. 원본 block이 생기면 `--blocks <새 미국 blocks.jsonl> --examples <실제 양식 jsonl> --report <새 보고서 경로>`로 위치 왕복을 검사하고 P01 registry ID·권리·회계기간을 사람이 추가 대조한다. 기본 검사기는 source rights를 확정하지 않는다.

## 미완료 작업

P02-T05 실제 seed와 T10 인간 2인 이상의 처음 보는 실제 사례 독립 작성이 미완료다. T01~T04는 질문/문헌 실행 범위만 부분 완료이고 T06~T09는 잠정 구현이다. T11은 초안 패키지 인계이며 최종 종료 조건이 아니다. 사용자/팀 범위·담당/가용시간, 허용 원문 접근, 원문 수동 감사, 실제 재무 개념/지표 선정, 독립 주석과 조정 전 일치도, 가이드 수정·재검증을 다음 순서로 진행한다.

source 조건 unresolved는 허용된 다른 경로의 접근 조사로 해소한다. 소표본에 접근한 뒤에도 회사 발표와 외부 확인 수준을 분리한다. 가이드 개발에 쓰인 실제 표본은 adaptation/practice로 남기고 test에 넣지 않는다.
