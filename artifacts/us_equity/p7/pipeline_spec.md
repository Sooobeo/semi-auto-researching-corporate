# P08 실제 통합 계약 · 2026-10-07

정책 `integration-0.1.0`, 카드 `p08-card-0.1`, 설정 `p08-config-0.1`. 입력은 동결 P05 `m0_004`, P06 `review_change_003`, P07 `change_002`와 등록된 Microsoft 선택 표본이다. 한국기업 자료·예약 FY2026 Q1 본문·신규 URL 수집은 입력에 없다.

| 단계 | 실제 실행/입출력 | 오류·재사용 |
| --- | --- | --- |
| extract | 동결 P05 CLI를 새 경로에서 재실행 → 위치 검증 → 개발 참조 비교. 새 predictions의 의미가 동결 결과와 같은지 먼저 확인한 뒤 기존 stable candidate ID adapter 사용 | 불일치는 새 adapter가 필요한 실패. 기존 패키지 수정 금지 |
| compare | 별도 run에서 P07의 3 시점·exact/희소 검색·호환성·계산을 실행. 기존 의미 hash와 비교 | 비교 불가/입력 부족도 결과로 보존 |
| review | 새 P06 run에 새 P07 change 연결. 기존 정책의 의미 hash 대조 | 점수·확률 null, needs_review 유지 |
| cards | 검증된 facts/changes/calculations를 review group으로 구성. candidate→card 링크 생성 | 항목 실패는 failed_items에 보존하고 다른 묶음은 처리. 전체 입력 연결이 끊긴 run은 승격하지 않음 |
| feedback_snapshot | 원자적 journal의 지정 source run·카드 버전 이력을 고정. gold/학습 제외 | 파일 기반 공동 반영, 자동 공동 저장 없음 |
| validate | schema·ID·단계 보존식·Decimal·보류 null·카드 버전 검사와 피드백 반례 | 실패/취소/timeout run에 성공 manifest 없음 |

stage key는 입력 hash·문서 revision을 포함하는 동결 manifest·정책/schema/코드·설정·feedback journal hash·선행 출력 hash를 포함한다. `--resume`은 같은 key의 성공 결과 hash를 확인하고 재사용한다. 변경된 입력/설정/코드는 새 run을 요구한다. 실패 attempt는 별도 경로에 남겨 재시도한다. timeout은 retryable 또는 pipeline deadline 실패로, Ctrl+C는 cancelled로 기록한다. CLI는 고정된 Python 명령 배열만 실행하며 사용자 텍스트를 shell 코드로 조합하지 않는다.

현재 cutoff는 선행 개발 결과 재현을 위해 2026-10-06에 고정했다. 당시 공개/관측 모드는 각 발표의 날짜 cutoff를 사용한다. 실행일(2026-10-07)을 발표 날짜나 source cutoff로 대체하지 않는다. 정확 발표 시각·날짜 충돌 미확인도 그대로 남긴다.

숫자 33·관계 6 = 39 candidate → 33 card. 관계의 6 발표 주장은 고유 endpoint tuple 3개이며 숫자와 근거를 공유한다. 카드 수·후보 수·발표 family 2개를 독립 사건 분모로 혼용하지 않는다. `event_id=null`은 confirmed event가 없음을 뜻한다.

카드 순서: 회사/scope·기간·발표 → 회사 주장 → 시점별 prior/비교 → 양쪽 위치·정의 → 질문/부족 입력 → 공식/입력/중단 → 별도 검토 이력. 원문 raw/prose·자유 메모는 게시 adapter로 전달하지 않는다. 숫자는 base-unit Decimal 원문자열(scale=1), 기간은 별도 구조, offset은 Unicode code point이다.

피드백은 자체 신고 actor/시각, 원래 before, evidence ID, action/field/after, source run/card version/idempotency key를 검증한다. 최대 512KB·200건. 동일 key 다른 내용·모르는 카드/근거·위조 before·허용 밖 field·script 숫자를 거부한다. journal 하나를 원자적으로 교체하고 writer lock을 사용한다. JSONL은 재생성 가능한 append 이력 projection이다. 서로 다른 수정과 해결 이력을 모두 보존한다. 마지막 수정으로 원예측을 덮어쓰지 않는다. owner 확인은 로컬 운영자 assertion이며 플랫폼 인증된 저자 검증이 아니다.

private·키·원문·사람 메모·검증되지 않은 자유입력은 게시하지 않는다. 기존 최소 사실 참조 조건(확인 2026-10-05)을 유지하며 신규 수집/외부 LLM은 0회다. 비용·메모리 peak는 미측정이다. 서버는 loopback만 bind하고 endpoint/static 경로·Host·Origin·CSRF token·요청 크기를 제한한다.
