# ICCV-Style Manuscript Source

Last updated: 2026-05-25 KST

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

Build from this directory:

```bash
cd paper/iccv
pdflatex main
bibtex main
pdflatex main
pdflatex main
```

Build has not been verified in this workspace because no TeX engine is
currently available on the host. `pdflatex`, `bibtex`, `latexmk`,
`rsvg-convert`, and `inkscape` were not found on 2026-05-25.

## Figure Handling

The current tracked figure sources are SVG files under
`paper/generated/figures/`. This LaTeX source uses figure placeholders unless
PDF/PNG versions are generated. Before final build, convert:

- `../generated/figures/figure1_framework.svg`
- `../generated/figures/figure2_tradeoff.svg`
- `../generated/figures/figure3_geometry_panels.svg`

to PDF or PNG and update the `\figmaybe{...}` paths in `sec/6_results.tex` if
needed.

## Source Boundary

This is a manuscript source conversion, not a final camera-ready paper. Keep
claim wording scoped to measured geometry-checkable relation reliability across
VL-SAT and the Docker-reproduced averaged-BLIP Open3DSG variant.
