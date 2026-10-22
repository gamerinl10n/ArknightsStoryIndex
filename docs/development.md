# 개발과 배포

프로젝트 소개와 기본 실행은 [README](../README.md), 검색 해석과 후속 과제는 [architecture.md](architecture.md)를 참고하세요.

## 환경과 검증

앱에는 Python 3.12 이상과 Git이 필요합니다. UI 테스트에는 Node.js 22.22.2 이상(22 계열) 또는 지원되는 최신 Node.js가 필요합니다. 의존성 설치는 잠금 파일을 사용합니다.

```sh
python -m pip install -r requirements.txt
npm ci --ignore-scripts
python -m unittest discover -s tests -v
npm test
node --check web/app.js
node --check web/theme.js
node --check web/chrome.js
node --check web/update-banner.mjs
node --check web/update-monitor.mjs
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

배포 번들에는 `generated/search.sqlite.gz`만 포함하고 원본 SQLite·아카이브는 제외합니다. 런타임은 파일 잠금으로 중복 압축 해제를 막고 `/tmp`에 한 번 풀어 immutable 읽기 전용으로 엽니다. 이 파일은 재생성 가능한 임시 캐시입니다.

2026-10-22 검증본은 1,433,397개 대사, SQLite 약 419MiB, gzip 약 141MiB입니다. 압축 전 DB가 450MiB를 넘으면 빌드를 중단합니다. 최종 Function 번들 크기는 의존성을 포함해 배포에서 확인합니다.

## 주요 API

| 경로 | 기능 |
| --- | --- |
| `/api/search` | 화자 필수 검색, 대상·표현·언어·공개 범위·페이지 지정 |
| `/api/suggestions` | 선택한 언어·공개 범위의 화자와 등록 별칭 |
| `/api/context` | 원본 story·ordinal 기준 앞뒤 최대 100개 대사 |
| `/api/status` | 수집 출처·SHA·파일 수·대사 수·미처리 텍스트 수 |
| `/version.json` | 새 배포 감지용 버전 |

화면 언어 `ui=ko/zh/ja/en`와 대사 언어 `lang=ko_KR/zh_CN/ja_JP/en_US`는 독립적입니다. 검색 조건은 공유 URL에 기록됩니다. 관리자 검토·로그인·외부 검토 DB는 사용하지 않습니다. 예전 로컬 DB에 남은 검토 테이블도 검색하거나 배포하지 않습니다.

## 공통 화면

`web/base.html`이 헤더·푸터를 공유하며 `pages.py`와 `localized_pages.py`가 안내 문서를 제공합니다. `translations.py`는 네 언어의 UI 문구를 관리합니다.

테마는 `asi-theme-v1` localStorage 키에 저장합니다. 업데이트 알림은 60초마다 확인하고 숨겨진 탭·오프라인에서는 쉬며, 30분 재알림은 sessionStorage에 보관합니다. 업데이트 전에 입력 중인 검색 조건을 URL에 보존합니다. 피드백은 외부 Tally 링크이며 분석·광고 스크립트는 포함하지 않습니다.
