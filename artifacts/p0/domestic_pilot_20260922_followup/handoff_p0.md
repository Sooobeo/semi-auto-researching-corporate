# P01 자료와 분석 결과 인계

기준일: 2026-09-22. 처음 읽는 사람은 [쉬운 브리핑](briefing.md)부터 읽는다. 이 문서는 실제 자료를 찾아가고 같은 점검을 반복할 담당자를 위한 안내다. 온톨로지와 P04 정답 데이터 작성은 수행하지 않았다.

## 서로 다른 두 자료 흐름

**기업의 기준 자료**는 정기보고서와 실적 IR이다. `../document_manifest.csv`에서 문서 ID, 원본 경로, 파일 해시, 대상 기간을 찾고 `../extraction_audit.csv`에서 확인한 표·문단 위치와 사업 범위를 찾는다. 두 기업 × 10분기 × 2종류로 기본 문서는 40건이다. 공식 보조 HTML 2건을 포함한 42건의 전체 추출 기록은 `../blocks.jsonl`에 있다.

**국내 언론사 기사**는 `../domestic_pilot_20260922/article_candidates.csv`의 고정 후보 39개에서 출발한다. 수집된 22개는 `collect_smoke/manifest.csv`와 `collect_remaining/manifest.csv`가 원본으로 연결한다. 미수집 17개도 원래 행과 사유를 유지한다. `collection_index.csv`의 `storage_uri`는 각 `source_manifest`가 있는 디렉터리 기준이므로 이 합본 CSV의 디렉터리를 기준으로 해석하면 안 된다.

공식 뉴스룸 4건은 회사 발표 표본이다. 국내 언론사 22건에 더해 매체 문체 표본으로 세지 않는다. 공식 문서 manifest의 보조 HTML 2건과 뉴스룸 표본 일부도 겹치므로 모든 manifest 행 수를 단순 합산하지 않는다.

## 원문으로 찾아가는 실제 예

1. `../document_manifest.csv`에서 `SAM-2024Q1-IR`을 찾는다. `storage_uri`는 `artifacts/p0/raw/SAM-2024Q1-IR.pdf`이며 저장소 루트 기준이다.
2. 파일의 SHA-256이 `3704942ea4a57008c6633f917abc0a68167fe8b8739cf68ffca2de1fd4adaea6`인지 확인한다.
3. `../extraction_audit.csv`의 같은 문서 행에 있는 **PDF 6쪽**의 문단·표를 연다. 감사 범위는 `SAM_memory_revenue_only`, 단위는 조원이다. DS 전체 값과 섞지 않는다.
4. 숫자 대조는 `../numeric_reconciliation.csv`의 `metric_scope`와 기간 변환을 함께 읽는다. 이 표의 삼성 대조 대상은 DS 매출이므로 위 메모리 매출 행과 같은 지표로 취급하지 않는다.

이 경로와 계산의 기계적 재현은 점검했다. 설계서가 요구하는 다른 사람의 독립 원문 재확인과 새 문서 등록 실습은 완료 기록이 없다.

## 이번 후속 실행의 최종 파일

| 질문 | 확인할 파일 |
| --- | --- |
| 기존 공시·IR이 보존되고 분기별 자료가 있는가? | [p01_inventory/summary.json](p01_inventory/summary.json), [coverage_review.csv](p01_inventory/coverage_review.csv) |
| 숫자와 기간 변환을 다시 계산했는가? | [numeric_recheck.csv](p01_inventory/numeric_recheck.csv), [scope_checks.csv](p01_inventory/scope_checks.csv) |
| 기사 본문 누락·혼입의 추가 신호는 무엇인가? | [추출 진단](extraction_review_001/summary.json), [검토 우선순위](extraction_review_001/review_priorities.json) |
| 한국어 문장·형태소를 어떻게 만들었는가? | [형태소 결과 읽는 법](morphology_001/methods.md), [문장 검토 200개](morphology_001/sentence_review_queue.csv) |
| 문장 비교에서 숫자·단위·계획 표현을 확인했는가? | [주장 진단 설명](claim_diagnostics_002/README.md), [pair_diagnostics.jsonl](claim_diagnostics_002/pair_diagnostics.jsonl) |
| 기사 URL·게시/수정 날짜 후보가 서로 맞는가? | [메타데이터 검토](metadata_review_001/README.md), [summary.json](metadata_review_001/summary.json) |
| 이미지뿐인 IR 페이지의 글자를 읽었는가? | [OCR 결과](ir_image_ocr_002/summary.json) |
| 여러 진단에서 같은 문서·구간을 어떻게 찾는가? | [문서 연결표](integrated_003/document_review_index.csv), [문장쌍 연결표](integrated_003/pair_review_index.csv), [작업 상태](integrated_003/task_status.csv) |
| 이전 원문과 코드가 보존됐는가? | [baseline.json](baseline.json), [final_validation.json](final_validation.json) |
| 실행 버전과 전체 산출물은 어디에 있는가? | [run_manifest.json](run_manifest.json), [artifact_checksums.csv](artifact_checksums.csv) |

`claim_diagnostics_001`은 숫자 표기·단위 경계 보완 전 결과다. 보존용으로만 두고 최종 `002`를 사용한다. 이전 국내 기사 실행의 `body_audit_003`, `classification_001`, `comparison_001`은 그대로 보존했다. 규칙 문장 448개를 사용한 비교와 Kiwi 문장 433개를 사용하는 형태소 결과는 각각의 ID를 유지하며, 연결표에서 대응 관계를 확인한다.

통합 연결표의 최종 버전은 `integrated_003`다. 최초 `001`의 데이터 연결은 맞았지만 근거 파일의 상대 경로에 오류가 있어 결과와 실패 검증을 보존하고 `002`에서 고쳤다. `003`은 최종 OCR 결과까지 명시적으로 연결한 버전이다. 이미지 OCR의 최종 버전은 `ir_image_ocr_002`이며 최초 `001`도 남겼다. 이미지 OCR 31쪽의 조건별 자동 인식 결과는 기존 743,683개 원문 블록에 합쳐 덮어쓰지 않았으며 별도 보조 결과로 남겼다.

## 로컬 재실행

모든 명령은 저장소 루트에서 실행한다. 아래 `REPLAY` 경로는 존재하지 않는 새 디렉터리여야 한다. 이 단계는 저장된 원문을 사용하므로 기사 사이트에 다시 요청하지 않는다.

```powershell
python scripts/p01_existing_evidence_review.py --output-dir artifacts/p0/domestic_pilot_20260922_followup/p01_inventory_REPLAY
python scripts/p01_domestic_extraction_review.py --body-audit-dir artifacts/p0/domestic_pilot_20260922/body_audit_003 --output-dir artifacts/p0/domestic_pilot_20260922_followup/extraction_review_REPLAY
python scripts/p01_domestic_claim_diagnostics.py --audit-dir artifacts/p0/domestic_pilot_20260922/body_audit_003 --comparison-dir artifacts/p0/domestic_pilot_20260922/comparison_001 --output-dir artifacts/p0/domestic_pilot_20260922_followup/claim_diagnostics_REPLAY
```

한국어 분석은 기존 Python 환경과 분리한 `C:/Users/Insun/.cache/p01-research/kiwi-20260922/` 환경을 사용했다. 분석기·모델 버전은 각각 0.23.1, 0.23.0이며 [고정 의존성](../../../scripts/requirements-p01-local-nlp.txt)을 사용한다. 다른 컴퓨터에서는 이 의존성으로 별도 환경을 만든다.

```powershell
& 'C:/Users/Insun/.cache/p01-research/kiwi-20260922/Scripts/python.exe' scripts/p01_domestic_morphology.py --body-audit-dir artifacts/p0/domestic_pilot_20260922/body_audit_003 --candidates artifacts/p0/domestic_pilot_20260922/article_candidates.csv --output-dir artifacts/p0/domestic_pilot_20260922_followup/morphology_REPLAY
```

처음 설치할 때만 프로그램·언어 모델 파일을 내려받았다. 기사 본문은 이 프로그램이 로컬에서 처리했다. 형태소의 분석형은 원문 글자와 다를 수 있고, 한 글자 위치에 여러 형태소가 겹치거나 길이 0인 어미가 나올 수 있다. 이를 숨기거나 원문 offset으로 잘못 재구성하지 않는다.

## 다음 담당자가 판정할 항목

- 기사 원페이지와 추출본의 제목·부제·본문·인용·표를 비교한다. 파서 간 차이를 모두 누락으로 간주하지 않는다.
- 기사 20개에 대한 두 사람의 검토와 문장 200개에 대한 경계·형태소 검토를 기록한다. 자동·에이전트 점검은 사람 서명으로 대체하지 않는다.
- 문장 비교 후보에서 숫자가 가리키는 제품, 사업 범위, 기간, 단위, 화자를 확인하고 회사 기준 발표의 주장에 연결한다. 포함한 사실과 생략한 사실은 표현 차이와 별도 기록한다.
- 반복되는 문구가 회사 보도자료·인용·전재인지 확인한다. 유사도만으로 독립 기자 표현 수를 늘리지 않는다.
- 계획→실행, 번역, 정정 관계의 실제 근거를 확인한다. 기존 family와 서로 연결된 수정본을 나중의 학습·평가 양쪽에 나누지 않는다.

원문·인용 구간·OCR 텍스트·형태소 원형이 있는 파일은 `raw/`에 보관한다. 공개 CSV와 index는 ID·해시·위치·후보 상태만 담는다. 권리 상태가 미확정인 출처를 허가 완료로 바꾸지 않았고, 출처의 명시적 수집 금지를 우회하지 않았다.
