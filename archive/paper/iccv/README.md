# ICCV-Style Manuscript Source

Last updated: 2026-05-26 KST

This directory is the first ICCV-style LaTeX source conversion of
`paper/draft.md`.

## Template Route

- Route chosen: official ICCV/CVF LaTeX author-kit structure.
- Template source checked: ICCV 2025 Author Kit from the CVF/ICCV author
  guidelines route and `cvpr-org/author-kit`.
  - https://media.eventhosts.cc/Conferences/ICCV2025/ICCV2025-Author-Kit.zip
  - https://github.com/cvpr-org/author-kit
- Vendored style files:
  - `iccv.sty`
  - `ieeenat_fullname.bst`
- Reason: ICCV 2027 official kit is not fixed in this repo yet, so the current
  public ICCV 2025 style is used as the closest ICCV-style source route. Update
  the style files when the exact target-year kit is released.

## Build

Content status:

- Main manuscript-content pass is complete as of 2026-05-26.
- The source includes fixed scope/denominator accounting, source-specific
  claim-boundary table, an Open3DSG-first main source-results table, controls,
  GT verifier evaluation, audit/sanity evidence in prose, explicit Open3DSG
  caveats, qualitative failure callout, limitations, and conclusion.
- Figure 1-3 PNG assets are converted and the include paths point to PNG files.
- Docker PDF build is verified with `h001-iccv-tex:20260525`: after
  compression, `main.pdf` builds to 9 review pages with no missing citations,
  undefined refs, or overfull hbox warnings.
- PDF visual/layout inspection is recorded in `inspection/report.md`. The
  current draft has no blocking visual issue and keeps Open3DSG as the first
  block in manuscript Table 3.

Build from this directory:

```bash
cd paper/iccv
pdflatex main
bibtex main
pdflatex main
pdflatex main
```

Host build has not been verified in this workspace because no TeX engine is
currently available on the host. `pdflatex`, `bibtex`, and `latexmk` were not
found on 2026-05-25.

Docker build route:

```bash
docker build -f paper/iccv/Dockerfile.tex -t h001-iccv-tex:20260525 paper/iccv
docker run --rm -v "$PWD/paper:/work" -w /work/iccv h001-iccv-tex:20260525 \
  latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
```

Verified run:

- Image build log: `logs/h001_iccv_tex_image_build_20260525_235416.log`
- PDF build log: `logs/h001_iccv_pdf_build_20260526_013847.log`
- Output: `paper/iccv/main.pdf`
- Page count: 9 review pages
- Current warnings: none from citations, references, or overfull hboxes in the
  latest build log `logs/h001_iccv_pdf_build_20260526_013847.log`
- Visual inspection: `paper/iccv/inspection/report.md`

## Figure Handling

The current tracked figure sources are SVG files under
`paper/generated/figures/`. PNG build assets were generated on 2026-05-25 using
Chrome headless screenshots:

- `../generated/figures/figure1_framework.png` from `figure1_framework.svg`
- `../generated/figures/figure2_tradeoff.png` from `figure2_tradeoff.svg`
- `../generated/figures/figure3_geometry_panels.png` from `figure3_geometry_panels.svg`

The `\figmaybe{...}` paths in `sec/6_results.tex` now point to the PNG files.

## Source Boundary

This is a manuscript source conversion, not a final camera-ready paper. Keep
claim wording scoped to measured geometry-checkable relation reliability across
VL-SAT and the Docker-reproduced averaged-BLIP Open3DSG variant.
