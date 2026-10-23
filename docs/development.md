# 개발과 배포

프로젝트 소개와 기본 실행은 [README](../README.md), 검색 해석과 후속 과제는 [architecture.md](architecture.md)를 참고하세요.

## 환경과 검증

앱에는 Python 3.12 이상과 Git이 필요합니다. UI 테스트에는 Node.js 22.22.2 이상(22 계열) 또는 지원되는 최신 Node.js가 필요합니다. 의존성 설치는 잠금 파일을 사용합니다.

```sh
python -m pip install -r requirements-dev.txt
npm ci --ignore-scripts
python -m unittest discover -s tests -v
npm test
node --check web/app.js
node --check web/theme.js
node --check web/chrome.js
node --check web/update-banner.mjs
node --check web/update-monitor.mjs
npm run format:check
python -m black --check app.py core.py catalog.py search_queries.py search_service.py build.py runtime_snapshot.py scripts/benchmark.py
git diff --check
```

테스트의 대사는 합성 fixture이며 공식 용례로 인용하지 않습니다. 원본 게임 덤프, DB, 환경 변수와 자격 증명은 커밋하지 않습니다.

## 원본 수집과 이름 사전

```sh
python sync.py
python sync.py --ref <source-commit-sha>
python app.py --import-root /path/to/ArknightsGamedata --revision <source-commit-sha>
```

`sync.py`는 네 언어의 원본을 가져오고 SHA를 고정한 뒤 `data/index.sqlite`에 반영합니다. 원문 스냅샷과 출처를 보관하며, 파싱 결과를 트랜잭션으로 적용합니다. 기존 대사가 100개 이상일 때 전체 대사가 20% 이상 감소하면 갱신을 차단합니다.

`character_catalog.py`는 원본 `character_table.json`의 공식 ID로 이름을 연결하고 `characters.json`과 `characters.source.json`을 생성합니다. 이름의 유사성으로 다른 인물을 합치거나 임의 별명을 자동 생성하지 않습니다. `M3`와 같은 검색 약칭은 명시적으로 관리합니다.

`data/`를 영구 디스크에 두고 별도로 백업하세요. 빌드 환경의 원본 체크아웃은 영구 백업이 아닙니다. 직접 게임 리소스 다운로드 어댑터는 미구현 상태입니다.

## Vercel 배포

저장소 루트를 Root Directory로 사용하고 Output Directory 수동 지정은 비워둡니다. `vercel.json`이 Flask 진입점과 `python build.py`를 지정합니다. `ASI_SOURCE_REF`로 원본 SHA를 고정할 수 있으며, 기본 원본 SHA는 `dataset-source.json`으로 고정합니다. UI 배포만으로 원본 버전은 바뀌지 않습니다.

```sh
python build.py --source-db data/index.sqlite
VERCEL=1 python app.py
```

빌드에서는 재생성 가능한 중간 DB에만 `--ephemeral` 및 메모리 저널을 사용합니다. 영구 아카이브 갱신에는 사용하지 않습니다. 최종 DB는 `quick_check`와 용량 검사 후 교체하며 수집·변환 실패 시 빌드를 실패시킵니다.

배포 번들에는 `generated/search.sqlite.gz`와 `generated/portraits/`를 포함하고 원본 SQLite·아카이브는 제외합니다. 런타임은 파일 잠금으로 중복 압축 해제를 막고 `/tmp`에 한 번 풀어 immutable 읽기 전용으로 엽니다. 이 파일은 재생성 가능한 임시 캐시입니다.

2026-10-22 검증본은 1,433,397개 대사, SQLite 약 419MiB, gzip 약 141MiB입니다. 압축 전 DB가 450MiB를 넘으면 빌드를 중단합니다. 최종 Function 번들 크기는 의존성을 포함해 배포에서 확인합니다.

## 주요 API

| 경로 | 기능 |
| --- | --- |
| `/api/search` | 인물·표현 중 하나 이상으로 검색, 대상·표현·언어·공개 범위·페이지 지정 |
| `/api/suggestions` | 선택한 언어·공개 범위의 화자와 등록 별칭 |
| `/api/context` | 원본 story·ordinal 기준 앞뒤 최대 100개 대사 |
| `/api/status` | 수집 출처·SHA·파일 수·대사 수·미처리 텍스트 수 |
| `/version.json` | 새 배포 감지용 버전 |

화면 언어 `ui=ko/zh/ja/en`와 대사 언어 `lang=ko_KR/zh_CN/ja_JP/en_US`를 별도로 지정할 수 있습니다. 상단 언어 선택은 두 값을 함께 바꾸며 검색창의 대사 언어는 별도로 선택합니다. 검색 조건은 공유 URL에 기록됩니다. 관리자 검토·로그인·외부 검토 DB는 사용하지 않습니다. 예전 로컬 DB에 남은 검토 테이블도 검색하거나 배포하지 않습니다.

## 공통 화면

`web/base.html`이 헤더·푸터를 공유하며 `pages.py`와 `localized_pages.py`가 안내 문서를 제공합니다. `translations.py`는 네 언어의 UI 문구를 관리합니다.

테마는 `asi-theme-v1` localStorage 키에 저장합니다. 업데이트 알림은 60초마다 확인하고 숨겨진 탭·오프라인에서는 쉬며, 30분 재알림은 sessionStorage에 보관합니다. 업데이트 전에 입력 중인 검색 조건을 URL에 보존합니다. 피드백은 외부 Tally 링크이며 분석·광고 스크립트는 포함하지 않습니다.


## 역할별 코드 위치

- `app.py`: HTTP 입력 검증, HTML·API·버전별 정적 파일 응답.
- `core.py`: 파싱·아카이브 적재. 기존 import 호환을 위해 검색 함수도 재수출합니다.
- `catalog.py`: 프로세스당 한 번 읽는 이름·별칭 인덱스.
- `search_queries.py`: 검색 조건·파일 집계·문맥 조회.
- `search_service.py`: 읽기 전용 DB 연결과 공개 자동완성 캐시.
- `web/app.js`: 검색 요청·결과 상태·브라우저 기록을 연결하는 컨트롤러.
- `web/ui/`: API, 자동완성, 결과 렌더링, 화면 전환, 폼 상태, 필터, 모달, 공통 DOM 모듈.
- `web/chrome.js`: 헤더·테마·푸터 초기화. 업데이트 알림도 같은 폼 상태 모듈을 씁니다.

브라우저 표준 ES 모듈을 사용하며 번들러나 새 런타임 프레임워크가 필요하지 않습니다. UI 테스트는 각 jsdom의 격리된 VM에서 실제 모듈 그래프를 실행합니다. Node의 `--experimental-vm-modules` 옵션은 테스트에만 사용합니다. `npm run format:ui`로 UI 모듈을 정리하고 `npm run format:check`로 검사합니다.

정적 파일은 `/assets/<deployment-version>/...` 주소와 immutable 캐시를 사용합니다. 모듈 상대 경로도 같은 버전 아래에서 로드합니다. HTML·API·버전 응답은 no-store입니다. 로컬 버전 해시는 하위 UI 모듈까지 포함합니다. 사용자가 이전 배포 화면을 열어둔 동안의 데이터 변경은 업데이트 알림·새로고침으로 반영합니다.

## 성능 확인

```sh
python scripts/benchmark.py generated/search.sqlite.gz
```

실제 DB가 있는 로컬 환경에서 대사 원문을 출력하지 않고 조회 수·응답 크기·반복 중앙값을 측정합니다. UI는 `details=0`으로 보이는 결과만 받고, 문맥은 `/api/context`를 펼칠 때만 가져옵니다. UI에서는 다른 언어 후보를 조회하지 않습니다. 기본 API의 상세 응답은 이전과 호환됩니다. 스토리 집계에서 전체 개수를 구해 별도 count 스캔을 없앴습니다.

자동완성 집계는 스냅샷 빌드에서 `suggestion_counts`로 생성하고, 서버에서는 공개 목록만 최대 8개 언어·범위 조합으로 캐시합니다. 구버전 DB와 변경 가능한 로컬 아카이브는 기존 집계로 동작합니다. 브라우저 API 캐시는 현재 탭 메모리에서 최대 16개·60초이며 실패·취소 응답을 보관하지 않습니다. 검색어는 디스크 저장소에 캐시하지 않습니다.


2026-10-22 로컬 스냅샷 1,433,397개 대사에서 변경 전후 각 15회 측정했습니다. 네트워크·Vercel 기동·최초 gzip 해제 시간은 포함하지 않습니다. 자동완성은 7,453개 항목이며 새 집계 스냅샷은 약 420.5MiB로 450MiB 제한 안에 있습니다.

| 항목 | 변경 전 | 변경 후 |
| --- | ---: | ---: |
| 한국어 자동완성 API 반복 중앙값 | 958ms | 5.8ms |
| M3→켈시 검색 중앙값 | 9.7ms | 3.8ms |
| 아미야 전체 검색 중앙값 | 20.5ms | 14.9ms |
| 첫 결과 SQL 수 | 103 | 2 |
| M3→켈시 첫 결과 JSON | 약 112KB | 약 28KB |

다른 환경의 절대 속도를 보장하는 수치는 아닙니다. 문맥을 펼치면 해당 요청 비용이 추가됩니다. 기능 추가 시 같은 스냅샷·검색 조건으로 다시 측정하고 결과 개수·출처·분기·공개 범위가 같음을 함께 확인하세요.

## 초상화와 글꼴

`python build_portraits.py`는 portraits.source.json에 고정된 원본 SHA를 검증하고 기본 아바타를 96px WebP로 생성합니다. 이미지와 인덱스는 generated/에만 두고 커밋하지 않습니다. 빌드에 실패하면 배포를 중단합니다. 요청 중 외부 다운로드는 없습니다. 공식 ID로만 연결하고, 중복 이름·누락 이미지는 기본 아이콘을 사용합니다.

L10ndiff의 NEXON Lv2 Gothic Regular/Bold 원본은 web/fonts/에 변경 없이 보관합니다. fonts.source.json에 Git blob SHA와 출처를 기록하며 일본어·중국어는 기기 글꼴로 이어집니다. 글꼴은 버전별 정적 경로로 캐시합니다. 푸터 링크는 화면 언어를 따르고 문서 본문은 한국어·영어 병기입니다.

## 검색 데이터와 UI 배포 분리

`Publish search dataset` 워크플로는 원본 SHA·파서·빌드 입력이 변경될 때만 실행합니다. 수동 실행도 가능합니다. 검증된 검색 스냅샷 gzip, 공식 ID 이름 사전, 초상화를 `dataset-<입력 해시>` GitHub Release의 `dataset.zip`에 보관합니다. 원문 아카이브는 포함하지 않습니다. 데이터 갱신은 dataset-source.json의 SHA를 갱신하는 PR로 진행합니다.

기본 `python build.py`는 정확히 같은 입력 해시의 묶음을 다운로드해 파일 목록·용량·SHA-256을 검증합니다. UI만 바꾸면 원본 수집·파싱·이미지 변환을 생략합니다. 해당 Release가 아직 없는 첫 배포는 고정 원본에서 직접 빌드합니다. 404 이외의 다운로드 실패나 검증 오류는 배포를 중단합니다. `--fresh-data` 또는 `ASI_SOURCE_REF`는 재사용을 우회합니다. Release 생성과 첫 Vercel 배포가 동시에 실행될 수 있으므로 첫 배포까지 빨라지는 것은 아닙니다.

두 인물 검색은 전체 일치 결과를 가까운 상대 발화 수(앞·뒤 각각 최대 1)로 먼저 정렬하고, 파일·행으로 동률을 정렬한 뒤 50개씩 반환합니다. 각 방향 최대 6개 텍스트 행·물리 60행만 조사하며 다른 분기나 다른 화자를 만나면 탐색을 멈춥니다. 직접 대화·제삼자 언급을 확정하지 않고 검색 순위에만 이용합니다. 단어 단독 검색 순서는 유지합니다.

2026-10-22 추가 파서 검증: 같은 원본 SHA에서 한국어·일본어·영어 각 368,102개, 중국어 385,920개, 총 1,490,226개 텍스트를 확인했습니다. 검색 DB 438.0MiB, gzip 147.1MiB입니다. 로컬 M3→켈시 5회 반복 중앙값은 언어별 3.2–3.7ms이며 서버·네트워크 지연은 포함하지 않습니다. 미지원 텍스트 명령은 import_status의 unsupported_text_tags에 집계합니다. 튜토리얼·UI 명령 등은 아직 검색하지 않습니다. 물리적으로 분리된 다중행은 원본 행별로 유지합니다.

## 브랜드와 공개 변경 기록

brand/masters의 투명 PNG 원본과 web/brand의 크기별 내보내기를 보관합니다. `python scripts/export_brand.py`로 내보내기를 재생성합니다. 1번 기록실 로고는 파비콘, 2번 후드 로고는 헤더와 홈 검색창 위에 사용합니다.

공개 패치노트의 기준은 2026-10-22의 1.0.0입니다. 이후에는 검색 기능의 실질적 변화, 호환성 변경, 중요한 오류 수정만 기록하고 일상적인 스타일 조정·리팩터링·개발 과정은 Git 이력에 남깁니다.

## 언어 전환 스플래시와 입력 초기화

L10ndiff의 sessionStorage 마커, 380ms 이탈 → 페이지 이동 → 300ms 진입 구조를 ui/language-transition.mjs와 ui/language-splash.mjs로 옮겼습니다. language-splash-boot.js는 외부 클래식 스크립트로 첫 화면 전 상태를 복원합니다. CSP 완화·인라인 스크립트는 추가하지 않습니다. 마커는 목적 화면 언어와 유효 시간을 검증하고 저장소 접근 실패·모션 줄이기·BFCache 복귀·이동 실패를 처리합니다.

토끼는 기존 투명 PNG를 CSS clip-path로 몸·양쪽 귀에 나눠 서로 다른 지연과 회전·스쿼시를 적용합니다. GIF나 애니메이션 라이브러리를 추가하지 않습니다. 기본 홈에는 중앙 로고를 표시하지 않습니다. 입력 지우기는 검색 버튼 옆에 있고 언어·선행 스토리 설정을 보존한 빈 홈으로 복귀합니다.

원문 대응 1차 구조 조사 결과는 alignment-feasibility.md를 참고하세요. 원문·번역 대조는 검증된 파일 범위에서 선택적으로 제공합니다. 전체 빌드 결과와 한계는 alignment-feasibility.md를 참고하세요.

대응 인덱스가 추가되어 dataset.py의 입력 해시에 translation_alignment.py를 포함합니다. 구버전 스냅샷에서 대조를 요청하면 대응 미확인 상태로 반환하고 기존 단일 언어 검색은 유지합니다. 빌드에서 raw 스크립트는 최종 스냅샷에 복사하지 않습니다. 새 인덱스도 450MiB 예산 및 quick_check를 통과해야 배포합니다.


통합 다국어 검색은 `/api/search?all_languages=1&lang=ko_KR&q=你好&details=0`으로 확인합니다. `lang`은 대표 표시 언어이며 네 언어에서 literal 일치를 찾습니다. `variants`는 검증된 대응만 포함합니다. 문맥에도 `all_languages=1`을 지정할 수 있습니다. 검색어를 보관하지 않는 요청별 임시 테이블을 사용하며 읽기 전용 스냅샷에서도 SQLite TEMP는 동작합니다. UI의 추가 표시 언어는 `show=zh_CN,ja_JP`로 복원하며 검색을 재실행하지 않습니다.


검색 폼의 조건은 세 칸 중 하나 이상입니다. HTML의 자동 제출 검증은 novalidate로 끄고 submit에서 그룹 조건을 검사한 뒤 명시적으로 reportValidity를 호출합니다. 대사 칸에 남은 과거 customValidity가 submit 이벤트를 막지 않게 합니다. 자동완성의 마우스·키보드 선택은 모두 input 이벤트를 보내며, 기록 복원 시 이전 오류를 해제합니다. UI 회귀 검증에는 실제 requestSubmit 경로를 사용합니다.
