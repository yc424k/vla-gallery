#!/usr/bin/env bash
# Rebuild every number, figure, table, the PDF and the Word copy of the manuscript from ../gallery/*.json.
# Needs: python3 with matplotlib, numpy, scipy; TeX Live (latexmk, pdflatex, bibtex); pandoc (Word copy only).
set -euo pipefail
cd "$(dirname "$0")/scripts"
python3 calib.py > /dev/null      # estimator calibration, leave-one-out, ablations -> data/calibration.json
python3 analysis.py > /dev/null   # corpus statistics -> data/stats.json, stats.tex
python3 tests.py > /dev/null      # Fisher tests -> data/disclosure_tests.json
python3 figures.py > /dev/null    # figures/fig2-9 (fig1 is figures/src/fig1_anatomy.tex)
python3 tables.py > /dev/null     # tables/*.tex
python3 build_bib.py > /dev/null  # references.bib (uses cached arXiv metadata in data/arxiv_meta.json)
cd ..
latexmk -pdf -interaction=nonstopmode -quiet manuscript.tex
python3 scripts/make_docx.py
rm -f submission/latex_source.zip   # LaTeX source bundle for the MDPI submission system
zip -q -r submission/latex_source.zip manuscript.tex stats.tex references.bib manuscript.bbl Definitions figures/*.pdf figures/src/fig1_anatomy.tex tables/*.tex -x "Definitions/*.eps"
echo "done: manuscript.pdf, submission/manuscript.docx, submission/latex_source.zip"
