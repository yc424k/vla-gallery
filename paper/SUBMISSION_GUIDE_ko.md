# Applied Sciences 투고 안내

## 1. 투고처

| 항목 | 내용 |
|---|---|
| 저널 | **Applied Sciences** (MDPI), ISSN 2076-3417 |
| 섹션 / 유형 | Robotics and Automation / **Review** |
| 등재 | SCIE (Web of Science), Scopus, Ei Compendex |
| 영향력 지수 | 2025 IF 2.9 (JCR 2026 발표) |
| 심사 속도 | 첫 결정까지 약 15일, 수락 후 게재까지 2.9일 (2026년 상반기 중앙값) |
| 게재료 | CHF 2,400 (수락 후 청구, 소속 기관 할인 여부 확인) |

- 근거: MDPI 공식 저널 안내 자료(2026년판)와 Applied Sciences APC 페이지.
- Sensors(IF 4.0)도 후보였지만, 센서 중심 저널이라 '모델 서베이'는 주제 부적합으로 바로 반려될 위험이 있습니다. 범위가 넓은 Applied Sciences가 연내 통과 가능성이 더 높습니다.
- 같은 MDPI의 Drones에 VLA 리뷰(Sa et al., 2026)가 실린 전례가 있어 주제 자체는 MDPI에서 받아들여집니다.
- 투고 직전에 Web of Science Master Journal List(mjl.clarivate.com)에서 SCIE 등재를 한 번 더 확인하세요.

## 2. 만든 파일 (`paper/`)

| 파일 | 내용 |
|---|---|
| `manuscript.pdf` | 완성 원고(34쪽, MDPI 양식) |
| `manuscript.tex`, `stats.tex`, `references.bib`, `Definitions/`, `figures/`, `tables/` | LaTeX 원본. MDPI는 LaTeX 투고를 받습니다 |
| `submission/manuscript.docx` | 같은 내용의 Word 판(읽기·수정용) |
| `submission/cover_letter.md`, `.docx` | 편집장에게 보내는 투고 편지 |
| `scripts/` | 모든 수치·그림·표·참고문헌을 데이터에서 다시 만드는 스크립트 |
| `data/` | 계산 결과(stats.json, calibration.json 등)와 arXiv 서지 정보 캐시 |
| `build_paper.sh` | 전체 재생성: `./paper/build_paper.sh` |

- 본문의 수치는 `gallery/data.json`에서 자동으로 계산해 `stats.tex`와 `tables/`로 들어갑니다. 데이터를 고친 뒤 `build_paper.sh`를 돌리면 원고 수치가 함께 바뀝니다.
- 다만 본문에 직접 적은 일부 수치(예: 연도별 비율)는 다시 확인해야 합니다.

## 3. 투고 전에 꼭 채울 것 (원고에 `TODO(author)`로 표시)

1. **저자 정보**: 이름, 소속, ORCID, 교신 이메일 (`manuscript.tex` 상단). 공저자가 있으면 `oneauthor`를 `moreauthors`로 바꿉니다.
2. **모델 수집 방법 (3.2절)**: 후보 모델을 실제로 어떻게 찾았는지 적습니다. 예: 기존 서베이 참고문헌, arXiv cs.RO, 기업 발표, awesome 목록. 심사위원이 가장 먼저 볼 부분입니다.
3. **생성형 AI 사용 고지 (3.7절과 Acknowledgments)**: MDPI 필수 항목입니다.
   - 데이터 수집·검증에 AI를 썼다면 그대로 적어야 합니다.
   - 사용한 Claude 버전도 적습니다.
   - 사실과 다르게 적으면 게재 후 철회 사유가 됩니다.
4. **연구비 (Funding)와 게재료 부담 주체**.
5. **저자 기여 (Author Contributions, CRediT 형식)**.
6. **데이터 공개**: GitHub 저장소가 공개 상태인지 확인하고, Zenodo에 릴리스를 올려 DOI를 받아 Data Availability에 넣습니다. MDPI가 강하게 권장합니다.
7. **투고 편지**의 [ ] 부분 (날짜, 이름, 소속, 프리프린트 여부).

## 4. 투고 절차 (MDPI SuSy)

1. https://susy.mdpi.com 로그인 → *Submit Manuscript*.
2. Journal: **Applied Sciences**, Section: **Robotics and Automation**, Article type: **Review**.
3. 업로드할 파일:
   - 원고 PDF
   - LaTeX 원본 zip (`manuscript.tex`, `stats.tex`, `references.bib`, `manuscript.bbl`, `Definitions/`, `figures/`, `tables/`)
   - 투고 편지
4. 추천 심사위원(선택, 보통 3~5명): 관련 서베이 저자 중 이해관계가 없는 사람을 고릅니다. 예: Kawaharazuka et al. 2025, Guan et al. 2025, Grover et al. 2026, Sa et al. 2026의 교신저자. 이메일은 논문에서 직접 확인하세요.
5. 제출 후 보통 며칠 안에 편집부의 사전 검토(유사도·형식)를 거쳐 심사로 넘어갑니다.

## 5. 연내 승인 일정 예시

| 날짜 | 할 일 |
|---|---|
| ~11월 5일 | 3장의 TODO 채우기, Zenodo DOI 받기, 투고 |
| ~11월 20일 | 첫 심사 결과 (Minor·Major revision 예상) |
| 결과 후 7일 이내 | 수정본과 답변서 제출 (이게 가장 중요) |
| 12월 중순 | 게재 승인 목표 |

## 6. 심사에서 나올 만한 지적과 대비

- **후보 수집이 체계적인가**: 3.2절을 구체적으로 씁니다. 요구가 있으면 PRISMA 흐름도를 추가합니다.
- **데이터 정확성**: 2차 검증(145건 확인, 58건 수정)과 근거 링크 공개를 강조합니다. AI 보조 추출을 했다면 사람의 확인 절차를 설명합니다.
- **추정식 과적합**: leave-one-out 결과(1.49배)와 장치 간 환산(1.09배)이 이미 들어 있습니다. 임베디드 장치 실측이 6건뿐이라는 한계도 이미 적었습니다.
- **2026년 최신성**: 기준일(10월 6·14·19일)을 명시했습니다. 갤러리가 계속 갱신된다는 점을 답변에 활용합니다.

## 7. 다시 만들기

```bash
pip install matplotlib numpy scipy
sudo apt-get install texlive-latex-extra texlive-science texlive-plain-generic latexmk pandoc   # Ubuntu 기준
./paper/build_paper.sh
```
