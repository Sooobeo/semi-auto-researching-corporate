# P09 실행 결과 — 2026-10-07

`evaluation_005`의 개발 검증·재현·비교 보고와 같은 사이트 버전4 게시를 완료했다. 측정 전에 protocol을 고정했다. 상태는 **개발 완료·게시 완료, 정식 연구 평가 미완료**다.

Microsoft 2문서/2 family, P08 `integration_012`의 후보39개(숫자33·관계6)/카드33개를 사용했다. 새로운 출처·독립 평가 자료는 수집하지 않았고 예약 FY2026 Q1 본문도 열지 않았다. 출처·권리 범위는 [P08 실행 결과](../p7/execution_briefing.md)의 기존 최소 사실 사용 판단을 유지했다.

| 개발 검증 | 실제 결과 | 해석 범위 |
| --- | --- | --- |
| 공학 검사 | 12/12 통과 | 동결 package·계약·재현·실패 처리 |
| 합성/장애/평가 조건 | 37/37 통과 = P08 30 + P09 7 | 독립 정확도 아님 |
| 같은 agent 별도 run | 카드 의미 hash 일치 | 동료 실제 재실행 미실행 |
| S0 / S1 / S3 | 39후보 / 39후보 / 33카드(39후보 연결) | 같은 universe·cutoff·예산의 개발 비교 |
| exact/희소 검색 비교 | 234 query, 117쌍 중 선택 결과117쌍 일치 | qrels 없는 개발 선택 비교, Recall 아님 |
| S2 / S4 / S5 | 미실행 | 독립 train/dev/labels 또는 AI권리·예산 미확보 |

current_review 변화15/42(발표 간12·동일 발표 비교열3)·공식8/8, historical_public 변화3/42(동일 발표 비교열)·공식0/8, observed_live 변화0/42·공식0/8이다. 보류 변화108개와 미계산 공식16개, 총124개 결과를 전체 보존했다. 동일 후보의 여러 시점 결과이며 독립 오류124개로 해석하지 않는다.

외부 API·LLM 호출은0회, 실제 P08 단계 합계는 약3.067초다. 전체 비용·peak memory·1000문서 비용은 미측정(null)이다. 목록 생성시간은 사람 검토시간이 아니다.

사람 gold·독립 test·qrels·실제 사람 세션은 각각0이며 정식 정확도·중요성 recall·검토시간 절감·보정·CI는 모두 null/미평가다. 사람 작성 학습 사례도0이다. 프로그램을 완성했다는 이유로 사람 판단·개인 이해·투자 효용을 인정하지 않는다.

[기존 사이트](https://corporate-research-p05.sooobeo.chatgpt.site)의 **버전4 배포 `succeeded`**, 2026-10-07 13:58 KST. 기존 접근2인 유지, 팀원 실제 접속은 미확인이다. 로컬 desktop/mobile 주요 UI는 agent가 확인했고 사람 사용성은 미실행이다. 원문/private/credential은 배포 묶음에서 제외했다.

[최종 개발 보고](runs/evaluation_005/final_report.md) · [평가 protocol](runs/evaluation_005/evaluation_protocol.md) · [게시 manifest](runs/evaluation_005/site_update_manifest.json) · [후속 사람 평가 protocol](runs/evaluation_005/study_protocol.md) · [재현 안내](runs/evaluation_005/reproducibility.md) · [산출물·변경 파일 인계](delivery_index.md)
