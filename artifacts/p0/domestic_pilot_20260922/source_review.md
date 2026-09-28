# 직접 매체 5개 출처 조건 재확인 — 2026-09-22

사용자가 비상업 연구로 진행하도록 지시한 실행 근거는 별도 user authorization에 둔다. 출처의 이용허락·계약이 확인되었다고 변경하지 않았다. 이 문서는 출처가 게시한 조건의 조사 기록이며 법률적 허용/위법 결론이 아니다.

| 출처 | 자동수집 | 내부 원문 보관·분석 | AI | 원문 공유·재배포 |
| --- | --- | --- | --- | --- |
| HANKYUNG | 사전서면허가 없는 추출 목적 자동수집 명시금지 | 무승낙 복제금지; 일반 분석·inference 세부는 미확인 | 학습 사전동의; inference/embedding은 미확인 | 무승낙 제3자제공 제한 |
| ETNEWS | 이번 정책에서 특정 금지 미발견, unresolved | 정보서비스/인트라넷 DB 계약요구; 소표본 내부연구 적용은 unresolved | 별도 구체조항 미확인 | 사전허가 없는 전재·배포 제한 |
| ZDNET_KR | 특정 금지 미발견, unresolved | 비상업 내부저장·분석의 개별 권한 미확인 | 개별 권한 미확인 | 배포 명시금지, 인용·발췌 별도조건 |
| NEWSPIM | 크롤링·자동수집 명시금지 | 무승낙 복사·DB/데이터셋·기업내부망 사용 제한 | AI학습/ML 금지; inference/embedding 세부미확인 | 원문/일부 복제·게시·전송 제한; 단순URL공유 별도 |
| EDAILY | 특정 금지 미발견, unresolved | 서비스이용외 목적 복제제한; 내부연구 적용은 unresolved | 별도 구체조항 미확인 | 무승낙 제3자제공 제한 |

주요 근거:

- [한국경제 이용약관](https://www.hankyung.com/help/policy?category=%EC%9D%B4%EC%9A%A9%EC%95%BD%EA%B4%80) 제19조는 데이터 추출 목적 봇·크롤러·스크레이퍼 및 수동 프로세스 접근/수집에 서면허가를 요구한다. 제11조3항은 무승낙 복제·타인 제공을 제한한다. 학습 제한을 모든 AI inference에 자동 확대하지 않았다.
- [전자신문 약관](https://info.etnews.com/sub_3_4.html) 제7조8항과 [콘텐츠 구매의 저작권 안내](https://info.etnews.com/sub_2_2.html) 1~3항은 복사·정보서비스·배포 및 기관 인트라넷용 DB를 다룬다. 비영리 인용·법상 예외의 출처 표기 조건도 존재한다. 외부 정보서비스와 이번 소표본 내부연구를 같다고 단정하지 않았다.
- [지디넷코리아 회원 약관](https://zdnet.co.kr/member/teamservice.php) 제6조8항·제9조는 제3자 이용, 배포, 발췌·인용 조건을 규정한다. 이 조항만으로 비상업 내부저장 전부가 금지되었다고 판정하지 않았다.
- [뉴스핌 저작권규약](https://mem.newspim.com/customer/copyright)은 수집·DB/데이터셋·AI학습 등을 직접 열거한다. [서비스약관](https://mem.newspim.com/customer/terms)의 상업적 사용 제한보다 구체적이다. 비영리 인용의 출처 요구는 자동수집 허락으로 바꾸지 않았다.
- [이데일리 약관](https://www.edaily.co.kr/info/E04_01.html) 제18조1항5호의 서비스 이용 외 목적 복제와 제3자 제공을 분리했다. 회원 게시물에 관한 회사의 사용권을 이용자에게 주어진 기사 사용권으로 읽지 않았다.

## robots와 확인 수준

5개 exact host의 /robots.txt는 P01ResearchCrawler/0.2로 직접 요청하여 **5/5 HTTP 200**을 확인했다. 일반 기사 경로인 한국경제 /article/, 전자신문 /숫자기사ID, 지디넷 /view/, 뉴스핌 /news/view/, 이데일리 /News/Read에 적용되는 금지는 발견하지 못했다. 최종 URL별 검사는 수집기가 다시 수행해야 한다. robots 허용은 저장·AI 이용허락이 아니다.

한국경제는 /article/download/·/api/ 등, 지디넷은 /Include2/user/·/Contents/, 뉴스핌은 /search·/news/preview/print 등, 이데일리는 지정 popup 경로를 제한한다. 전자신문의 GPTBot 제한 예시는 주석으로 비활성 상태였다. 봇 이름을 바꾸거나 차단된 대체 호스트를 탐색하지 않았다.

source_trials에는 **고유 요청 URL 16개에 대한 17개 자원 확인 기록**을 남겼다(정책/링크발견 11 + robots 6). 이데일리 robots의 첫 응답은 로컬 출력 인코딩 오류로 결과가 소실되어 HTTP 상태를 not_observed로 기록하고, 같은 UA/URL에서 출력 인코딩을 수정한 확인은 200으로 별도 기록했다. web 도구의 정책 페이지 읽기 성공은 원서버 HTTP 200으로 추정하지 않았다.

기사 상세 URL을 열거나 원문을 수집·저장하지 않았다. 웹검색에서 불필요하게 노출된 기사 결과는 정책근거로 쓰지 않았다. 회원가입·로그인·외부연락·API 인증·계약확인은 수행하지 않았다. registry의 authentication=none은 정책/홈/robots의 무인증 접근 관찰을 뜻하며, 개별 기사 유료벽·로그인은 런타임 별도 검사 대상이다.

권한 11개 열에서 확인되지 않은 것은 unresolved, 명시 제한만 denied로 기록했다. 전 행의 rights_status와 authorization은 unresolved다. body_xpath는 지정하지 않았다. 공유금지와 내부보관 미확인은 구별되며 어제 기록은 보존했다.
