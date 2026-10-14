# 로봇 VA·VLA 모델 비교 갤러리 — 인수인계

## 한눈에
- 2022~2026년 로봇 VA·VLA 모델 211개를 비교하는 정적 웹 갤러리와 엑셀 비교표다. 범위는 매니퓰레이션, 휴머노이드 전신 제어, 모바일 매니퓰레이션, 내비게이션이다.
- 카드마다 구조도, 논문 링크, 백본 LLM, 액션 헤드, 학습 GPU·시간·데이터, 추론 장치·속도·메모리, 강화학습 사용처, 베이스 제어 방식이 있다.
- 현재 게시본: claude.ai 아티팩트 https://claude.ai/artifact/CdHZuSinnVa9n6rXrx5DMH (사용자만 볼 수 있는 비공개 상태). 다음 목표는 GitHub Pages 배포다.
- 기준일:
  - 기존 165개 모델 수치: 2026-10-06
  - 모바일 매니퓰레이션·내비게이션 46개, 베이스 제어 분류, '내 장치' 추정: 2026-10-14

## 작업 방식
- 사용자와는 한국어로 대화한다.
- 고친 뒤에는 `./build.sh`로 다시 만들고, 렌더 점검을 거친 다음 `docs/index.html`까지 함께 커밋한다.

## 폴더
| 경로 | 내용 |
|---|---|
| `gallery/template.html` | 페이지 원본(HTML·CSS·JS 한 파일). `__DATA__`, `__DEVICES__` 자리에 JSON이 들어간다 |
| `gallery/data.json` | 빌드 결과(모델 211개). 직접 고치지 말고 아래 원천 파일을 고친 뒤 빌드한다 |
| `parts/rows_w1~w6.jsonl` | 기존 165개 모델 행(한국어 키 28개) |
| `parts/rows_w7.jsonl` | 데이터셋 67개 |
| `parts/rows_w8.jsonl` | 모바일·내비 46개. `build.sh`가 `gallery/new_models.json`에서 다시 뽑는다 |
| `gallery/fields.py` | 기존 165개의 구조도·백본 LLM·헤드·추론 필드(`F`, 행 번호 1~165) |
| `gallery/rl.py` | 기존 165개의 강화학습 (상태, 분류, 사용 위치, 근거 URL) |
| `gallery/papers.py` | 논문 제목(`T`), 예외(`OWN`), 관련 논문(`REL`) |
| `gallery/new_models.json` | 신규 46개 레코드(row·fields·rl·paper·base·evidence, 독립 검증 반영본). 신규 모델의 원천 파일이다 |
| `gallery/base_existing.json` | 기존 165개의 베이스 제어(types·how·cat) |
| `gallery/devices.json` | '내 장치' 계산용 장치 24종 사양과 출처 |
| `parts/sources_w*.md` | 엑셀 '출처' 시트용 링크 |
| `build/` | `build_data.py`(병합), `inject.py`(페이지 생성), `make_site.py`(배포용 완전한 HTML), `make_xlsx2.py`(엑셀), `shot4.py`·`shot5.py`(Playwright 렌더 점검) |
| `docs/` | GitHub Pages에 올릴 파일(`index.html`, `robots.txt`, `sitemap.xml`, `.nojekyll`, `CNAME`). `build.sh`가 다시 만든다(`CNAME` 제외). 검색용 메타 태그·사이트 주소(`SITE`)는 `make_site.py`에 있다 |
| `reports/` | 로봇 VA VLA 모델 비교표.xlsx |
| `research/notes/` | 주제별 조사 노트. `verification_*.md`(검증 노트)가 다른 노트보다 우선한다 |
| `research/mobile/` | 모바일·내비 조사 명세(`SPEC.md`), 조사 원본(`new_models.json`), 검증 결과(`verify_v*.json`), 적용 스크립트(`apply.py`) |
| `research/devspec/calib.py` | '내 장치' 추정 상수 보정 스크립트 |
| `research/drafts/` | 초기 보고서 섹션 초안 |
| `.claude/settings.json` | 커밋·PR에 Claude 서명이 붙지 않게 하는 설정(아래 Git 규칙) |

- `research/`는 `.gitignore`에 들어 있어 저장소에 올리지 않는다(로컬 전용). 빌드에는 필요 없다.
- `research/mobile/apply.py`는 조사 원본에 검증 수정을 적용해 네 파일을 만든 기록이다. 만드는 파일은 `gallery/new_models.json`, `parts/rows_w8.jsonl`, `parts/sources_w8.md`, `gallery/base_existing.json`이다.
  - 지금 돌리면 현재 파일과 똑같이 재현된다.
  - 이 네 파일을 직접 고친 뒤에는 돌리지 않는다(덮어쓴다).

## 빌드
- 전체 빌드: `./build.sh`. python3와 openpyxl이 필요하다.
- 렌더 점검:
  1. `pip install playwright && playwright install chromium`
  2. 저장소 루트에서 `mkdir -p shots && python3 build/shot5.py "$PWD/shots"`
  3. 콘솔 오류가 없고, `scrollWidth`가 화면 폭(1280·400)과 같은지 확인한다.

## 페이지 구성 (template.html)
01 추론 자원 / 02 메모리 계산기 / 03 내 장치 / 04 백본 LLM / 05 강화학습 / 06 모바일 베이스 / 07 두 모델 비교 / 08 갤러리

- 페이지 나누기: 한 HTML 안에서 주소의 해시(`#infer`, `#gallery` 등)마다 섹션 하나만 보여 준다. 해시가 없으면 홈(첫 화면 + 페이지 목차)이다.
  - `<head>`의 스크립트가 첫 화면 전에 `html[data-page]`를 정하고, CSS가 그 값에 맞는 섹션만 보이게 한다. JS의 `PAGES`와 `route()`가 이후 이동을 맡는다.
  - `#m-<모델 id>`는 갤러리 페이지로 가서 그 카드로 스크롤한다. 뒤로 가기도 페이지 단위로 동작한다.
  - 섹션 사이를 오가는 버튼(비교 A·B, 메모리 계산, 갤러리에서 보기)은 `go("페이지")`로 이동한다.

- 03 내 장치: 장치·정밀도·기준 Hz를 고르면 사용 가능한 모델을 보여 준다.
- 08 갤러리 필터: 분류, 유형, 연도, 크기, 백본, 헤드, 공개, 추론, 강화학습, 내 장치, 베이스, 논문, 정렬.
- 디자인 방향: 인쇄된 기술 사양서처럼 괘선과 무채색으로 정리한다. 그라데이션 글자, 빛 번짐 배경, 그림자, 떠오르는 hover, 알약 모양 칩, 히어로 순차 등장은 'AI가 만든 느낌'이 나서 뺐다. 다시 넣지 않는다.
- 모션: 짧은 스크롤 등장, 페이지 전환, 구조도 블록 순차 등장, 필터 전환(FLIP), 계산기 숫자 굴리기, 진행 막대, 맨 위로 버튼, 테마 전환(원형 View Transition)이 있다.
  - 테마를 바꾸는 순간에는 `html.theme-x`로 모든 transition을 끄고, 카드에는 `content-visibility:auto`를 걸어 화면 밖 카드를 그리지 않는다. 둘 중 하나라도 빼면 갤러리에서 테마 전환이 수백 ms씩 멈춘다.
  - `<head>`의 작은 스크립트가 `html.motion` 클래스와 저장된 테마(`vla-theme`)를 첫 화면 전에 정한다. `prefers-reduced-motion: reduce`이면 `motion`이 붙지 않아 모든 애니메이션이 꺼진다.
  - 렌더 점검 스크립트(`shot4.py`·`shot5.py`)는 `reduced_motion="reduce"`로 찍고, 요소를 찍기 전에 그 요소가 든 페이지로 해시를 옮긴다.

## '내 장치' 추정 방식
- **메모리:** P×바이트 + 1 GB + 0.3 GB×P(B). 장치 메모리의 90%까지 쓸 수 있다고 보고, Jetson은 75%로 본다.
- **지연:** 가중치 읽기 시간과 연산 시간 중 큰 쪽(roofline)으로 계산한다.
  - 토큰형: 백본 1회 + 토큰 수 × 디코딩
  - flow·diffusion: 백본 1회 + K × 헤드
  - 회귀: 1회
- **상수:** `EST = {em 0.6, ec 0.6, c0 4 ms, ct 4 ms, emb 1.5}`.
  - 실측(template.html의 `ANCHORS`) 38건 중 추정 공식이 적용되는 37건으로 보정했다. 중앙값 오차는 1.37배이고, 26건이 2배 이내다.
  - 다시 보정하려면 `python3 research/devspec/calib.py`를 실행한다. 출력 첫 줄이 현재 상수의 오차다.
- **실측 우선:** 같은 장치의 실측이 있으면 그 값을 쓴다. 다른 장치면 가장 가까운 장치의 실측을 비율로 환산한다.
- **모델별 파라미터:** `est`는 `build_data.py`의 `est_params()`가 만든다(행동당 토큰 수는 `TOKN`).

## 표기 규칙 (데이터를 고칠 때 지킬 것)
- **미공개 / 미확인:** 미공개는 1차 출처 어디에도 없다는 뜻이고, 미확인은 원문을 확인하지 못했다는 뜻이다. 추정하지 않는다. GPU-시간만 예외로, 장수와 시간이 둘 다 숫자일 때 곱해서 환산한다.
- **(2차) / † / A/B:** (2차)는 기사·타사 논문 등 2차 출처, †는 원문 대조를 못 한 값, A/B는 출처끼리 다른 값을 함께 적은 것이다.
- **서술:** 한국어 간결체로 쓰고, 모델·데이터셋·하드웨어 이름은 원문 그대로 둔다. '핵심 특징'은 '다.'로 끝나는 두 문장이다.
- **1차 출처:** 논문(arXiv), 공식 README, 모델 카드, 공식 블로그.
- **허용 값 목록:**
  - 구분(분류): `build_data.py`의 `ORDER`
  - 액션 헤드 종류: `HK`
  - LLM 계열: `FAM`
  - 베이스 종류: 고정 / 바퀴형 / 사족보행 / 휴머노이드 보행 / 비행 / 시뮬 전용
  - 베이스 제어 방식: template.html의 `BCATS`

## Git 규칙 (사용자 지정)
- 커밋 메시지는 add / update / fix / edit 중 하나로 시작한다. 예: `add: VLA 아키텍처 갤러리 페이지`
- 커밋과 푸시에 Claude를 기여자로 남기지 않는다.
  - Co-Authored-By 줄이나 'Generated with Claude Code' 문구를 넣지 않는다.
  - `.claude/settings.json`의 `attribution` 설정으로 자동 서명도 꺼 두었다.

## GitHub Pages 배포
1. GitHub에 저장소를 만든다. 무료 계정은 Public이어야 Pages를 켤 수 있다. 조사 노트를 공개하고 싶지 않으면 `research/`를 빼고 올린다.
2. 이 폴더를 커밋하고 푸시한다.
3. 저장소 Settings → Pages에서 Source를 'Deploy from a branch'로, Branch를 `main`, 폴더를 `/docs`로 고른다.
4. 주소는 `https://<계정>.github.io/<저장소>/`가 된다.

## 남은 일 / 아이디어
- GitHub Pages 배포(위 절차).
- (선택) 카드 등장과 필터 전환 애니메이션. 정적 호스팅이라 CSS·JS 애니메이션에는 제약이 없다.
- '판정 불가' 89개 모델의 파라미터 수 보강. 크기 공개 자료가 나오면 행의 파라미터·파라미터(B)를 채운다.
- claude.ai Docs의 초기 보고서에는 강화학습, 논문, 모바일 베이스, 내 장치 내용이 반영되지 않았다.
- 새 모델을 추가할 때:
  1. `research/mobile/SPEC.md` 형식의 레코드를 `gallery/new_models.json`에 덧붙인다. `build_data.py`가 166번 이후 행으로 붙인다.
  2. 근거 링크는 `parts/sources_w8.md`에 추가한다.
  3. `./build.sh`로 다시 만든다.
