# Arknights Story Index

명일방주 캐릭터의 대사와 호칭 용례를 찾아 앞뒤 문맥으로 판단하는 비공식 검색 도구입니다.

## 검색

- A만 선택하면 해당 인물의 대사를 검색합니다.
- B도 선택하면 B의 이름·등록 별칭이 포함된 A의 대사를 찾습니다.
- 앞뒤 대사 3개, 분기 표기, 같은 줄 위치의 다른 언어 대조 후보, 출처 복사를 제공합니다.
- 상대방·직접 호칭·제삼자 지칭은 사용자가 문맥으로 판단합니다. 인물의 동시 등장만으로 대화 상대를 확정하지 않습니다.
- 관리자 검토, 인증, 기록 저장 기능은 사용하지 않습니다. 별도 PostgreSQL이나 토큰 설정이 필요하지 않습니다.

`characters.json`에 언어별 이름·검색용 별칭을 등록합니다. 현재 M3→Mon3tr, 켈시↔凯尔希를 지원합니다. 화자는 정확한 표기로 검색하며 물음표 화자·합동 화자는 자동 병합하지 않습니다. 등록되지 않은 별칭·대명사나 이름이 생략된 대사는 두 인물 검색에서 누락될 수 있으므로 A만 선택한 전체 대사 검색도 함께 활용하세요.

## 로컬 실행

Python 3.12+, Git이 필요합니다.

```sh
python -m pip install -r requirements.txt
python sync.py
python app.py
```

http://127.0.0.1:8000 에서 검색합니다. 이미 확보한 원본을 가져올 수도 있습니다.

```sh
python app.py --import-root /path/to/ArknightsGamedata --revision <commit-sha>
```

원본 제공처는 ArknightsAssets/ArknightsGamedata입니다. 원본 TXT를 자체 파서로 변환하고 SHA와 원문 스냅샷을 보관합니다. 원본·DB는 git에 넣지 않으며 `data/`를 영구 디스크에 두고 백업하세요. 파싱 후 트랜잭션으로 반영하고, 기존 대사가 100개 이상일 때 20% 이상 감소하면 갱신을 차단합니다.

## Vercel 배포

저장소 루트를 Root Directory로 사용하고 Output Directory 수동 지정은 비워두세요. `vercel.json`이 Flask 진입점 및 `python build.py`를 지정합니다. 빌드에서 원본을 가져와 읽기 전용 `generated/search.sqlite`를 생성합니다. 다운로드나 변환 실패 시 빌드를 실패시켜 빈 데이터를 배포하지 않습니다. 데이터 갱신은 재배포 시 반영됩니다. `ASI_SOURCE_REF`로 원본 commit SHA를 고정할 수 있습니다.

원본·스냅샷은 Function 번들에서 제외합니다. Vercel 빌드 디렉터리는 영구 아카이브가 아니므로 별도 원본 백업이 필요합니다. 2026-10-22 기준 검색 DB는 약 208MiB이며, 400MiB를 넘으면 빌드를 차단합니다. 의존성을 포함한 최종 크기는 Vercel에서 확인하세요.

```sh
python build.py --source-db data/index.sqlite
VERCEL=1 python app.py
```

`/api/status`에 성공한 수집의 출처·SHA·파일 수·추출 대사 수·미처리 일반 텍스트 수를 표시합니다. 기존 로컬 DB에 남은 검토 테이블은 읽거나 갱신하지 않으며 새 검색 DB에도 포함하지 않습니다. 예전 관리자 환경 변수는 사용하지 않습니다.

## 한계와 검증

한국 서버 공개분 기본 필터는 같은 경로의 한국어 파일 존재 여부를 사용한 근사치입니다. 언어 대조도 같은 줄 위치의 후보이므로 문맥으로 대응을 확인하세요. name/multiline 이외 자막·선택지·다중행 병합, 분기 그래프, 삭제 스토리 처리가 남아 있습니다. 미처리 일반 텍스트에는 내레이션과 개발용 문서도 섞여 있어 이 수치를 대사 누락률로 해석하면 안 됩니다. 검색 결과가 없다고 공식 용례가 없다는 뜻은 아닙니다.

직접 게임 리소스 다운로드는 아직 구현하지 않았습니다. 코드와 게임 원문의 권리는 구분하며 제삼자 코드·자료 사용 조건을 확인해야 합니다.

```sh
python -m unittest discover -s tests -v
node --check web/app.js
```


## 공통 UI와 안내 페이지

L10ndiff의 민트·틸 팔레트와 달/해 테마 버튼(SVG·전환 모션)을 동일 운영자의 요청으로 재사용했습니다. 둥근 검색 카드, 이름 자동완성(대사 수·등록 약칭 안내), 예시 검색을 제공합니다. /help, /privacy, /terms, /license, /changelog는 동일한 헤더·푸터·테마 전환을 공유합니다.

테마는 localStorage의 asi-theme-v1에만 저장하며 검색어를 브라우저 저장소에 저장하지 않습니다. 이 서비스의 검색어는 서버로 전송되고 요청 URL에 포함될 수 있습니다. L10ndiff의 브라우저 전용 처리 안내·Analytics·광고·Tally 폼은 가져오지 않았습니다. 피드백은 이 프로젝트 GitHub Issues 링크를 사용합니다. 자체 코드 라이선스와 출처는 LICENSE 및 NOTICE를 확인하세요.
