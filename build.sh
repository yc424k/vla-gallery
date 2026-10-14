#!/usr/bin/env bash
# 전체 다시 만들기: 데이터 병합 → 갤러리 페이지 → 배포용 docs/index.html → 엑셀 비교표
set -euo pipefail
cd "$(dirname "$0")"
python3 build/build_data.py parts gallery gallery/data.json
python3 build/inject.py gallery/template.html gallery/data.json gallery/vla-gallery.html
python3 build/make_site.py gallery/vla-gallery.html docs/index.html
touch docs/.nojekyll
# 엑셀용 신규 모델 행은 gallery/new_models.json에서 다시 뽑는다
python3 -c "import json;R=json.load(open('gallery/new_models.json',encoding='utf-8'));open('parts/rows_w8.jsonl','w',encoding='utf-8').write(''.join(json.dumps(r['row'],ensure_ascii=False)+'\n' for r in R))"
python3 build/make_xlsx2.py parts "reports/로봇 VA VLA 모델 비교표.xlsx" gallery/data.json
