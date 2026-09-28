# 저장 HTML의 기사 식별·시각 메타데이터 검토

저장된 HTML 22개를 로컬에서 읽어 canonical URL, `og:url`, 기사 ID, 게시/수정 시각 후보를 별도 overlay로 기록했습니다. 원래 `doc_id`와 manifest는 변경하지 않았습니다.

- 22/22개에 canonical·OG URL이 있고 원요청 URL의 기사 ID를 지지합니다. 기사 ID 불일치는 0건, 서로 다른 문서가 같은 canonical URL을 선언한 그룹도 0개입니다. 이것만으로 독립 원저작이나 기사 고유성을 확정하지 않습니다.
- 이전 `body_audit_003`과 날짜·제목·부제·바이라인 메타데이터가 각각 22/22개 일치했습니다. 같은 추출기를 재사용했으므로 이는 재현성 검사이며 독립적인 의미 해석 정확도 검증은 아닙니다.
- 날짜 역할 후보는 게시 72개, 수정 29개, 역할 미확정 5개입니다. 게시 후보 중 40개는 명시적 `+09:00`이 있어 UTC를 파생할 수 있고, 22개 기사 모두에 해당 후보가 있습니다. 시간대가 적혀 있지 않은 게시 후보 32개도 함께 보존합니다. 표면 시각에 임의로 한국 시간대를 붙이지 않았습니다.
- 게시 후보끼리, 수정 후보끼리 비교한 충돌은 각각 0건입니다. 단일한 정답 시각을 선택하거나 사건 발생 시각으로 바꾸지 않았습니다. `NEWS-4777711726295645`의 수정일 meta와 JSON-LD 값은 빈 문자열이므로 파싱 불가 2개로 유지합니다.

`article_metadata_overlay.jsonl`은 정확한 요청/최종 URL, canonical/OG/JSON-LD URL 근거, ID 후보와 제목/바이라인의 hash를 담습니다. `date_candidates.jsonl`은 게시/수정 구분, 원시값 hash·위치, 날짜·시각·정밀도·명시 시간대·UTC 파생값을 분리합니다. UTC는 원래 분/초 정밀도를 유지합니다. 원시 header 값과 제목·바이라인은 Git 제외된 `raw/`에만 있습니다.

기계적·합성 경계 검증 14개가 통과했습니다. 원자료 hash 22/22개가 맞고 입력 파일은 바뀌지 않았습니다. 비공개 파일 3개는 Git 제외·추적 0개입니다. 네트워크·외부 모델 호출이나 본문 출력은 없습니다. 정밀도 전체 분포는 초 62개, 분 27개, 날짜만 15개, 파싱 불가 2개입니다.

```powershell
python scripts/p01_domestic_metadata_review.py --audit-dir artifacts/p0/domestic_pilot_20260922/body_audit_003 --manifest artifacts/p0/domestic_pilot_20260922/collect_smoke/manifest.csv --manifest artifacts/p0/domestic_pilot_20260922/collect_remaining/manifest.csv --output-dir artifacts/p0/domestic_pilot_20260922_followup/metadata_review_NEW
```
