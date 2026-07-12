# GeoCalib AAAI-27 Manuscript

Last updated: 2026-07-12 KST

This directory contains only the active AAAI-27 source and the three canonical
review PDFs. Superseded manuscript snapshots, the AAAI-26 style, and historical
inspection notes live under `archive/paper/aaai_snapshots/`.

## Active Layout

| Path | Role |
| --- | --- |
| `main.tex`, `preamble.tex`, `sec/` | active anonymous main-paper source |
| `supplement.tex` | active three-page method, sensitivity, provenance, and transfer-development supplement source |
| `reproducibility_checklist_main.tex`, `reproducibility_checklist.tex` | standalone checklist source |
| `aaai2027.sty`, `aaai2027.bst` | active AAAI-27 style |
| `official/` | preserved official anonymous and checklist templates |
| `Dockerfile.tex` | pinned paper-build environment |
| `main_aaai27.pdf` | canonical main-paper review PDF |
| `supplement_aaai27.pdf` | canonical technical-supplement PDF |
| `reproducibility_checklist_aaai27.pdf` | canonical checklist PDF |

The default LaTeX outputs `main.pdf`, `supplement.pdf`, and
`reproducibility_checklist_main.pdf` are disposable build products and are not
canonical versions.

## Verified Outputs

- `main_aaai27.pdf`: 9 US-Letter pages; technical content through page 7 and
  pages 8--9 contain references only; SHA256
  `8f4632c8150affa764ef02b29696b1c538c9b288fc3f4879630813d0c22fcc1a`.
- `supplement_aaai27.pdf`: 3 US-Letter pages; SHA256
  `897ab70542d3e66be1f27813f94692fc97ee704e81b6fc0239cfdceea4d10441`.
- `reproducibility_checklist_aaai27.pdf`: 2 US-Letter pages; SHA256
  `166fe5d602079ab60d3b0c4e5b927c1ec1df44ff6a16d5308cf55f4a37d0c07d`.

All three have zero Type 3 fonts and no unresolved citations/references or
blocking LaTeX/overfull errors. Final main log:
`logs/h001_claim_lock_main_final_20260712.log`; figure generation log:
`logs/h001_strengthening_figure_regeneration_20260712.log`.

The current main paper excludes Codex-derived validity results. Its narrative
is failure-first; Figure 1 contains no review-checklist artifact, Figure 2 is a
three-source K trajectory, and Figure 3 shows two corrected examples plus one
residual failure. The Codex proxy appendix exists only in
`paper/paper_nonsub/` and must not enter the submission bundle.

## Build

From the repository root:

```bash
docker build -f paper/aaai/Dockerfile.tex -t h001-aaai27-tex:20260712 paper/aaai
docker run --rm -v "$PWD/paper:/work" -w /work/aaai \
  h001-aaai27-tex:20260712 \
  latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
docker run --rm -v "$PWD/paper:/work" -w /work/aaai \
  h001-aaai27-tex:20260712 \
  latexmk -pdf -interaction=nonstopmode -halt-on-error supplement.tex
docker run --rm -v "$PWD/paper:/work" -w /work/aaai \
  h001-aaai27-tex:20260712 \
  latexmk -pdf -interaction=nonstopmode -halt-on-error \
  reproducibility_checklist_main.tex
```

After verification, copy the default outputs to the three versioned canonical
filenames above, then remove LaTeX intermediates. Do not retain multiple PDFs
with identical hashes in this directory.

## Submission Bundle

The active OpenReview field bundle is
`release/h001_aaai27_openreview_20260712_083625/`. It contains renamed copies
of the three canonical PDFs plus the anonymized code/data ZIP. The earlier
compact tarball is a historical handoff artifact, not an upload source.

AAAI-27 policy lock: at most 7 technical pages and 9 total pages; pages 8--9
are references only. The checklist is uploaded separately. Supplementary
material is optional, anonymous, and not required reading.
