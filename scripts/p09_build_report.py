"""Regenerate every numerical report from evaluation_results.json."""
import argparse
from p09_common import *

def build(path):
    path=Path(path);d=read(path/'evaluation_results.json');s=d['summary']
    atomic(path/'report_tables.json',d)
    systems=d['systems']; fields=['system','status','records','covered_candidates','documents','families','materialization_seconds','warm_seconds','unit','reason']
    csvfile(path/'system_comparison.csv',fields,systems)
    lines=['# P09 개발 검증 보고', '',
        f"Microsoft {s['documents']}문서 · {s['families']} 발표 family · 후보 {s['candidates']}개(숫자 {s['numeric_candidates']} + 관계 {s['relation_candidates']}) · 카드 {s['cards']}개.",
        '두 발표는 같은 adaptation 노출 그룹입니다. 독립 표본 39개 또는 새 자료 정확도로 해석하지 않습니다.', '',
        f"공학 검사 {d['engineering_checks_passed']}/{d['engineering_checks_total']}개, 합성·장애·평가 gate 반례 {d['synthetic_passed']}/{d['synthetic_total']}개 통과.",
        f"같은 agent 별도 실행 의미 hash 일치: {d['semantic_reproduction']}. 동료 실제 재실행은 미실행입니다.", '',
        '| 비교군 | 실행 | 출력 단위/수 | 포함 후보 | 자료 |', '| --- | --- | --- | --- | --- |']
    lines += [f"| {x['system']} | {x['status']} | {x['unit']} {x['records'] if x['records'] is not None else 'NA'} | {x['covered_candidates'] if x['covered_candidates'] is not None else 'NA'} | 문서 {x['documents']} / family {x['families']} |" for x in systems]
    lines += ['', 'S0는 시간순 최소 사실 목록, S1은 P06 규칙 목록, S3는 통합 카드입니다. 같은 후보 universe·시점·39개 후보 예산을 사용했습니다. 목록 생성시간은 사람 검토시간이 아닙니다.', '',
        f"실제 P08 단계 합계 {d['stage_wall_seconds']:.6f}초. 로컬 실행의 외부 API·LLM 호출 {d['external_calls']}회. 전체 운영 비용·메모리 peak는 미측정(null)입니다.",
        '관측 비용/1000문서도 null입니다. 실제 1000문서를 실행하지 않았고 두 문서의 짧은 처리시간을 처리량으로 일반화하지 않습니다.', '',
        '## 시점별 비교와 계산', '', '| 모드 | 변화 계산/시도 | 공식 계산/시도 |', '| --- | --- | --- |']
    lines += [f"| {mode} | {x['computed']}/{x['attempts']} | {x['calculated']}/{x['calculation_attempts']} |" for mode,x in d['mode_counts'].items()]
    lines += ['', '현재 재검토의 변화에는 독립 발표 비교와 동일 발표의 사업부 비교열이 함께 있으므로 별도 종류를 보존했습니다. 당시 공개 모드의 계산 가능 변화는 동일 발표 비교열이며 prior 검색 성능이 아닙니다.', '',
        f"보류 change 고유 결과 {d['withheld_change_count']}개, 미계산 공식 {d['withheld_calculation_count']}개. 동일 후보의 세 시점 결과는 독립 오류 표본이 아닙니다.",
        '모든 보류/실패 사례는 failure_cases.jsonl에 전체 보존했습니다. 실패 원인 수의 합은 고유 항목 수와 다릅니다.', '',
        '## 연구 미완료', '',
        '사람 gold 0, 독립 test 0, 검색 qrels 0, 실제 사람 세션 0. 추출·관계·검색·변화 정확도, 중요성 recall/NDCG, 검토시간 절감, 보정 확률, 신뢰구간은 모두 미평가입니다.',
        '정확한 발표 시각·날짜 충돌·사업부 정의 변경·보고 관계 유효기간·전체 본문 완전성·순이익→CFO 대사 입력도 미확인입니다.',
        'S2 학습 모델과 S4/S5 LLM은 데이터/권리/예산 조건 미확보로 미실행입니다. 예약 FY2026 Q1 본문은 열지 않았습니다.', '',
        '## 직접 사용할 수 있는 기능', '',
        '고정 입력 배치·실패 재개, 통합 카드·원문 위치·시점별 비교, 파일 기반 피드백 검증·중복/충돌/해결 이력, 안전한 게시 snapshot을 사용할 수 있습니다.',
        '게시 snapshot과 내 PC 실행은 다릅니다. 브라우저 초안은 공동 저장이 아니며, 내보내기→소유자 가져오기→새 실행/재게시 후 공유 결과에 반영됩니다.',
        '사이트 URL·게시 버전·상태는 별도 site_update_manifest.json에 기록합니다. 보고서 생성만으로 게시 성공을 뜻하지 않습니다.']
    textfile(path/'final_report.md','\n'.join(lines))
    textfile(path/'cost_latency_report.md',f"# 실제 비용·시간\n\n문서 분모 {s['documents']}, 후보 {s['candidates']}, family {s['families']}. P08 단계 wall 합계 {d['stage_wall_seconds']:.6f}초. 외부 호출 {d['external_calls']}회. S0/S1/S3의 cold/warm 목록 구성 관측은 system_comparison.csv에 있습니다. 원문 읽기·프로세스 시작·패키지 검사와 목록 구성을 구별합니다. 모델 로드: 해당 없음. 하드웨어·노동·에너지·메모리 peak와 금전 단가는 미측정. 관측 비용 및 1000문서 환산은 null; 외부 호출 0을 총 비용 0원으로 바꾸지 않습니다.")
    textfile(path/'failure_cases.md',f"# 전체 보류 사례\n\nchange 보류 {d['withheld_change_count']} / {sum(x['attempts'] for x in d['mode_counts'].values())} 결과, 공식 미계산 {d['withheld_calculation_count']} / {sum(x['calculation_attempts'] for x in d['mode_counts'].values())}. 전체를 failure_cases.jsonl에 보존합니다. 선정 방식: 각 stage의 미계산/보류 결과 전부. 이 목록은 호환성·시점·입력 부족과 구현 결함을 구분하며 정확도 오류로 합산하지 않습니다. 실제 입력의 카드 실패는 {d['card_failures']}개. 별도 합성 장애/피드백 반례는 synthetic_tests.json에 있습니다.")
    textfile(path/'uncertainty_analysis.md','# 불확실성\n\nMicrosoft 한 기업·두 노출 family의 development 관측입니다. CI/p-value와 일반화는 미측정. 사람 gold·독립 qrels·사람 세션 부재로 metric=null. 0%/100%로 대체하지 않습니다. 관계 6개는 고유 endpoint tuple 3개이며 숫자와 근거를 공유합니다. 중요성 임계값/운영 목표 선택은 미완료입니다.')
    textfile(path/'project_closeout.md','# 인계\n\n개발 검증과 실제 결과 게시 범위만 종료 대상입니다. 정식 프로젝트 평가는 미완료입니다. 다음은 독립 평가 목적/권리/노출 protocol을 본문 개봉 전에 고정하고 사람 정답·qrels를 수집한 새 run, 실제 두 사람의 서로 다른 과업과 교차 순서 세션, 동료 재실행입니다. 기존 개발 후보의 일괄 피드백은 사람 gold나 untouched test로 자동 승격하지 않습니다. 게시 상태는 site_update_manifest.json을 확인하세요.')
    return d

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--run-dir',type=Path,required=True);a=p.parse_args();build(a.run_dir);print('{"status":"reports_regenerated"}')
