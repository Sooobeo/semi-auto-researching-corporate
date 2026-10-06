# 실패·보류·격리 및 호출 정책

지원하는 입력은 고정된 Microsoft 2문서의 선택 셀·머리글이다. 다른 문서, 지표의 모호한 이름, 알려지지 않은 단위/기간/회계기준, 양수로 들어온 capex 원표현은 abstained로 남긴다. 0은 유효 값, 빈칸/dash/unknown은 서로 다른 보류 사유다. 입력 근거 연결·hash·schema 오류는 quarantined, 예기치 못한 실행 오류는 failed다. 오류를 낮은 중요성으로 바꾸지 않는다.

input_results에는 모든 입력의 terminal 결과와 후보 ID/실패 단계/사유/시도가 남는다. 운영 검증 실패 후보는 저장소용 후보에서 제외하고 withheld_results에 둔다. 성공 후보도 review_readiness=needs_review다. 보고 사업부 문맥은 숫자 파싱 성공과 별개로 처리한다. 숫자 후보가 없어도 관계 후보는 유지하며 연결 불가 사유를 남긴다.

외부 LLM, 검색, 재수집, 모델 다운로드 fallback은 disabled; 호출 예산 0이다. 확률은 null이고 score_type=uncalibrated_rule이다. 인간 gold와 독립 자료가 없는 현재 참조 일치율을 신뢰 확률이나 중요성 정답으로 전환하지 않는다.
