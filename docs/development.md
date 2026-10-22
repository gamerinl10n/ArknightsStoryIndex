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

저장소 루트를 Root Directory로 사용하고 Output Directory 수동 지정은 비워둡니다. `vercel.json`이 Flask 진입점과 `python build.py`를 지정합니다. `ASI_SOURCE_REF`로 원본 SHA를 고정할 수 있으며, 데이터는 재배포 시 갱신됩니다.

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

화면 언어 `ui=ko/zh/ja/en`와 대사 언어 `lang=ko_KR/zh_CN/ja_JP/en_US`는 독립적입니다. 검색 조건은 공유 URL에 기록됩니다. 관리자 검토·로그인·외부 검토 DB는 사용하지 않습니다. 예전 로컬 DB에 남은 검토 테이블도 검색하거나 배포하지 않습니다.

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

실제 DB가 있는 로컬 환경에서 대사 원문을 출력하지 않고 조회 수·응답 크기·반복 중앙값을 측정합니다. UI는 `details=0`으로 보이는 결과만 받고, 문맥·언어 후보는 `/api/context?parallel=1`을 열 때 가져옵니다. 기본 API의 상세 응답은 이전과 호환됩니다. 스토리 집계에서 전체 개수를 구해 별도 count 스캔을 없앴습니다.

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
