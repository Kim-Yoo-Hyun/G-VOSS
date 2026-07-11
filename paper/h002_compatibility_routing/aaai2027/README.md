# H002 AAAI 2027 Source

Last updated: 2026-07-11 KST

Canonical anonymous AAAI manuscript source for H002.

## File Map

- `main.tex`: seven-page technical manuscript
- `h002.bib`: bibliography
- `supplement.tex`: supplementary tables and figures
- `reproducibility_checklist.tex`: AAAI checklist
- `figures/`: claim-safe generated PDF figures
- `tables/appendix_tables.tex`: generated appendix tables
- `official/`: local official template/checklist copies
- `aaai2027.sty`, `aaai2027.bst`: venue style files; do not edit
- `final_readiness.md`: external submission blockers

## Build

```bash
docker build -t h002-aaai2027-tex:latest \
  paper/h002_compatibility_routing/aaai2027

docker run --rm -u $(id -u):$(id -g) \
  -e HOME=/tmp -e TEXMFVAR=/tmp/texmf-var -e TEXMFCONFIG=/tmp/texmf-config \
  -v /home/yoohyun/research:/workspace \
  -w /workspace/paper/h002_compatibility_routing/aaai2027 \
  h002-aaai2027-tex:latest bash -lc \
  'pdflatex -interaction=nonstopmode -halt-on-error main.tex &&
   bibtex main &&
   pdflatex -interaction=nonstopmode -halt-on-error main.tex &&
   pdflatex -interaction=nonstopmode -halt-on-error main.tex'
```

Build `supplement.tex` and `reproducibility_checklist.tex` with PDFLaTeX when
those artifacts are needed.

Current verified outputs are 7-page `main.pdf`, 3-page `supplement.pdf`, and
2-page `reproducibility_checklist.pdf`, all US Letter with zero Type 3 fonts,
missing citations/references, LaTeX errors, and overfull boxes.

## Claim Boundary

- validated: relative vertical and relative size compatibility
- qualified: left/right
- diagnostic: proximity, front/behind, support/contact
- not claimed: hidden test, SOTA, all-family reliability, learned G_e,
  calibrated p_obs/p_rel

The current figures show the validated \(T_e,G_e\rightarrow C_e\) and
\(S_2=\operatorname{norm}(Z_e)C_e\) path. They intentionally exclude the
discarded broad PointNet/energy/selective-decision framework.
