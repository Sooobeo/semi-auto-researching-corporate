import fs from 'node:fs';
import path from 'node:path';
import zlib from 'node:zlib';

const ROOT = 'C:/Users/Insun/semi-auto-researching-corporate';
const OUT = path.join(ROOT, 'output/documents/corporate_research_system_update_20261007.docx');
const BUILD = path.join(ROOT, 'tmp/docx_system_update_20261007');
const pages = [];
const page = (title, items) => pages.push({title, items});
const P = text => ({kind:'p',text});
const H = text => ({kind:'h',text});
const T = (headers, rows, widths) => ({kind:'table',headers,rows,widths});
const L = text => ({kind:'list',text});

page('1 사용자가 경험하게 될 변화', [
 P('현재 시스템은 기업의 새 발표에서 숫자와 관계를 추출하고, 이전 정보와 비교한 결과를 검토 카드로 보여줍니다. 변경 후에는 사용자가 그 정보를 자신의 가설에 연결하고, 판단을 바꾼 이유와 이후 결과까지 확인할 수 있도록 확장합니다. 기존 수집·추출·비교 기능과 검증 기록은 첫 번째 버전인 V1으로 보존합니다. 그 위에 가설 추적과 사후 검증을 추가하는 두 번째 버전을 V2로 제안합니다.'),
 P('사용자에게 가장 크게 달라지는 점은 발표별 검토가 가설별 판단 이력과 후속 결과까지 이어진다는 것입니다. 사용자는 처음에 무엇을 예상했는지, 당시 어떤 근거를 사용했는지, 새 정보 때문에 무엇을 수정했는지, 실제 결과가 어떠했는지를 한 흐름에서 확인하게 됩니다.'),
 T(['사용 과정','현재 V1에서 하는 일','변경 후 V2에서 하게 될 일'], [
 ['새 발표 확인','선택된 숫자·관계 후보와 원문 위치를 카드에서 확인합니다.','등록된 새 자료를 처리하고, 어떤 가설과 관련된 발표인지 함께 확인합니다.'],
 ['이전 정보와 비교','기간·사업 범위가 맞는 이전 값과 변화량을 봅니다. 비교 불가 이유도 확인합니다.','기존 비교에 더해, 이 변화가 가설을 지지하거나 반박하는 이유를 검토합니다.'],
 ['판단 기록','검토 초안을 만들고 파일로 내보낼 수 있습니다. 가설의 버전 이력은 아직 연결되지 않았습니다.','가설을 유지·수정·보류한 이유와 당시 근거를 새 버전으로 기록합니다.'],
 ['후속 발표 확인','후속 결과와 자신의 과거 판단을 체계적으로 연결하는 기능은 없습니다.','처음 정한 대상 기간과 판정 조건을 사용해 실제 실적을 비교합니다.'],
 ['과거 판단 재확인','세 시점 모드의 비교 결과와 보류 사유를 조회합니다.','특정 가설 버전에서 사용한 근거를 복원하고, 사후 결과는 별도 화면에서 봅니다.']
 ],[1450,3850,4110]),
 P('V2의 사용자 경험은 향후 제작할 목표입니다. 현재 P09까지 완료한 범위는 V1의 개발·자동 검증·게시이며, V2 기능이 이미 구현됐다는 뜻은 아닙니다. 독립 자료의 정확도와 실제 사람의 검토 효용도 별도로 평가해야 합니다.'),
 P('이 문서는 사용자 이용 변화부터 설명한 뒤, 현재 진행 상태와 전체 시스템 변경을 정리합니다. 이어서 P01부터 P09까지의 수정 작업과 완료 기준을 제시합니다. 기준일은 2026년 10월 7일입니다.')
]);

page('2 하나의 사례로 보는 변경 전후의 이용 과정', [
 P('다음은 이용 과정을 설명하기 위한 가상 사례입니다. 기업 A와 아래 가설은 실제 확보 자료나 투자 판단 결과를 뜻하지 않습니다. 가설은 앞으로 일어날 일을 검증 가능한 문장으로 적은 예상이고, 주장은 기업이 문서에서 실제로 발표한 내용입니다. 시스템은 이 둘을 서로 다른 기록으로 저장합니다.'),
 H('현재 사용자가 발표를 검토하는 과정'),
 P('기업 A가 이번 분기의 매출 실적을 발표했다고 가정합니다. 현재 시스템의 검토 카드는 발표에서 선택한 실적 표의 정보를 원문 위치와 연결하고, 같은 기준의 이전 값이 있으면 비교 결과를 보여줍니다. 사용자는 기간과 사업 범위를 확인한 뒤 이 발표가 자신의 분석에 어떤 의미가 있는지 판단합니다. 다만 그 판단을 가설의 한 버전으로 저장하고 후속 실적과 연결하는 흐름은 아직 없습니다.'),
 H('변경 후 사용자가 가설을 관리하는 과정'),
 L('1  사용자는 이번 실적과 회사의 다음 분기 전망을 검토한 뒤 “기업 A의 다음 분기 매출이 전년 같은 분기보다 증가할 것이다”라는 가설을 작성합니다. 회사·사업 범위·실제 대상 기간·지표 정의와 판정 조건을 함께 정합니다.'),
 L('2  사용자는 기업의 전망 주장과 원문 근거를 가설에 연결합니다. 전망을 지지하는 근거뿐 아니라, 수요 둔화나 고객 집중처럼 반박하거나 추가 확인이 필요한 근거도 기록합니다.'),
 L('3  새로운 발표가 나오면 시스템은 기존 가설과 관련된 주장을 찾아 보여줍니다. 사용자는 가설을 유지·수정·보류할지 판단하고, 이유와 사용한 근거를 새 버전으로 남깁니다.'),
 L('4  대상 분기의 실적이 발표되면 시스템은 처음 정한 조건과 실제 지표를 비교합니다. 기간이나 사업 범위가 다르면 결과를 억지로 확정하지 않고 판정 불가 이유를 보여줍니다.'),
 L('5  사용자는 과거 버전의 근거와 이후 결과를 나란히 확인합니다. 실제로 매출이 증가했더라도, 특정 고객 때문에 증가했다는 인과관계나 주가 상승까지 자동으로 인정하지 않습니다.'),
 H('사용자가 직접 판단해야 하는 부분'),
 P('시스템이 원문을 연결하거나 계산을 수행한 것과 사용자가 분석을 채택한 것은 구분합니다. 가설의 내용과 판정 조건은 검토 가능한 초안으로 시작할 수 있지만, agent가 만든 초안을 사람의 독립 판단이나 정답으로 저장하지 않습니다. 실제 작성자와 검토 상태를 표시한 뒤, 사용자가 채택하거나 수정한 이력을 남깁니다.'),
 P('과거 자료를 보고 오늘 작성한 가설은 사후 재구성으로 표시합니다. 이렇게 해야 당시 실제로 작성한 예상과 결과를 알고 나서 다시 구성한 설명을 구분할 수 있습니다.')
]);

page('3 현재 완료한 개발과 남아 있는 검증', [
 P('최신 활성 실행은 P08의 integration_012와 P09의 evaluation_005입니다. P08은 추출·비교·검토 사유·카드·피드백 결과를 한 배치로 연결했고, P09는 그 구현의 계약·재현·실패 처리를 검사했습니다. 두 단계의 상태는 개발 완료·게시 완료이며, 정식 연구 평가는 미완료입니다. [S1 S2]'),
 T(['집계 단위','현재 기록','이 수치를 읽는 방법'],[
 ['숫자 분석 자료','Microsoft 실적 발표 2문서와 발표 family 2개','같은 개발 노출 그룹입니다. 발표 family는 하나의 독립 발표를 기준으로 묶은 단위입니다.'],
 ['보관 원본','실적 발표 2개와 사업 범위 참고 연차보고서 1개','원본 3개와 숫자 표본 2문서의 분모는 다릅니다.'],
 ['추출 후보와 카드','숫자 33개와 보고 사업부 관계 6개를 카드 33개로 연결','후보 39개가 독립 사건 39개라는 뜻은 아닙니다. 관계는 숫자와 근거를 공유합니다.'],
 ['개발 검증','공학 12개와 합성·장애·평가 조건 37개 통과','프로그램 계약과 반례 검사입니다. 새 자료 정확도나 투자 효용의 점수가 아닙니다.'],
 ['사람과 독립 자료','사람이 만든 평가용 정답인 gold·독립 test·검색 정답·사람 세션 각각 0','추출 정확도, 검색 성능, 중요성, 검토시간 절감은 미평가입니다.'],
 ['실행 시간과 비용','P08 단계 합계 약 3.067초와 외부 API·LLM 호출 0회','2문서의 로컬 측정입니다. 전체 비용·메모리 peak·1000문서 비용은 미측정입니다.']
 ],[1710,3420,4280]),
 H('과거 시점에서 비교할 수 있는 범위'),
 T(['시점 모드','변화 계산과 시도','공식 계산과 시도'],[
 ['현재 자료로 재검토','15건 계산 / 42건 시도','8건 계산 / 8건 시도'],
 ['당시 공개 정보 기준','3건 계산 / 42건 시도','0건 계산 / 8건 시도'],
 ['시스템 관측 기준','0건 계산 / 42건 시도','0건 계산 / 8건 시도']
 ],[4110,2650,2650]),
 P('당시 공개 모드의 계산 3건은 같은 발표 안의 사업부 비교열입니다. 과거 발표를 검색해 얻은 성능이나 미래 가설 검증 성공 건수로 해석하면 안 됩니다. 정확 발표시각, 사업부 정의 변경, 사후 scope 문맥, 관계 유효기간, 전체 본문 완전성은 아직 미확인입니다. [S3]')
]);

page('4 P01부터 P09까지의 현재 진행 상태', [
 P('P01부터 P09는 설계서의 순번입니다. 실제 단계 번호는 Phase 0부터 Phase 8이고, 결과 폴더도 p0부터 p8을 사용합니다. 따라서 P08의 결과는 p7에, P09의 결과는 p8에 있습니다. 아래 표는 현재 구현과 결과를 요약하며, 계획서의 모든 연구 종료 조건을 달성했다는 뜻은 아닙니다.'),
 T(['단계','현재 구현과 결과','남아 있는 조건'],[
 ['P01 자료 조사','접근 실패를 보존하고 Microsoft의 제한된 숫자·라벨·기간·위치 참조를 확보했습니다.','전 기간 수집, 다른 기업 접근, 전체 본문 감사는 미완료입니다.'],
 ['P02 스키마','주장·문서·수정본·발표 family와 원문값·판단·계산 계약을 작성했습니다.','사람이 새 사례에 독립적으로 양식을 적용하는 시험은 미완료입니다.'],
 ['P03 등록부','숫자 33개와 보고 사업부 관계를 적용하고, 비교 21쌍 중 15쌍을 계산했습니다.','고객·공급·경쟁 관계와 다른 기업에 대한 검증은 미완료입니다.'],
 ['P04 주석','39개 개발 항목에 agent 주석·검토·노출 분할을 적용했습니다.','사람 gold와 독립 test는 0건입니다. 예약 문서 본문은 열지 않았습니다.'],
 ['P05 추출','미리 선정한 표 셀을 처리하는 규칙 baseline과 39개 후보를 만들었습니다.','전체 본문에서 중요한 사건을 발견하는 성능과 새 자료 정확도는 미평가입니다.'],
 ['P06 검토 목록','39개 후보에 검토 사유를 붙이고 P07 변화 결과를 연결했습니다.','학습된 중요성 모델과 recall·확률 보정은 미실행입니다.'],
 ['P07 검색과 비교','세 시점 모드의 검색·호환 검사·변화·공식 계산과 중단 처리를 구현했습니다.','독립 검색 정답, 실제 가정 입력, 완전한 재무 대사는 없습니다.'],
 ['P08 통합','배치·실패 재개·카드 33개·파일 피드백 검증과 충돌 이력을 구현했습니다.','사람 피드백과 메모는 0건이며, 팀원 재실행은 미실행입니다.'],
 ['P09 평가','같은 개발 입력의 목록·카드 비교, 공학·재현·전체 보류 결과 보고를 완료했습니다.','정식 정확도·사람 사용성·검토시간 절감·투자 효용은 미평가입니다.']
 ],[1490,4040,3880]),
 P('초기 P01 보고서의 실제 자료 0건은 당시 접근 실패 기록입니다. 현재 입력은 이후 확보한 available_20261005의 manifest를 기준으로 읽어야 합니다. 과거 실패를 현재 성공으로 덮어쓰거나, 과거 문서를 최신 상태로 소급 수정하지 않습니다. [S4 S5 S6 S7]')
]);

page('5 전체 프로젝트의 방향과 최초 제작 범위', [
 P('현재 프로젝트는 새 기업정보에서 달라진 점을 찾아 사람이 검토할 항목을 정리하는 도구입니다. V2에서는 이 기능을 계속 사용하면서, 검토 결과가 어떤 가설을 바꾸었는지와 그 가설의 이후 결과를 기록합니다. 제안하는 주제는 “공개 기업정보의 시점과 근거 기반 구조화 및 투자 가설 추적과 검증 시스템”입니다.'),
 T(['설계 관점','현재 V1','제안하는 V2'],[
 ['핵심 질문','새 발표에서 무엇이 달라졌고, 무엇을 확인해야 하는가','당시 근거가 어느 가설을 지지·반박했고, 이후 결과가 어땠는가'],
 ['온톨로지 역할','기업·지표·범위·관계의 의미를 통일하고 비교 조건을 정함','기존 역할에 더해 가설의 근거와 결과를 일관된 의미로 연결함'],
 ['기록의 중심','주장 후보, 이전 정보, 변화 결과, 검토 카드','기존 기록에 가설 버전, 근거 연결, 판단 이력, 사후 결과를 추가함'],
 ['평가의 중심','프로그램 계약·재현과 앞으로 수행할 정확도·검토 효용','기술 정확도·사람 검토 효용·가설 결과를 각각 평가함'],
 ['팀의 학습 목표','온톨로지·NLP 적용과 사업 분석, 개인 재무 분석 경험','같은 목표를 유지하며 가설 작성·반대 근거·후속 검증으로 구체화함']
 ],[1710,3760,3940]),
 H('첫 번째 V2에서 완성할 범위'),
 P('기업 한 곳의 허용된 연속 발표 자료와 가설 하나를 선정합니다. 가설 작성, 당시 근거 연결, 후속 발표에 따른 판단 수정, 대상 기간 실적의 판정까지 끝까지 이어지는지 확인합니다. Microsoft의 기존 표본은 계속 회귀 검사에 사용하고, 새 자료는 별도 입력과 실행에 등록합니다.'),
 P('이 흐름을 확인한 뒤 관계가 연결된 소수 기업으로 확장하는 것을 제안합니다. 3~5개 기업은 후속 범위 제안이며 확보된 기업 수가 아닙니다. 튜닝 문서의 30~50개 기업, confidence 0.82, 과거 사례 23건도 현재 확보나 검증된 확률을 뜻하지 않습니다.'),
 P('컨센서스, 주가 반응, 매매, 포트폴리오 판단은 별도 후속 범위로 둡니다. 사업 지표의 예상이 맞았는지와 투자 수익이 발생했는지는 다른 질문이므로, 첫 V2의 완료 기준에 한꺼번에 포함하지 않습니다. [S8 S9]')
]);

page('6 전체 시스템에서 유지하고 확장할 기능', [
 P('시스템은 현재의 자료 등록·추출·비교·검토·카드 흐름을 유지합니다. 새로 추가하는 가설 기능은 기존 원문 주장을 참조하고, 판단 변경과 결과 기록을 연결합니다. 같은 숫자를 여러 파일의 별도 진실 원본으로 복제하지 않도록 주장 ID와 수정본 ID를 공통 참조로 사용합니다.'),
 T(['기능','유지할 기반','추가할 처리'],[
 ['자료 등록','출처 권리와 문서·수정본·해시·실패 기록','연속 발표와 가이던스 수정·후속 실적의 coverage 관리'],
 ['정보 추출','원문 위치, 숫자·단위·기간·사업 범위','전망·계획·조건·부정·화자와 필요한 정성 관계 추출'],
 ['의미 연결','지표·개체·별칭·단위·정의 등록부','가설 대상 지표와 결과 지표, 실제 사업 관계의 시점 연결'],
 ['시점 검색','공개·관측·현재 검토 모드와 제외 사유','가설 버전별로 사용할 수 있었던 근거 집합 복원'],
 ['검토 사유','불확실성과 비교 불가, 추가 질문','어느 가설의 어떤 가정을 다시 확인해야 하는지 제시'],
 ['가설 관리','기존 가정·메모 참조 계약 활용','가설·판정 조건·버전·지지와 반박 근거·작성 방식 저장'],
 ['판단과 결과','피드백 journal과 계산 입력·공식 이력','유지·수정·보류 결정 및 대상 기간 실적 판정 기록'],
 ['화면과 게시','현재 카드와 평가 화면, 안전한 snapshot','가설 목록·타임라인·시점별 근거·사후 결과 조회'],
 ['검증과 평가','기존 회귀·재현·실패 보존','새 입력 manifest 검사와 V2의 독립 평가 protocol']
 ],[1460,3720,4230]),
 H('새 자료를 받기 전에 바꿔야 할 실행 계약'),
 P('현재 P08은 source_run을 m0_004로, cutoff를 2026-10-06으로 제한합니다. P09도 입력 문서 2개·family 2개·후보 39개를 전제로 검사합니다. 이 조건은 현재 V1을 재현하는 규칙으로 보존합니다. V2에서는 등록된 새 입력과 정책 버전을 받아 실제 건수와 분모를 계산하는 adapter와 검증기를 별도로 만듭니다. [S10]'),
 P('기존 동결 검사를 통과시키려고 manifest나 결과를 다시 만들지 않습니다. 새 기능은 별도 코드 경로·스키마 버전·Phase별 새 run으로 구현하고, V1 회귀 검사는 고정된 기준 결과를 확인하는 역할로 유지합니다.')
]);

page('7 가설과 근거와 결과를 저장하는 방식', [
 P('원문 주장은 기업이 실제로 발표한 내용이고, 가설은 그 주장을 이용해 사용자가 세운 예상입니다. 가설이 주장과 다른 층에 있어야 기업의 전망을 사용자의 결론으로 잘못 바꾸지 않습니다. V2는 아래 기록을 기존 주장·관계·계산·카드 ID에 연결하는 구조를 제안합니다.'),
 T(['새 기록','담을 내용','다른 기록과의 연결'],[
 ['가설과 버전','대상 기업·범위·지표·기간, 예상 방향 또는 기준, 반박 조건, 판정 시점, 작성자·시각·방식','이전 가설 버전을 보존하고 새 버전과 연결합니다.'],
 ['가설과 근거 연결','지지·반박·조건·배경 구분, 판단자·이유·작성 시각, 당시 사용 가능 여부','원문 claim과 revision, 근거 위치를 참조합니다.'],
 ['판단 변경','유지·수정·보류 결정, 결정 이유, 사용한 근거, 이전·새 버전','원래 가설과 검토 카드·피드백 이력에 연결합니다.'],
 ['사후 결과','실제 대상 지표·기간·정의, 발표 근거, 판정 규칙 버전, 결과와 비교 불가 이유','평가한 가설 버전과 후속 실적 claim을 연결합니다.']
 ],[1710,4320,3380]),
 H('주장과 가설의 관계는 여러 개를 허용'),
 P('하나의 주장은 여러 가설에 사용될 수 있고, 하나의 가설은 여러 발표의 근거를 사용할 수 있습니다. 따라서 가설과 근거는 별도 연결 기록으로 관리합니다. 같은 주장이 가설 두 개에 연결됐다고 고유 주장 수를 두 배로 세지 않습니다. 기존 후보와 카드의 집계 단위도 유지합니다.'),
 H('실제 관계와 영향 해석의 구분'),
 P('회사가 공급 관계를 발표한 경우에는 그 관계 주장과 원문 근거를 기록합니다. “공급사가 매출 증가의 수혜를 받을 것이다”라는 설명에는 추가 가정이 필요하므로 가설이나 해석으로 저장합니다. 관계가 있다는 사실만으로 매출 기여도나 영향 규모를 생성하지 않습니다.'),
 H('판정 상태와 검토 상태의 구분'),
 P('가설은 판정 조건 준비 여부, 운영 중인지 보류·철회됐는지, 결과 판정이 가능한지를 각각 표시합니다. 근거의 사람 검토 상태는 별도입니다. 자동 계산이 성공했다고 사람이 검토한 상태로 바꾸지 않으며, 결과가 아직 발표되지 않은 가설은 판정 대기로 남깁니다.'),
 P('필드와 상태 이름은 P02의 새 계약에서 실제 사례로 검증한 뒤 고정합니다. 현재의 단순 confidence 예시를 확률로 채우기보다는 작성 주체·근거 충분성·미확인 사유를 먼저 저장합니다.')
]);

page('8 과거 시점의 판단을 재현하는 원칙', [
 P('과거 판단을 재현하려면 사건의 대상 기간과 정보가 공개된 시점을 구분해야 합니다. 예를 들어 2025년 실적을 설명하는 문서를 2026년에 읽었다면, 대상 기간은 2025년이고 시스템이 읽은 시점은 2026년입니다. 대상 기간이 과거라는 이유만으로 그 문서를 당시 시스템이 알고 있었다고 기록하지 않습니다.'),
 T(['시간 또는 모드','의미','V2에서 확인할 내용'],[
 ['대상과 적용 기간','실적이 발생한 기간 또는 계획이 적용될 기간','가설과 실제 결과가 같은 기간·사업 범위를 다루는지 확인합니다.'],
 ['공개 시점','출처에서 정보를 공개한 시점','정확 시각과 날짜만 아는 경우를 구분합니다. 미상 시각을 만들지 않습니다.'],
 ['시스템 관측 시점','시스템이 실제로 자료를 읽은 시점','늦게 수집한 문서를 과거 실시간 결과에 넣지 않습니다.'],
 ['가설 작성과 수정 시점','사용자나 agent가 가설을 기록한 시점','당시 작성과 사후 재구성을 구분하고 이전 버전을 보존합니다.'],
 ['당시 공개 정보 모드','해당 시점에 공개돼 있었다는 근거가 있는 자료 사용','원문뿐 아니라 필요한 정의·scope·관계 문맥도 당시 사용 가능했는지 확인합니다.'],
 ['시스템 관측 모드','공개 조건과 실제 관측 조건을 모두 만족','시스템이 당시 사용한 자료와 정책으로 판단을 복원합니다.'],
 ['현재 재검토 모드','현재 확인할 수 있는 자료로 사후 검토','사후 자료와 작성 방식을 표시하고 당시 실시간 성과로 보고하지 않습니다.']
 ],[1820,3300,4290]),
 P('가설 버전마다 사용한 근거·문서 수정본·등록부 정의·계산식·정책의 버전을 고정합니다. 이렇게 해야 새로운 정의나 정정 자료가 들어왔을 때 과거 판단이 조용히 바뀌는 일을 막을 수 있습니다. 나중에 알게 된 결과는 평가 화면에 연결하되, 과거 가설의 입력 근거에는 넣지 않습니다.'),
 P('발표 날짜만 확인됐으면 일 단위 비교까지만 수행합니다. 같은 날 발표의 순서를 알 수 없거나 필요한 문맥의 공개시점이 미상인 경우에는 보류합니다. 정확 시각을 확보하지 못한 상태에서 장중 투자 판단을 재현했다고 보고하지 않습니다.')
]);

page('9 같은 사이트에서 사용하고 검토를 반영하는 과정', [
 P('기본 운영 방식은 V2에서도 유지합니다. 소유자는 PC에서 등록된 자료를 처리하고 결과를 검증한 뒤, 허용된 결과를 같은 사이트에 게시합니다. 지정 사용자는 그 게시 결과를 보고 검토 파일을 내보냅니다. 소유자가 파일을 가져와 검증하고 새 결과를 게시해야 공유 화면에 검토가 반영됩니다.'),
 T(['사용 위치','현재 사용할 수 있는 기능','V2에서 추가할 기능'],[
 ['소유자 PC','고정 입력 배치, 실패 재개, 파일 가져오기와 충돌 처리','등록된 새 입력 처리, 가설 버전과 판단·결과 기록 검증'],
 ['공유 사이트','통합 카드·원문 위치·시점별 비교·검토 질문·개발 평가 조회','가설 목록·상세·타임라인, 당시 근거와 사후 결과 조회'],
 ['사용자 기기','검토 초안 보관과 구조화 파일 내보내기','가설 관련 검토 초안·근거 연결·판단 제안의 파일 내보내기'],
 ['소유자 반영','가져온 파일 검증, 중복·충돌 이력, 새 snapshot 게시','가설·카드 버전 불일치와 판정 조건 수정 충돌까지 검사']
 ],[1560,3790,4060]),
 H('기존 게시 상태와 새 기능의 게시 조건'),
 P('현재 사이트는 corporate-research-p05.sooobeo.chatgpt.site이며, P08·P09 게시 manifest에는 버전 4의 배포 상태 succeeded와 2026년 10월 7일 13시 58분 KST가 기록돼 있습니다. 기록상 접근 계정 수는 2이고 접근 범위를 변경하지 않았습니다. 팀원의 실제 접속은 미확인입니다. 로컬 브라우저의 주요 흐름 확인과 게시 페이지의 직접 확인은 서로 구분합니다. [S11]'),
 P('V2에서도 기존 프로젝트와 지정 사용자 접근을 유지합니다. Phase 기능을 추가할 때 결과 내보내기 adapter·스키마·화면·게시 기록을 함께 갱신하고, 같은 프로젝트의 배포 성공을 확인합니다. 로컬 파일 수정이나 GitHub push만으로 사이트 반영 완료라고 보고하지 않습니다.'),
 H('공유할 수 있는 정보의 범위'),
 P('공유 데이터에는 허용된 숫자·표준 라벨·기간·원문 위치와 추적 가능한 결과를 포함합니다. 제한 원문 prose, private 파일, 키·토큰, 개인 메모와 검증되지 않은 자유입력은 기본 게시 대상에서 제외합니다. 자유롭게 작성한 가설 설명을 공유하려면 작성 주체·검토 상태와 게시 허용 범위를 먼저 정해야 합니다.'),
 P('브라우저 초안은 공동 영속 저장이 아닙니다. 별도 DB·새 ID와 비밀번호 저장소·공유 사이트의 원격 Python 실행은 이번 V2의 기본 운영에 추가하지 않습니다. [S12]')
]);

const phases = [
{
 id:'P01',name:'가설 검증에 필요한 자료 조사와 수집',current:'초기 SEC 접근 실패를 남긴 뒤 Microsoft의 실적 발표 2개와 scope 참고 연차보고서 1개를 확보했습니다. 선택 숫자 33개와 기간·배율·위치의 대조는 수행했지만 전체 본문 완전성은 감사하지 않았습니다. 원문 AI 이용이나 다른 기업의 접근을 검증한 상태도 아닙니다. [S4 S5]',why:'V1의 두 실적 발표는 선택 숫자를 비교하는 데 사용했습니다. V2에서 처음 예상한 내용과 후속 결과를 연결하려면 같은 기업의 연속 발표, 전망 수정, 대상 기간 실적이 필요합니다. 먼저 가설에 필요한 자료를 정하고 그 자료의 사용 조건을 확인해야 합니다.',tasks:[
 ['1','최초 질문과 기간 선정','P02와 함께 기업 한 곳과 검증할 가설을 고릅니다. 대상 지표·사업 범위·기간과 필요한 선행·후속 발표를 coverage 표에 적습니다.'],
 ['2','출처와 권리 확인','조회·자동 접근·저장·내부 분석·AI·외부 전송·공유 조건을 각각 확인합니다. 미확인 본문의 대량 수집과 AI 분석을 진행하지 않습니다.'],
 ['3','새 자료 별도 등록','새 manifest와 run에 문서·수정본·발표 family, 공개·관측·대상 시점, hash와 실패 이유를 기록합니다. 예약 문서는 용도를 고정하기 전에 열지 않습니다.'],
 ['4','원문과 시점 감사','제목·본문·표 머리글·숫자·기간·scope·날짜를 대조합니다. 누락·혼입·공개시점 미상을 확인하고, 정확 시각은 확인된 경우에만 기록합니다.']
],outputs:'새 scope와 연속 기간 coverage 표, source registry, document manifest, 원문·시점 감사표를 만듭니다. 이는 기존 p0 파일을 덮어쓰지 않는 새 실행 산출물입니다.',done:'후보 발견·접근·본문 확보·범위 적합·사용 가능한 근거의 수와 실패 이유가 각각 연결돼야 합니다. 최초 가설의 선행 자료와 후속 결과를 확보했거나, 아직 없는 자료와 판정 대기 이유를 명시해야 합니다.',dependency:'P02의 가설 질문과 함께 범위를 정합니다. 사용 가능한 자료와 위치를 P03·P04·P05에 전달합니다.',site:'자료 coverage와 공개시점 정밀도, 접근 실패·미확인 상태를 게시 허용 범위 안에서 보여줍니다.'
},
{
 id:'P02',name:'가설과 근거와 결과의 기록 계약',current:'문서·주장·관계·수정본·발표 family를 구분하고, 원문값·정규화값·판단·계산을 나누는 스키마를 작성했습니다. 최초 합성 계약 검사 28개는 통과했지만 사람의 새 사례 독립 양식 시험은 미완료입니다. 후속 실자료 적용을 최초 P02 완료 사실로 소급하지 않습니다. [S4 S6]',why:'현재 계약은 원문 주장과 비교 결과를 표현할 수 있습니다. V2에서는 사용자의 예상, 예상에 대한 근거 판단, 판단 변경, 이후 결과를 함께 저장해야 하므로 각각의 의미와 필수 조건을 먼저 정해야 합니다.',tasks:[
 ['1','가설과 버전 정의','회사·scope·지표·대상 기간·예상 기준·반박 조건·판정 시점·작성자·작성 시각을 정의합니다. 조건이 부족하면 검증 준비 미완료로 둡니다.'],
 ['2','근거 연결 정의','지지·반박·조건·배경 관계와 판단 이유를 기록합니다. claim·revision·위치 참조와 연결을 만든 주체·시점을 함께 둡니다.'],
 ['3','판단과 결과 정의','유지·수정·보류 결정과 이전 버전을 연결합니다. 실제 결과, 판정 규칙, 비교 불가·미발표·철회 상태를 구분합니다.'],
 ['4','실제 사례와 반례 확인','당시 작성과 사후 재구성, 전망과 실적, 결과를 본 뒤 조건 수정, 근거 없는 연결을 정상·오류 사례로 검사합니다.']
],outputs:'가설·버전·근거 연결·판단·결과의 새 스키마, 필드 설명, 작성 가이드, 실제 사례와 반례, 계약 변경 기록을 만듭니다.',done:'처음 보는 사람이 각 기록의 의미와 연결을 설명할 수 있어야 합니다. 조건 없는 가설을 판정하거나, 사후 재구성을 당시 예상으로 표시하거나, 계산 성공을 사람 검토로 승격하는 오류를 차단해야 합니다.',dependency:'P01의 허용된 실제 자료로 예시를 작성합니다. 고정한 새 계약을 P03부터 P09까지 공통 입력으로 전달합니다.',site:'사용자 화면에서 가설·회사 주장·사람 판단·계산 결과가 구분되도록 필드와 표시 규칙을 정합니다.'
},
{
 id:'P03',name:'지표와 기업 관계의 의미와 비교 조건',current:'지표·개체·별칭·단위 등록부를 만들고 Microsoft 숫자 33개와 보고 사업부 관계 주장 6개에 적용했습니다. 기존 비교 21쌍 중 15쌍을 계산하고 정의가 다른 6쌍을 차단했습니다. 보고 사업부 관계는 고객·공급 관계가 아닙니다. [S5]',why:'가설의 예상 지표와 후속 실적이 같은 이름을 사용하더라도 기간·사업 범위·회계 정의가 다를 수 있습니다. V2는 이 차이를 확인한 뒤 결과를 판정해야 합니다. 기업 간 영향 가설도 실제 관계 근거와 별도로 연결해야 합니다.',tasks:[
 ['1','가설 대상 지표 등록','예상·수정 전망·실적이 사용하는 지표 정의와 단위·기간·회계 기준을 연결합니다. 회사 발표 지표와 프로젝트 계산 지표는 구분합니다.'],
 ['2','필요한 관계 확장','실제 자료가 지지하는 제품·고객·공급 관계만 추가합니다. 회사·사업부·제품 ID, 관계 방향·역할·적용 범위를 확인합니다.'],
 ['3','유효기간과 정의 이력','관계와 정의의 유효기간, 근거 공개·관측 시점, registry 버전을 기록합니다. 미상 날짜를 발표일로 채우지 않습니다.'],
 ['4','사실과 수혜 해석 분리','공급 관계 주장은 사실 층에, 수혜 예상과 영향 규모는 가설·판단·계산 층에 둡니다. 동일 이름의 정의 변경과 비호환 지표 반례를 검사합니다.']
],outputs:'새 metric·entity·relation·alias registry와 정의 이력, 가설 지표와 결과 지표의 연결표, 비교 규칙과 적용 로그를 만듭니다.',done:'같은 이름의 다른 지표나 사업 범위를 자동으로 합치지 않아야 합니다. 미공개 고객을 추측하지 않고, 관계 존재만으로 매출 영향을 생성하지 않아야 합니다. 모든 채택 정의와 관계에 근거 또는 미확인 사유가 있어야 합니다.',dependency:'P02 계약과 P01 자료를 사용합니다. 정의·별칭을 만든 자료는 P04에서 개발 노출로 기록하고 P05·P07에 버전을 전달합니다.',site:'기업 관계와 가설의 근거를 조회할 때 정의·scope·시점과 사실 또는 해석의 구분을 함께 보여줍니다.'
},
{
 id:'P04',name:'사람 주석과 독립 평가 자료 준비',current:'공유 개발 항목 39개에 agent A와 B의 주석·검토·분할 기록을 만들었습니다. 두 발표는 같은 개발 노출 그룹이고, 사람 gold·독립 train·dev·test는 0입니다. FY2026 Q1은 메타데이터만 예약됐으며 본문은 열지 않았습니다. [S7]',why:'V2의 추출 정확도와 가설 근거 연결을 평가하려면 개발에 쓰지 않은 자료와 사람 판단이 필요합니다. 운영 중 카드에 남긴 피드백과 평가용 정답은 목적과 노출 조건이 다르므로 구분해야 합니다.',tasks:[
 ['1','평가 질문과 표집 고정','사실 추출, 근거 연결, 결과 판정 중 무엇을 평가할지 정합니다. 자료를 열기 전에 권리·용도·발표 family·노출 상태와 표집 기준을 고정합니다.'],
 ['2','세 주석 양식 구분','원문 사실, 가설 지지·반박 판단, 실제 결과 판정을 별도 양식으로 작성합니다. 가설 당시 판단에는 후속 결과를 제공하지 않습니다.'],
 ['3','독립 기록과 조정 보존','사람이 실제 독립 작성한 원본과 이견·조정 이유를 남깁니다. agent 참조와 협의 후 기록을 독립 사람 gold로 바꾸지 않습니다.'],
 ['4','노출과 분할 감사','같은 발표의 번역·정정·전재가 평가 양쪽에 갈라지지 않도록 합니다. 이미 본 자료·피드백·연습은 독립 test에서 제외합니다.']
],outputs:'새 sampling protocol, annotation guide, exposure와 split manifest, 사람 주석·조정 기록, 평가 가능 항목과 제외 이유를 만듭니다.',done:'정식 평가로 표시한 항목은 목적에 맞는 독립 자격과 사람 기록이 있어야 합니다. 독립 자료가 없으면 개발은 계속하되 해당 지표를 미평가로 남깁니다. 기억으로 알게 된 사후 정보 등 판단 제한도 기록합니다.',dependency:'P02·P03 정의를 먼저 고정합니다. 정답과 노출 조건은 P05·P06·P07·P09 평가에 전달하고 운영 피드백과 분리합니다.',site:'사람 검토·agent 참조·독립 평가의 수와 상태를 별도로 보여주며, 피드백을 저장했다고 gold가 생긴 것으로 표시하지 않습니다.'
},
{
 id:'P05',name:'새 자료와 전망과 정성 관계의 추출',current:'미리 고른 표 셀과 머리글을 처리하는 규칙 baseline을 구현했습니다. 숫자 33개와 보고 사업부 관계 6개가 기존 agent 참조와 일치했고, 같은 입력 재실행의 의미도 같았습니다. 전체 문서에서 중요 사건을 자동 발견하는 정확도는 아직 평가하지 않았습니다. [S6]',why:'가설을 추적하려면 실적 숫자뿐 아니라 전망·계획·조건·부정·관계 변화가 필요합니다. 따라서 현재 선택 셀 baseline을 보존하면서 새로운 자료 형식과 주장 유형을 받는 추출 경로를 추가해야 합니다.',tasks:[
 ['1','새 입력 adapter 추가','등록된 문서·revision·block과 권리 정보를 받아 새 추출 입력을 만듭니다. 특정 V1 run과 셀 목록에 맞춘 계약과 구분합니다.'],
 ['2','숫자와 전망 구조화','값·단위·통화·배율·실제 기간·scope·화자·actual 또는 forecast·plan을 기록합니다. 회사 전망과 실제 실적을 섞지 않습니다.'],
 ['3','조건과 관계 추출','부정·조건부 설명과 필요한 정성 관계를 기록합니다. 제품 개발·검증·양산·출하를 각각의 단계로 유지하고 미연결 개체는 미상으로 둡니다.'],
 ['4','누락과 잘못 추가된 항목 감사','새 소표본을 원문과 대조하고 근거 위치·offset 왕복을 검사합니다. 실패·부분 추출·미확인 결과도 입력 ID에 연결합니다.']
],outputs:'새 입력 계약과 adapter, 예측·근거·실패 로그, 원문 감사표, 새 유형의 반례와 별도 개발 보고서를 만듭니다.',done:'원문에 없는 주장을 추가하지 않고, 전망을 실적으로 바꾸지 않아야 합니다. 새 자료 검증과 기존 39항목 회귀 일치를 따로 보고합니다. 독립 성능은 P04의 평가 자료가 준비된 범위에서만 측정합니다.',dependency:'P01의 허용 자료와 P02·P03 계약을 사용합니다. 새 출력과 안정 ID를 P06·P07·P08에 연결합니다. 기존 P04·P05 동결 코드는 별도 보존합니다.',site:'기존 선택 셀 결과와 새 자료 결과의 범위·추출 상태를 구분하고, 모든 후보의 원문 위치와 미확인 이유를 확인할 수 있게 합니다.'
},
{
 id:'P06',name:'가설과 연결된 검토 사유와 확인 질문',current:'후보 39개에 검토 사유·누락 정보·확인 질문을 연결하고 P07 변화 feature를 적용했습니다. 시간순과 사유별 목록을 만들었지만 중요성 모델·보정 확률·중요 사건 recall은 미실행입니다. 점수는 null이고 사람 검토 상태는 유지됩니다. [S3]',why:'V1의 질문은 숫자·기간·사업 범위가 맞는지를 확인하는 데 집중합니다. V2에서는 이 검토가 어느 가설의 어떤 가정을 확인하는 작업인지 보여줘야 사용자가 새로운 발표의 의미를 자신의 분석과 연결할 수 있습니다.',tasks:[
 ['1','주장과 가설 후보 연결','기업·scope·지표·기간·관계를 사용해 관련 가설을 찾습니다. 자동 연결은 후보로 남기고 연결 이유와 시점 조건을 제시합니다.'],
 ['2','가정별 확인 질문 작성','기존 검토 사유에 가설의 어떤 근거가 부족한지 연결합니다. 예를 들어 기간 불일치가 가설의 결과 판정을 막는 이유를 설명합니다.'],
 ['3','반박과 충돌 근거 포함','지지하는 변화만 모으지 않습니다. 반박·정의 충돌·조건부 주장과 근거 부족을 별도 사유로 표시합니다.'],
 ['4','정렬과 평가 상태 분리','사유별·시간순 목록의 전체 입력을 보존합니다. 독립 사람 판단과 dev 자료가 없으면 점수·확률·효과 검증은 계속 미평가로 둡니다.']
],outputs:'가설별 검토 항목 sidecar, 연결 이유·누락 필드·확인 질문, 정렬 정책·버전, 연결 반례와 미평가 상태 보고를 만듭니다.',done:'모든 새 입력이 검토 목록 또는 명시적 보류·실패에 연결돼야 합니다. 가설 지지와 반박을 모두 조회할 수 있어야 하며, 목록 위치가 중요성 확률이나 매수 판단으로 바뀌지 않아야 합니다.',dependency:'P05 주장과 P02 가설 계약을 사용합니다. 근거 이용 가능성은 P07로 확인합니다. 최초 기본 사유를 만든 뒤 P07 연결은 별도 새 run으로 갱신합니다.',site:'카드에서 어떤 가설의 무엇을 확인해야 하는지와 연결 후보 여부를 보여줍니다. 근거 부족을 낮은 중요성으로 표시하지 않습니다.'
},
{
 id:'P07',name:'가설 버전별 과거 근거와 후속 실적 비교',current:'세 시점 모드와 exact·희소 검색, 호환 검사, 변화·공식 계산과 중단 처리를 구현했습니다. 현재 재검토에서 변화 15건과 공식 8건을 계산했지만 당시 공개 공식은 0건입니다. 실제 가정 파일은 비어 있고 시나리오와 완전한 재무 대사는 미완료입니다. [S3]',why:'V2에서 과거 가설을 평가하려면 당시 사용할 수 있었던 근거와 이후 실제 결과를 구분해야 합니다. 필요한 정의가 나중에 확인된 경우에는 과거의 판단 가능성을 확정할 수 없으므로, 원문 공개시점만 검사해서는 충분하지 않습니다.',tasks:[
 ['1','가설 버전의 근거 고정','문서·claim revision·registry 정의·정책·수식과 cutoff를 evidence snapshot에 저장합니다. 원문과 문맥의 공개·관측 조건을 검사합니다.'],
 ['2','전망과 후속 실적 연결','최초·수정 전망과 actual을 같은 대상 기간·scope·지표 정의로 연결합니다. 현재 발표의 과거 비교열을 당시 독립 발표로 사용하지 않습니다.'],
 ['3','판정 규칙 실행','사전에 정한 가설 기준으로 결과를 비교합니다. 입력 부족·기간 불일치·정의 변경·미발표 상태에서는 판정 불가 또는 대기를 반환합니다.'],
 ['4','미래 정보와 재구성 검사','미래 정정·관계·정의·결과를 넣어도 과거 입력이 바뀌지 않는지 검사합니다. 현재 재구성과 당시 시스템의 판단을 구분합니다.']
],outputs:'가설별 evidence snapshot, 시점 query와 제외 로그, 전망·실적 연결표, 판정 결과·규칙 버전·비교 불가 이유와 반례를 만듭니다.',done:'과거 근거와 사후 평가 자료를 각각 추적할 수 있어야 합니다. 날짜만 아는 항목에 정확 시각을 만들지 않고, 늦은 관측과 사후 문맥을 당시 실시간 입력에서 제외해야 합니다. 판정 불가 사례도 결과에 남겨야 합니다.',dependency:'P02 판정 계약과 P03 정의, P05 근거를 사용합니다. 결과는 P06 검토 연결과 P08 가설 화면, P09 결과 평가에 전달합니다.',site:'당시 근거·현재 재검토·사후 결과를 구분해 보여주고, 비교·계산·가설 판정의 조건과 미완료 이유를 함께 표시합니다.'
},
{
 id:'P08',name:'가설 화면과 통합 실행과 파일 검토 이력',current:'고정 입력의 추출·비교·검토·카드·피드백 snapshot·검증을 배치로 연결했습니다. 실패 재개·timeout·journal·중복·충돌 처리와 카드 33개를 구현했습니다. 실제 사람 피드백과 메모는 아직 없으며, 공유 사이트는 로컬 실행과 자동 공동 저장을 하지 않습니다. [S1]',why:'새 자료와 가설 기록을 사용자에게 제공하려면 V1의 고정 입력 계약과 새 실행 계약을 분리해야 합니다. 가설 화면을 추가할 때도 기존 카드와 검토 기록의 안정 ID·버전·실패 보존을 유지해야 합니다.',tasks:[
 ['1','새 배치 계약 연결','등록된 V2 입력·schema·registry·정책을 stage key와 manifest에 포함합니다. 변경된 입력은 새 run을 요구하고, 재개 시 출력 hash를 검사합니다.'],
 ['2','가설 조회와 연결 구현','가설 목록·상세·버전 타임라인에 여러 주장과 근거를 연결합니다. 기존 후보→카드 단위와 가설 연결 수를 따로 집계합니다.'],
 ['3','판단 파일과 충돌 처리','가설 유지·수정·보류 제안을 파일로 내보내고 소유자가 검증해 가져옵니다. 오래된 가설·카드 버전, 조건 수정과 중복·충돌 이력을 보존합니다.'],
 ['4','같은 사이트 게시','adapter·스키마·snapshot·화면을 함께 갱신합니다. 미확인·미평가·판정 대기를 유지하고 기존 프로젝트의 배포 성공을 기록합니다.']
],outputs:'새 pipeline 계약·설정·run manifest, 가설·카드 연결표, journal·검토 snapshot, 사이트 adapter·schema·UI와 게시 manifest를 만듭니다.',done:'새 자료에서 가설·근거·판단·결과가 연결되고 부분 실패·재개·중복·충돌 검사가 통과해야 합니다. 기존 동결 결과를 보존하고 같은 사이트의 게시 성공을 확인해야 합니다. 팀원 실제 접속 여부는 별도 기록합니다.',dependency:'P05·P06·P07의 검증된 출력과 P02 계약을 사용합니다. 사람 모델·독립 성능이 없어도 통합 개발을 진행하되 검토 상태를 자동 승격하지 않습니다.',site:'기기 초안, 파일 내보냄, 공유 반영을 구분합니다. 가설의 작성 주체·시점·검토 상태·판정 조건과 결과를 처음 보는 사용자도 읽을 수 있게 설명합니다.'
},
{
 id:'P09',name:'기술 정확도와 검토 효용과 가설 결과의 평가',current:'같은 개발 입력에서 시간순 목록 S0·규칙 목록 S1·통합 카드 S3를 비교했습니다. 공학 12개와 합성·장애·평가 조건 37개를 검사하고 보류 변화 108개·미계산 공식 16개를 보존했습니다. 사람 정답·독립 test·검색 정답·사람 세션은 각각 0건입니다. [S2]',why:'V1은 프로그램이 정해진 입력을 일관되게 처리하는지 검증했습니다. V2의 새 자료 정확도, 사용자 검토에 도움이 되는 정도, 가설의 실제 결과는 각각 다른 평가 질문입니다. 분모와 필요한 정답이 다르므로 하나의 성공률로 합치지 않아야 합니다.',tasks:[
 ['1','새 평가 protocol 고정','결과를 보기 전에 질문·단위·자료·노출·비교군·검토 예산·미상 처리·판정 규칙과 코드·사이트 버전을 고정합니다.'],
 ['2','기술 정확도 측정','P04의 준비된 독립 자료로 숫자·관계·검색·변화·판정 연결을 평가합니다. 기존 회귀와 synthetic 검사는 별도 결과로 보존합니다.'],
 ['3','사람 검토 과업 수행','실제 두 참여자의 원문·카드 과업과 교차 순서, 시간·수정·중단·노출을 기록합니다. agent UI 점검을 사람 세션으로 대체하지 않습니다.'],
 ['4','가설 결과와 전체 분모 보고','전체·판정 가능·대기·보류·철회·미완료 가설을 각각 셉니다. 사업 지표 결과와 주가·매매 수익은 별도 평가로 보고합니다.']
],outputs:'새 evaluation protocol과 동결 manifest, 독립 결과·검토 세션·가설 결과 집계, 비용·시간·오류·재현 보고와 같은 사이트 평가 snapshot을 만듭니다.',done:'실행한 평가의 실제 분모·정답·노출·불확실성을 확인할 수 있어야 합니다. 없는 정답·세션·비용은 null과 미실행 이유를 유지합니다. 목표 미달과 필수 평가 미실행을 구분하고, 같은 사이트의 결과 게시 상태를 기록합니다.',dependency:'P04 독립 자료와 P08 실행·게시 버전을 고정합니다. 미준비 항목은 개발 검증과 분리해 후속 작업으로 남깁니다. 실제 동료 재실행도 별도로 확인합니다.',site:'점수와 함께 표본 단위·평가 조건·사람 수·미실행 항목·실패 사례를 보여줍니다. 가설 결과를 투자 수익률 개선으로 확대하지 않습니다.'
}
];

for (let i=0;i<phases.length;i++) {
 const f=phases[i];
 page(`${10+i} ${f.id} ${f.name}`, [
 H(`${f.id} 현재까지 진행된 내용`),P(f.current),
 H(`${f.id} 변경이 필요한 이유`),P(f.why),
 H('세부 변경 작업'),T(['순서','작업','수행 내용'],f.tasks,[700,2170,6540]),
 H('산출물과 완료 기준'),P(f.outputs),P(f.done),
 H('다른 단계와 화면 연결'),P(f.dependency),P(f.site)
 ]);
}

page('19 변경 작업의 순서와 제작 완료 기준', [
 P('P01부터 P09를 처음부터 다시 수행하기보다, 현재 V1을 기준 결과로 보존하고 아래 작업 묶음으로 V2를 진행하는 것을 제안합니다. 단계별 설계는 이전 장의 상세 작업을 따르며, 사람 정답이 없는 동안에도 개발을 진행할 수 있습니다. 사람 평가에 필요한 조건은 별도 상태로 남깁니다.'),
 T(['작업 묶음','진행 내용','완료를 확인할 증거'],[
 ['1  방향과 계약','현재 상태를 보존하고 최초 가설과 판정 조건, 새 입력·기록·평가 계약을 정합니다.','V1 기준 버전과 V2 scope·schema·평가 목적이 구분됩니다.'],
 ['2  새 자료 처리','허용된 연속 자료를 확보하고 새 adapter·registry·manifest 검사로 처리합니다.','전체 입력과 실패·보류가 연결되고 V1 회귀 결과가 유지됩니다.'],
 ['3  가설 하나 연결','작성·당시 근거·판단 변경·후속 실적 판정을 한 흐름으로 연결합니다.','각 버전과 사용 근거·규칙·결과·판정 불가 사유를 재조회할 수 있습니다.'],
 ['4  사이트와 실제 검토','같은 사이트에 가설 기능을 게시하고 파일 검토 반영과 실제 과업을 수행합니다.','배포 성공, 버전·hash, 파일 반영 이력과 실제 수행 여부가 기록됩니다.'],
 ['5  독립 평가와 확장','준비된 새 정답·과업으로 평가하고 필요한 연결 기업과 관계를 추가합니다.','기술·사람 효용·가설 결과의 분모와 독립 자격이 각각 보고됩니다.']
 ],[1710,3770,3930]),
 H('첫 V2의 개발 완료 기준'),
 P('기업 한 곳의 새 자료에서 가설 하나를 작성하고, 해당 버전의 근거와 판단 변경을 보존하며, 후속 실적을 사전 조건으로 비교할 수 있어야 합니다. 결과가 없거나 비교가 불가능한 경우에도 대기·보류 이유를 반환해야 합니다. 새 실행의 실패 재개·참조·시점·수식·파일 검토를 검증하고 같은 사이트에 기능과 실제 결과를 게시해야 합니다.'),
 H('첫 V2의 정식 평가 완료 기준'),
 P('평가 protocol에 정한 필수 항목을 실제로 수행해야 합니다. 독립 정답이 필요한 정확도, 실제 참여가 필요한 검토 효용, 결과가 필요한 가설 판정을 각각 확인합니다. 하나가 미실행이면 그 부분은 평가 미완료로 남깁니다. 개발 완료와 평가 완료를 따로 기록하는 현재 원칙을 유지합니다.'),
 P('예상 일정·비용·표본 목표는 자료 접근성과 실제 작업량을 확인한 뒤 정합니다. 이 문서는 변경 계획을 정리한 것이며, 제안한 V2 실행이나 새 사이트 게시를 수행한 기록은 아닙니다.')
]);

page('20 함께 갱신할 문서와 쉬운 용어 설명', [
 P('V2를 실행할 때는 코드뿐 아니라 프로젝트 설명과 공통 계약도 함께 갱신해야 합니다. 현재 완료 사실과 향후 제안이 섞이면 새 참여자가 이미 구현된 기능을 잘못 이해할 수 있으므로, 기존 실행 기록은 보존하고 최신 상태와 새 범위를 분명히 연결합니다.'),
 T(['문서 또는 기록','갱신할 내용'],[
 ['README와 structure 목차','현재 V1의 실제 기능·입력 범위와 V2의 사용자 목표를 첫 부분에 설명합니다. 한국기업 과거 기획과 현재 미국기업 범위를 구분합니다.'],
 ['공통 목표와 DATA_CONTRACTS','온톨로지·NLP·사업 분석 목표를 유지하고, 가설·근거·판단·결과·시점·검토 상태 계약을 추가합니다.'],
 ['Phase 설계와 실행 로드맵','기존 완료 상태와 새 작업·의존성·완료 기준을 구분합니다. 과거 실행 전 설명과 최신 실행 기록을 읽는 순서를 명시합니다.'],
 ['튜닝 문서','최초 범위를 가설 하나로 구체화하고, confidence·기업 수·과거 사례 수의 예시 성격을 표시합니다. 매매·포트폴리오는 후속 범위로 정리합니다.'],
 ['사이트 계약과 운영 안내','가설 데이터의 게시 허용 범위와 파일 검토 반영 과정을 추가합니다. 기존 프로젝트·지정 사용자 접근·게시 기록 원칙을 유지합니다.']
 ],[2590,6820]),
 H('이 문서에서 사용하는 용어'),
 T(['용어','뜻'],[
 ['주장 또는 claim','기업이나 화자가 원문에서 실제로 발표한 한 가지 내용입니다. 외부에서 사실 확인이 완료됐다는 뜻은 아닙니다.'],
 ['발표 family','같은 독립 발표에 속하는 문서와 재보도 등을 묶는 단위입니다. 후속 새 발표는 별도 family로 연결합니다.'],
 ['scope','전사·사업부·제품 등 정보가 적용되는 사업 범위입니다. 이름이 같은 숫자라도 scope가 다르면 바로 비교하지 않습니다.'],
 ['adapter와 registry','adapter는 자료를 공통 형식으로 연결하는 처리이고, registry는 지표·개체·정의·별칭을 관리하는 등록부입니다.'],
 ['cutoff와 snapshot','cutoff는 판단에 사용할 수 있는 정보의 기준 시점입니다. snapshot은 특정 입력·버전·시점의 결과를 고정한 묶음입니다.'],
 ['gold와 독립 test','gold는 평가용 정답이며 작성 주체와 절차가 필요합니다. 독립 test는 개발·규칙 선택에 사용하지 않은 평가 자료입니다.'],
 ['사후 재구성','과거 자료를 바탕으로 지금 다시 작성한 가설이나 분석입니다. 당시 실제로 작성한 판단과 구분합니다.']
 ],[2590,6820])
]);

page('21 현재 상태와 변경 제안의 근거 문서', [
 P('현재 상태의 수치와 실행 여부는 최신 활성 run·최종 보고·게시 manifest를 기준으로 확인했습니다. 아래 경로는 저장소 루트에서 시작하는 상대 경로입니다. V2의 작업과 완료 기준은 이 실행 결과와 튜닝 문서에 대한 설계 제안이며, 현재 완료 수치에 합산하지 않습니다.'),
 T(['참조','근거와 확인 내용'],[
 ['S1  P08','artifacts/us_equity/p7/active_run.json\nartifacts/us_equity/p7/execution_briefing.md\nintegration_012의 통합·재개·카드·파일 피드백 구현과 제한'],
 ['S2  P09','artifacts/us_equity/p8/active_run.json\nartifacts/us_equity/p8/runs/evaluation_005/final_report.md\n개발 검증·비교군·실제 분모·미평가 항목'],
 ['S3  P06와 P07','artifacts/us_equity/p5/active_run.json\nartifacts/us_equity/p6/runs/change_002/run_manifest.json\n검토 사유·세 시점 결과·계산과 중단·빈 가정 기록'],
 ['S4  P01과 P02 최초 기록','artifacts/us_equity/execution_briefing.md\nartifacts/us_equity/p1/event_schema.md\n초기 접근 실패와 스키마·사실 판단 계산 분리'],
 ['S5  확보 자료와 등록부','artifacts/us_equity/p0/available_20261005/source_run_manifest.json\nartifacts/us_equity/p0/available_20261005/source_conditions.md\nartifacts/us_equity/p2/execution_briefing.md\n원본·숫자 표본·관계·권리 범위·비교 정의'],
 ['S6  추출과 계약','artifacts/us_equity/p4/execution_briefing.md\nstructure/DATA_CONTRACTS.md\n선택 셀 baseline과 원문·정규화·판단·파생 규약'],
 ['S7  주석과 노출','artifacts/us_equity/p3/dataset_card.md\nartifacts/us_equity/p3/handoff_p3.md\nagent 개발 자료·사람 gold 부재·예약 문서'],
 ['S8  주제 튜닝','financial_ontology_project_topic_tuning.md\n시간축·근거·가설·결과의 방향과 예시'],
 ['S9  공통 목표','structure/GOALS_AND_RESEARCH_WORKFLOW.md\n온톨로지·NLP·사업 분석과 개인 재무 적용 목표'],
 ['S10  고정 실행 계약','scripts/p08_common.py\nscripts/p09_common.py\nV1 입력 run·cutoff·분모·미평가 계약'],
 ['S11  게시 기록','artifacts/us_equity/p8/runs/evaluation_005/site_update_manifest.json\n버전 4 배포 성공·접근 기록·로컬 QA와 미확인 상태'],
 ['S12  운영과 후속 실행','artifacts/us_equity/p7/operator_guide.md\nstructure/SITE_PHASE_UPDATE_CONTRACT.md\nstructure/P06_P09_execution_roadmap.md\n파일 검토·같은 사이트 게시·개발과 연구 상태 구분']
 ],[2280,7130])
]);

const esc = s => String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
function run(text, {bold=false,size=null,color=null}={}) {
 let props = '<w:rFonts w:ascii="Malgun Gothic" w:hAnsi="Malgun Gothic" w:eastAsia="맑은 고딕" w:cs="Malgun Gothic"/>';
 if(bold) props+='<w:b/><w:bCs/>';
 if(size) props+=`<w:sz w:val="${size}"/><w:szCs w:val="${size}"/>`;
 if(color) props+=`<w:color w:val="${color}"/>`;
 return `<w:r><w:rPr>${props}</w:rPr>${String(text).split('\n').map((x,i)=>(i?'<w:br/>':'')+`<w:t xml:space="preserve">${esc(x)}</w:t>`).join('')}</w:r>`;
}
function para(text,style='Normal',{pageBefore=false,keepNext=false,align=null}={}) {
 return `<w:p><w:pPr><w:pStyle w:val="${style}"/>${pageBefore?'<w:pageBreakBefore/>':''}${keepNext?'<w:keepNext/>':''}${align?`<w:jc w:val="${align}"/>`:''}</w:pPr>${run(text)}</w:p>`;
}
function table(item) {
 const widths=item.widths||item.headers.map(()=>Math.floor(9410/item.headers.length));
 const sourceTable=item.headers[0]==='참조';
 const cellPadding=sourceTable?40:70;
 const textStyle=sourceTable?'SourceText':'TableText';
 const borders=['top','left','bottom','right','insideH','insideV'].map(x=>`<w:${x} w:val="single" w:sz="4" w:color="D9D9D9"/>`).join('');
 let xml=`<w:tbl><w:tblPr><w:tblW w:w="9410" w:type="dxa"/><w:jc w:val="center"/><w:tblLayout w:type="fixed"/><w:tblBorders>${borders}</w:tblBorders><w:tblCellMar><w:top w:w="${cellPadding}" w:type="dxa"/><w:left w:w="115" w:type="dxa"/><w:bottom w:w="${cellPadding}" w:type="dxa"/><w:right w:w="115" w:type="dxa"/></w:tblCellMar></w:tblPr><w:tblGrid>${widths.map(w=>`<w:gridCol w:w="${w}"/>`).join('')}</w:tblGrid>`;
 const rows=[item.headers,...item.rows];
 rows.forEach((row,index)=> {
  xml+=`<w:tr><w:trPr><w:cantSplit/>${index===0?'<w:tblHeader/>':''}</w:trPr>`;
  row.forEach((text,c)=> {
   const centered=index===0||(c===0&&widths[c]<=1820);
   xml+=`<w:tc><w:tcPr><w:tcW w:w="${widths[c]}" w:type="dxa"/><w:vAlign w:val="center"/>${index===0?'<w:shd w:fill="E7EBEF"/>':''}</w:tcPr><w:p><w:pPr><w:pStyle w:val="${textStyle}"/>${centered?'<w:jc w:val="center"/>':''}</w:pPr>${run(text,{bold:index===0})}</w:p></w:tc>`;
  });
  xml+='</w:tr>';
 });
 return xml+'</w:tbl>'+para('','TableAfter');
}
let body=para('기업 리서치 시스템의 현재 상태와 변경 계획','Title');
body+=para('사용자 이용 변화와 전체 시스템 및 P01부터 P09까지의 세부 작업','Subtitle');
body+=para('기준일 2026년 10월 7일','Meta');
for(let i=0;i<pages.length;i++) {
 body+=para(pages[i].title,'Heading1',{pageBefore:i>0});
 for(const item of pages[i].items) {
  body+=item.kind==='table'?table(item):para(item.text,item.kind==='h'?'Heading2':item.kind==='list'?'ListText':'Normal');
 }
}
body+='<w:sectPr><w:footerReference w:type="default" r:id="rIdFooter"/><w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="900" w:right="1248" w:bottom="900" w:left="1248" w:header="400" w:footer="420" w:gutter="0"/><w:cols w:space="720"/><w:docGrid w:linePitch="360"/></w:sectPr>';
const ns='xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"';
const style=(id,name,size,{bold=false,after=90,before=0,line=300,keep=false}={})=>`<w:style w:type="paragraph" w:styleId="${id}"><w:name w:val="${name}"/><w:basedOn w:val="Normal"/><w:pPr><w:spacing w:before="${before}" w:after="${after}" w:line="${line}" w:lineRule="auto"/><w:widowControl/>${keep?'<w:keepNext/><w:keepLines/>':''}${id==='Heading1'?'<w:outlineLvl w:val="0"/>':id==='Heading2'?'<w:outlineLvl w:val="1"/>':''}</w:pPr><w:rPr><w:rFonts w:ascii="Malgun Gothic" w:hAnsi="Malgun Gothic" w:eastAsia="맑은 고딕"/><w:color w:val="000000"/><w:sz w:val="${size}"/><w:szCs w:val="${size}"/>${bold?'<w:b/><w:bCs/>':''}</w:rPr></w:style>`;
const styles=`<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:styles ${ns}><w:docDefaults><w:rPrDefault><w:rPr><w:rFonts w:ascii="Malgun Gothic" w:hAnsi="Malgun Gothic" w:eastAsia="맑은 고딕"/><w:sz w:val="21"/><w:szCs w:val="21"/><w:lang w:val="ko-KR" w:eastAsia="ko-KR"/></w:rPr></w:rPrDefault><w:pPrDefault><w:pPr><w:spacing w:after="90" w:line="300" w:lineRule="auto"/><w:widowControl/></w:pPr></w:pPrDefault></w:docDefaults><w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/><w:qFormat/><w:pPr><w:spacing w:after="90" w:line="300" w:lineRule="auto"/><w:widowControl/><w:snapToGrid w:val="0"/></w:pPr><w:rPr><w:rFonts w:ascii="Malgun Gothic" w:hAnsi="Malgun Gothic" w:eastAsia="맑은 고딕"/><w:color w:val="000000"/><w:sz w:val="21"/><w:szCs w:val="21"/></w:rPr></w:style>${style('Title','Title',38,{bold:true,after:120,line:265,keep:true})}${style('Subtitle','Subtitle',22,{after:100,line:270,keep:true})}${style('Meta','Meta',19,{after:220,line:260,keep:true})}${style('Heading1','heading 1',28,{bold:true,after:140,line:275,keep:true})}${style('Heading2','heading 2',22,{bold:true,before:130,after:65,line:275,keep:true})}${style('TableText','Table Text',19,{after:0,line:270})}${style('TableAfter','Table After',4,{after:65,line:240})}${style('ListText','List Text',21,{after:95,line:300})}</w:styles>`;
const files={
 '[Content_Types].xml':'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/><Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/><Override PartName="/word/settings.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.settings+xml"/><Override PartName="/word/footer1.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml"/><Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/><Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/></Types>',
 '_rels/.rels':'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/><Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/><Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/></Relationships>',
 'word/document.xml':`<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document ${ns}><w:body>${body}</w:body></w:document>`,
 'word/styles.xml':styles.replace('</w:styles>',style('SourceText','Source Text',18,{after:0,line:250})+'</w:styles>').replace(/<w:rPr>([\s\S]*?)<\/w:rPr>/g,(m,p)=>`<w:rPr>${p.includes('<w:b/>')?'':'<w:b w:val="0"/><w:bCs w:val="0"/>'}${p}</w:rPr>`).replaceAll('w:sz w:val="21"','w:sz w:val="20"').replaceAll('w:szCs w:val="21"','w:szCs w:val="20"').replaceAll('w:after="65"','w:after="50"').replaceAll('w:after="90"','w:after="65"').replaceAll('w:line="300"','w:line="280"').replaceAll('w:line="270"','w:line="255"').replaceAll('w:before="130"','w:before="100"'),
 'word/settings.xml':`<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:settings ${ns}><w:zoom w:percent="100"/><w:defaultTabStop w:val="420"/><w:updateFields w:val="true"/><w:compat><w:compatSetting w:name="compatibilityMode" w:uri="http://schemas.microsoft.com/office/word" w:val="15"/></w:compat><w:doNotAutoHyphenate/><w:characterSpacingControl w:val="doNotCompress"/></w:settings>`,
 'word/_rels/document.xml.rels':'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rIdStyles" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/><Relationship Id="rIdSettings" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/settings" Target="settings.xml"/><Relationship Id="rIdFooter" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer" Target="footer1.xml"/></Relationships>',
 'word/footer1.xml':`<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:ftr ${ns}><w:p><w:pPr><w:jc w:val="center"/></w:pPr>${run('기업 리서치 시스템 변경 계획   ',{size:16,color:'666666'})}<w:fldSimple w:instr=" PAGE ">${run('1',{size:16,color:'666666'})}</w:fldSimple></w:p></w:ftr>`,
 'docProps/core.xml':'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><dc:title>기업 리서치 시스템의 현재 상태와 변경 계획</dc:title><dc:subject>사용자 이용 변화와 전체 시스템 및 Phase별 세부 변경</dc:subject><dc:creator>프로젝트 문서</dc:creator><dcterms:created xsi:type="dcterms:W3CDTF">2026-10-07T00:00:00Z</dcterms:created></cp:coreProperties>',
 'docProps/app.xml':'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes"><Application>OOXML Document Builder</Application></Properties>'
};
const crcTable=Array.from({length:256},(_,n)=>{for(let k=0;k<8;k++)n=n&1?0xEDB88320^(n>>>1):n>>>1;return n>>>0;});
const crc32=b=>{let c=0xFFFFFFFF;for(const x of b)c=crcTable[(c^x)&255]^(c>>>8);return (c^0xFFFFFFFF)>>>0;};
function zip(entries) {
 const local=[],central=[];let offset=0;
 for(const [name,txt] of Object.entries(entries)) {
  const nb=Buffer.from(name),data=Buffer.from(txt),packed=zlib.deflateRawSync(data),crc=crc32(data);
  const lh=Buffer.alloc(30);lh.writeUInt32LE(0x04034B50);lh.writeUInt16LE(20,4);lh.writeUInt16LE(0x800,6);lh.writeUInt16LE(8,8);lh.writeUInt32LE(crc,14);lh.writeUInt32LE(packed.length,18);lh.writeUInt32LE(data.length,22);lh.writeUInt16LE(nb.length,26);
  local.push(lh,nb,packed);
  const ch=Buffer.alloc(46);ch.writeUInt32LE(0x02014B50);ch.writeUInt16LE(20,4);ch.writeUInt16LE(20,6);ch.writeUInt16LE(0x800,8);ch.writeUInt16LE(8,10);ch.writeUInt32LE(crc,16);ch.writeUInt32LE(packed.length,20);ch.writeUInt32LE(data.length,24);ch.writeUInt16LE(nb.length,28);ch.writeUInt32LE(offset,42);central.push(ch,nb);offset+=lh.length+nb.length+packed.length;
 }
 const cd=Buffer.concat(central),end=Buffer.alloc(22);end.writeUInt32LE(0x06054B50);end.writeUInt16LE(Object.keys(entries).length,8);end.writeUInt16LE(Object.keys(entries).length,10);end.writeUInt32LE(cd.length,12);end.writeUInt32LE(offset,16);
 return Buffer.concat([...local,cd,end]);
}
fs.mkdirSync(path.dirname(OUT),{recursive:true});fs.mkdirSync(BUILD,{recursive:true});
fs.writeFileSync(OUT,zip(files));
fs.writeFileSync(path.join(BUILD,'content.json'),JSON.stringify(pages,null,2));
fs.writeFileSync(path.join(BUILD,'document.xml'),files['word/document.xml']);
console.log(JSON.stringify({output:OUT,sections:pages.length,bytes:fs.statSync(OUT).size,characters:pages.map(p=>JSON.stringify(p)).join('').length}));
