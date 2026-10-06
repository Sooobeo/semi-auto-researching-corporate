# P03 비교·단위 규칙

2026-10-05 · 등록부 `us-p2-0.1.0` · 엔진 `us-comparability-0.1.1`.

구현은 [p03_comparability.py](../../../scripts/p03_comparability.py), 실제 적용은 [applied_002](applied_002/run_manifest.json)이다. 비교 입력·변환·결과는 원문 사실과 분리한 normalized/derived 층이다. 사람 확인은 사용자 지시로 진행 조건에서 면제했으며 독립 gold를 생성하지 않았다.

## 입력과 결과

`numeric_value`는 유한 Decimal 문자열이어야 한다. float, 쉼표 표기, NaN/Infinity와 결측 값은 자동 계산에 사용하지 않는다. 원문 USD million 값·배율·부호·표 위치는 source record에 보존하고, 비교 입력은 [unit_rules.csv](unit_rules.csv)의 고유한 scale 규칙으로 base USD와 `scale=1`로 만든다. 원문 배율이 남은 입력은 `explicit_base_unit_normalization_required`로 차단한다. 계산 정밀도는 28자리, 반올림은 `ROUND_HALF_EVEN`이다. 이는 계산 정책이며 원문 정확도의 증가를 뜻하지 않는다. [Python Decimal 공식 문서](https://docs.python.org/3.13/library/decimal.html).

판정은 `comparable`, `not_comparable`, `unknown`이다. 확인된 조건 불일치는 `not_comparable`, 필수 정보 미상은 `unknown`이며 두 경우 모두 delta를 비운다. 조건이 더 필요한 입력은 이유 코드와 함께 `unknown`으로 남긴다. `comparable`에 한해서 `delta = new - prior`, `relative_delta = (new - prior) / abs(prior)`를 계산한다. relative 값의 단위는 fraction이며 표시용 백분율은 100을 곱한다. prior가 0이면 절대 차이는 계산하고 상대 변화는 `zero_prior_denominator`로 비운다.

## 결합 조건

| 확인 축 | 규칙·실패 처리 |
| --- | --- |
| 회사·scope·metric·definition | 모두 명시적 일치 필요. 전사/사업부/제품 또는 표시 정의 불일치는 `<field>_mismatch`. |
| 제품 | 명시적 같은 제품이거나, 전사 scope/`not_applicable`일 때만 null 허용. 사업부 null의 사유가 없으면 `product_unknown_for_noncompany_scope`. |
| 회계·통화·측정 | accounting basis, consolidation, currency, canonical unit, scale, value kind, balance/flow, period basis/kind, modality 일치 필요. |
| 회사 KPI·비율·부호 | adjustment definition, denominator, sign convention 일치 필요. non-GAAP 조정 정의 미상은 `non_gaap_definition_missing`; 비율 분모 미상은 `ratio_denominator_unknown`. |
| 동일 기간 | flow의 실제 시작·끝·inclusive 일수가 같아야 한다. balance는 시점 날짜 비교. 알려진 fiscal year/quarter 라벨 충돌도 차단. |
| 전년 비교 | `comparison_kind=yoy`를 명시한다. 시작·끝의 월/일이 일치하고 다음 해여야 한다. 실제 기간 길이가 같거나 calendar anniversary의 윤일 차이 1일만 허용한다. 52/53주 회계기간의 자동 호환을 허용하지 않는다. |
| 이용 가능 시점 | source publication과 모든 `availability_dependencies`를 cutoff로 확인한다. 관측시각만 확인한 근거는 `observed_conservative`로 그 시각 이후에만 사용한다. 날짜만 있는 근거로 당일 intraday 이용 가능을 확정하지 않는다. 미래·미상 근거는 delta 계산을 중단한다. |

원문 발행일과 회계기간을 별도로 보존한다. FY2024는 2023-07-01~2024-06-30(366일), FY2025는 2024-07-01~2025-06-30(365일)로 calendar anniversary guard가 필요하다. 기간 시작일은 원문 3/12개월 종료 헤더에서 계산한 값이다. 현재 연결 회계범위 보완 자료의 정확 발행일은 미확인이고 2026-10-05 관측 근거이므로 이번 결과는 현재 시점의 사후 비교다. 2024/2025 당시 판단으로 소급하지 않는다.

## 특수 변환

- YTD 차분은 같은 회계연도·시작일·회사·scope·정의·통화와 명시적 `ytd`, `flow`, `point`, `aggregation_behavior=additive_flow`가 있는 두 입력에 한한다. 짧은 YTD가 긴 YTD의 prefix여야 하며 두 claim ID를 보존한다. balance, percent, percent_point, percentage_point, ratio/fraction은 차분하지 않는다. 실제 이번 33건에는 YTD 차분 입력이 없어 실행 사례는 0건이다.
- 퍼센트 level 간 차이 단위는 `percent_point`이다. `percentage_point` 입력도 YTD 비가산 단위로 차단한다. %와 %p 간 일반 배율 변환은 없다.
- FX는 환율·출처·기준일·종류·기간 정책 없이는 실행하지 않는다. 실제 FX 실행은 0건이다.
- capex 부호는 자동 scale 변환으로 바꾸지 않는다. source extractor가 명시적 현금 PP&E 유출 line의 괄호 음수와 양의 cash payment 정규화 규칙을 각각 보존했고, 비교 엔진은 그 정의가 같은 입력만 사용한다.

## 실제 예외와 검증

사업부 revenue 정의는 `msft-segment-presentation-fy2024`와 `msft-segment-presentation-fy2025`로 구분했다. 이전 release와 다음 release의 동일 FY2024 비교열 값이 다르므로 이전 표시 기준의 값을 다음 표시 기준의 값과 자동 비교하지 않는다. 표시 차이는 원문 표에서 확인했지만 그 정확한 정책 원인은 이번 표본에서 확인하지 않았다.

21쌍 가운데 전사 전년 비교 12쌍과 FY2025 발표 내 같은 표시 기준의 사업부 전년 비교 3쌍은 계산한다. 사업부 이전 표시→새 연도 3쌍, 이전 표시→같은 기간 새 비교열 3쌍은 `definition_version_mismatch`로 차단한다. 표 셀·header·배율을 감사한 33건이 입력이며 전체 본문 검증이나 시스템 추출 정확도 표본이 아니다. 독립 구현 검사와 재계산은 [independent_validation.json](independent_validation.json)에 기록한다.

재현 명령은 [실행 브리핑](execution_briefing.md)에 있으며 기존 출력이 존재하면 새 revision 경로를 요구한다. `applied_001`은 이전 코드 실행 이력으로 보존하고 `applied_002`를 최종 적용으로 사용한다.
