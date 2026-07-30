# RelCompat3D AAAI-27 Source

Last updated: 2026-07-29 KST

This directory contains the active anonymous AAAI-27 source and the canonical
main-paper, Technical Supplement, and reproducibility-checklist PDFs.

## Active Layout

| Path | Role |
| --- | --- |
| `main.tex` | Only main-paper entry point |
| `sec/0_abstract.tex`--`sec/6_conclusion.tex` | Main sections in manuscript order |
| `supplement.tex`, `sec/supplement.tex` | Technical supplement |
| `reproducibility_checklist_main.tex`, `reproducibility_checklist.tex` | Standalone checklist |
| `aaai2027.sty`, `aaai2027.bst` | AAAI-27 style and bibliography style |
| `official/` | Preserved official templates |
| `Dockerfile.tex` | Pinned LaTeX environment |
| `main_aaai27.pdf` | Canonical main PDF |
| `supplement_aaai27.pdf` | Canonical supplement PDF |
| `reproducibility_checklist_aaai27.pdf` | Canonical checklist PDF |

The supplement wrapper contains its own required packages and commands.
`preamble.tex`, legacy teaser wrappers, debug builds, and alternate build
directories are not part of the active source.

## Main-Paper Structure

1. Abstract
2. Introduction
3. Related Work
4. Method
5. Experiments
6. Discussion and Limitations
7. Conclusion

The evaluation scope includes support/contact, proximity, and vertical order.
Family-aware re-ranking changes proximity and vertical-order candidates while
preserving the source family sequence and support/contact order.

## Build

From the repository root:

```bash
docker build -f paper/aaai/Dockerfile.tex \
  -t relcompat3d-aaai27-tex:20260712 paper/aaai

docker run --rm -v "$PWD/paper:/work" -w /work/aaai \
  relcompat3d-aaai27-tex:20260712 \
  latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex

docker run --rm -v "$PWD/paper:/work" -w /work/aaai \
  relcompat3d-aaai27-tex:20260712 \
  latexmk -pdf -interaction=nonstopmode -halt-on-error supplement.tex

docker run --rm -v "$PWD/paper:/work" -w /work/aaai \
  relcompat3d-aaai27-tex:20260712 \
  latexmk -pdf -interaction=nonstopmode -halt-on-error \
  reproducibility_checklist_main.tex
```

Copy the verified outputs to the corresponding `*_aaai27.pdf` names, then
remove default PDFs and LaTeX intermediates. Do not retain duplicate canonical
PDFs.

## Verification

For every final build:

- main technical content must remain within pages 1--7 and total main length
  within 9 pages;
- undefined citations/references, BibTeX warnings, graphics warnings, and
  overfull boxes must be zero;
- all pages must be US Letter and PDF 1.5;
- Type 3, CID/Identity-H, and unembedded fonts must be absent;
- all sources and PDFs must remain anonymous;
- the Technical Supplement must remain below the 10MB upload limit;
- canonical hashes must match the recorded submission inventory.

Current page counts and hashes are recorded in `../reproducibility.md`.

## Submission Boundary

The main paper is self-contained. The supplement provides detailed proofs,
controls, sensitivities, intervals, and reproducibility checks. Licensed raw
data, stable source identifiers, source-derived row bundles, third-party
checkpoints, obsolete experiment branches, and historical manuscript routes
are excluded from the review upload. No Media Supplement or Code and Data
Supplement is submitted during review. Artifact release remains an internal
post-acceptance task and a post-publication reproducibility-checklist
commitment, subject to third-party access terms.
