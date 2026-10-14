#!/usr/bin/env bash
# 전체 다시 만들기: 데이터 병합 → 갤러리 페이지 → 배포용 docs/(영어 맨 위 + ko·ja·zh) → 엑셀 비교표
set -euo pipefail
cd "$(dirname "$0")"
python3 build/build_data.py parts gallery gallery/data.json
python3 build/inject.py gallery/template.html gallery/data.json gallery/vla-gallery.html
# 배포 페이지: 영어가 사이트 맨 위(docs/index.html), 한국어·일본어·중국어는 docs/<lang>/
# 한국어 본문은 gallery/vla-gallery.html(위에서 만든 것)을 쓰고, 나머지는 i18n/<lang>.json으로 번역해 만든다
python3 build/i18n_extract.py gallery/template.html gallery/data.json gallery/devices.json i18n/source.json
mkdir -p docs/ko
python3 build/make_site.py gallery/vla-gallery.html docs/ko/index.html ko
for L in en ja zh; do
  python3 build/i18n_check.py i18n/source.json "i18n/$L.json" | tail -1 | sed "s/^/[$L 번역] /"
  out="docs/$L/index.html"; [ "$L" = en ] && out="docs/index.html"
  mkdir -p "$(dirname "$out")"; tmp=$(mktemp)
  python3 build/inject.py gallery/template.html gallery/data.json "$tmp" "$L"
  python3 build/make_site.py "$tmp" "$out" "$L"
  rm -f "$tmp"
done
# 예전 주소 /en/은 맨 위로 넘긴다(보던 페이지 해시 유지)
mkdir -p docs/en
cat > docs/en/index.html <<'HTML'
<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Robot VLA Gallery</title>
<link rel="canonical" href="https://vla-gallery.is-a.dev/"><meta name="robots" content="noindex">
<meta http-equiv="refresh" content="0; url=../">
<script>location.replace("../" + location.hash);</script></head>
<body><a href="../">Robot VLA Gallery</a></body></html>
HTML
touch docs/.nojekyll
# 모델별 정적 페이지(검색 노출용)와 sitemap.xml
python3 build/make_pages.py gallery/data.json i18n docs
# 링크 미리보기 이미지(언어별 홈 첫 화면). Playwright가 없으면 건너뛴다
python3 build/make_og.py docs
# 엑셀용 신규 모델 행은 gallery/new_models.json에서 다시 뽑는다
python3 -c "import json;R=json.load(open('gallery/new_models.json',encoding='utf-8'));open('parts/rows_w8.jsonl','w',encoding='utf-8').write(''.join(json.dumps(r['row'],ensure_ascii=False)+'\n' for r in R))"
python3 build/make_xlsx2.py parts "reports/로봇 VA VLA 모델 비교표.xlsx" gallery/data.json
