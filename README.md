# 로봇 VLA 아키텍처 갤러리 (Robot VLA Gallery)

**Robot Vision-Language-Action (VLA) model comparison** — 215 robot VLA/VA models (2022–2026) with architecture diagrams, backbone LLMs, action heads, training GPUs and inference memory: https://vla-gallery.is-a.dev/

2022~2026년 로봇 VA·VLA 모델 215개를 구조도 카드로 비교하는 정적 웹페이지와 엑셀 비교표입니다. 매니퓰레이션, 휴머노이드 전신 제어, 모바일 매니퓰레이션, 내비게이션 모델을 다룹니다.

- **페이지:** `docs/index.html` (GitHub Pages로 배포)
- **엑셀 비교표:** `reports/로봇 VA VLA 모델 비교표.xlsx`
- **다시 만들기:** `./build.sh` (python3, openpyxl)

## 페이지에서 볼 수 있는 것
- 모델별 구조도, 논문 링크, 백본 LLM, 액션 헤드, 학습 GPU·시간·데이터
- 추론 장치·속도·메모리, 추론 메모리 계산기
- 내 장치(GPU·Jetson)로 쓸 만한 속도가 나오는 모델 추정
- 강화학습 사용처와 모바일 베이스 제어 방식
- 두 모델 비교

## 수치와 출처
- 수치는 각 모델의 논문, 공식 README, 모델 카드, 공식 블로그에서 가져왔고, 출처 725건은 엑셀 '출처' 시트에 있습니다.
- 값이 없으면 '미공개'로 두고 추정하지 않았습니다. 2차 출처 값에는 '(2차)'를 붙였습니다.
- '내 장치' 속도는 실측이 아니라 계산값입니다. 실측 37건과 비교한 오차는 중앙값 약 1.4배입니다.
