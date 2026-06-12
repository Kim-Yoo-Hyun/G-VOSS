# AAAI-Style Manuscript Source

Last updated: 2026-06-11 KST

This directory is the AAAI-style LaTeX source conversion of the H001 paper.
It is separate from `paper/iccv/` so venue-specific formatting decisions do not
overwrite each other.

## Template Route

- Route chosen: AAAI Press LaTeX submission style.
- Current style files:
  - `aaai2027.sty`
  - `aaai2027.bst`
- Official AAAI-27 main technical track page checked on 2026-06-11 KST:
  - https://aaai.org/conference/aaai/aaai-27/main-technical-track-call/
- Current style-file source:
  - Official AAAI-27 Author Kit: https://aaai.org/authorkit27/
- Official kit check on 2026-06-11 KST:
  - `https://aaai.org/authorkit27/` redirects to
    `https://aaai.org/wp-content/uploads/2026/05/AuthorKit27.zip`.
  - HTTP metadata observed: content type `application/zip`, content length
    `5495535`, last modified `Thu, 28 May 2026 15:54:36 GMT`.
  - Zip SHA256:
    `e28c6ac9bc6eb3b4e2d849547d2cefb5162610ee39d0a12e0dc62d1126b44a7d`.
  - `paper/aaai/aaai2027.sty` and `paper/aaai/aaai2027.bst` were copied from
    `AuthorKit27/`.
  - Style SHA256:
    `391bce82815bf698b8e382dd3ae7e30c75d7ab46df140cb295b1266016bc8623`.
  - BST SHA256:
    `5db7765ba99de5c1e4686f9b3940a0add9c5e702f2164514462bec130ccb6e3c`.
  - Official `ReproducibilityChecklist.tex` SHA256:
    `06a3459158089bf1c64b738986118f1d1566e816da4b710c6397561e33c3d5e6`.
  - Local checklist was migrated to the AAAI-27 question structure while
    keeping H001-specific answers concise.

Important AAAI-27 constraints from the official main-track page and author kit:

- Papers use AAAI two-column style on US Letter.
- Submissions are anonymous for double-blind review.
- Main-track submissions may have up to 7 pages of technical content plus
  additional pages solely for references.
- Supplementary material is allowed but reviewers are not required to review it;
  critical evidence must stay in the main paper. AAAI-27 lists technical
  appendix, multimedia, and code/data as possible supplementary material, due
  3 days after the paper deadline.
- Authors must complete a reproducibility checklist.
- Qualified authors must be available for light reviewing unless exempt.
- The AAAI-27 author kit forbids `hyperref`, page-break commands in final
  source, layout-changing packages/commands, non-embedded fonts, and Type 3
  fonts. It also says the submitted LaTeX source should be flattened to a
  single `.tex` file for source upload, with only the `.bib` and used graphics
  as separate files.
- The current working source is still split into `main.tex` plus `sec/*.tex`
  for maintainability. Before final source upload, generate a flattened
  submission source archive and exclude unused historical files such as
  `aaai2026.*`.

## Content Status

- Open3DSG is framed as the main open-vocabulary relation-source case study.
- VL-SAT is framed as the controlled reproduced anchor.
- The Results section includes Docker subgraph bootstrap CIs as
  evaluation-context uncertainty checks, not repeated-training variance.
- The current source keeps the Open3DSG caveats explicit: selected official
  non-averaged checkpoint, filtered train/dev provenance, full-validation
  exact-label denominator 3,972, 548/548 recovery-policy branch,
  533/548 covered branch as sensitivity evidence, and residual calibration risk.
- Controls, GT verifier evaluation, structured audit, and visual sanity checks
  are prose-backed reviewer-defense evidence unless an appendix is added.

## Build

Host build has not been verified in this workspace. Use Docker for reproducible
paper builds:

```bash
docker build -f paper/aaai/Dockerfile.tex -t h001-aaai-tex:20260611 paper/aaai
docker run --rm -v "$PWD/paper:/work" -w /work/aaai h001-aaai-tex:20260611 \
  latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
```

The AAAI style forbids `hyperref` and several layout packages. AAAI-27 also
loads its own Times-like text font through `newtxtext`, so do not load
`times`, `helvet`, `courier`, or any other text-font package in this source.
The Dockerfile includes `texlive-fonts-extra` and `texlive-plain-generic`
because `aaai2027.sty` / `newtxtext` require them.

Verified run:

- Image build log:
  `logs/h001_aaai27_tex_image_build_20260611_aaai27_hygiene_retry1.log`
- PDF build log:
  `logs/h001_aaai_pdf_build_qwen_extension_update_20260611_121205.log`
- Output: `paper/aaai/main.pdf`
- Page count: 9 total pages
- Technical content and references/checklist: see
  `paper/aaai/inspection/report.md` for page-level inspection. The working
  source no longer forces `\clearpage` before references/checklist.
- Current warnings: no missing citations, no final undefined references, no
  overfull hboxes, no LaTeX errors, and no AAAI package errors in the final
  `main.log`. One small overfull vbox warning (`0.77646pt`) and underfull box
  warnings remain non-blocking layout warnings.
- Font check: `pdffonts paper/aaai/main.pdf` reports embedded Type 1 fonts only;
  no Type 3 fonts.
- Visual inspection: `paper/aaai/inspection/report.md`

## Source Boundary

This is a venue-style working source, not a final source-upload archive. Before
AAAI submission, perform one more target-year check against the official AAAI
site and OpenReview instructions, fix the final artifact/code-release URL or
DOI, flatten the LaTeX source if source upload requires it, strip PDF metadata
if required for anonymity, and decide whether a supplementary technical
appendix/code-data ZIP is being uploaded.
