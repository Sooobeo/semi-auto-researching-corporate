# 이미지 IR 페이지 OCR 개선 비교

기존 `ir_image_ocr_001`을 보존하고 세 조건을 비교했다. 대표 3쪽에서 눈으로 확인한 주요 제목과 기간이 함께 인식되는지 점검한 결과, 원본 sparse OCR은 2/3, 회색조 축소 영상은 2/3, 붉은색·주황색 글자 분리 영상은 3/3이었다. 001에서 인식하지 못했던 SKH-2026Q2-IR 13쪽의 제목과 분기도 회복됐다.

선택한 고정 설정은 `red_orange_mask_half_sparse`다. 원래 200 DPI 렌더를 가로·세로 절반으로 줄인 뒤 붉은색과 주황색 부분을 검은색으로 변환하고, Tesseract 영문 모델의 PSM 11로 인식한다. 대표 쪽의 제목·기간 일치 여부를 선택 기준으로 썼으며 최고 confidence로 정답을 고르지 않았다. 대표 3쪽 원본과 변형 이미지의 시각 대조도 수행했다. 같은 설정을 대상 31쪽에 적용하며 다른 두 조건의 인식 결과도 보존한다.

이 설정은 **주요 제목 인식을 보완하는 용도**다. 검은색·회색의 작은 글자나 한글 문구는 지워질 수 있고 배경이 잡음으로 인식되기도 한다. 변형 영상을 원본으로 대체하지 않았다. 3쪽의 토큰 일치만으로 나머지 28쪽의 정확한 전사나 31쪽 전체의 의미적 완전성을 확인한 것은 아니다. 단어 후보 수와 confidence는 정확한 정보량 또는 정답률이 아니며, 자동 인식된 숫자를 수치 근거로 승격하지 않았다. 사람의 전사 검증은 0쪽이다.

최종 집계는 `summary.json`을 참조한다. `page_manifest.csv`는 선택 설정의 쪽별 결과, `variant_page_manifest.csv`는 세 조건의 전체 결과, `preview_checks.csv`는 표본별 자동 토큰 일치 검사다. `visual_review.csv`의 검토 주체는 AI이며 사람의 검토와 구분한다. `source_preservation.csv`는 기존 PDF의 해시 보존, `validation.json`은 쪽 연결·렌더·OCR 해시·좌표·비공개 제외를 검증한다.

원본 sparse 영상의 경로 기준은 저장소 루트(`render_uri_base=repository`)이며, 새 변형 영상과 OCR JSON은 이 출력 폴더 기준이다. 새 영상과 문자 원문은 `raw/`에만 저장한다. 공개 표에는 원문 문자열을 복제하지 않는다. 원본 PDF, 기존 본문 블록, 001 실행은 그대로 둔다. 외부 OCR 서비스는 사용하지 않았다.

재실행 시 새 경로를 지정한다.

```powershell
python scripts/p01_ir_image_ocr.py --baseline-output artifacts/p0/domestic_pilot_20260922_followup/ir_image_ocr_001 --output-dir artifacts/p0/domestic_pilot_20260922_followup/ir_image_ocr_003
```
