# AAAI-Style Manuscript Source

Last updated: 2026-06-13 KST

This directory is the AAAI-style LaTeX source conversion of the GeoCalib paper.
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
    keeping experiment-specific answers concise.

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

- The paper-facing title acronym is fixed as `GeoCalib`, expanded in the title
  as `GeoCalib: Calibrating Geometric Consistency for Reliable 3D Scene Graph
  Relations`.
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
- Figure 1 is redrawn as a three-panel evidence-record schematic:
  relation-source graph, identity-preserved edge evidence, and reliable
  relation graph with recall/violation readout.

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
  `logs/h001_aaai_pdf_build_geocalib_figure_20260613_104500.log`
- Output: `paper/aaai/main.pdf`
- Page count: 9 total pages
- Technical content and references/checklist: see
  `paper/aaai/inspection/report.md` for page-level inspection. The working
  source no longer forces `\clearpage` before references/checklist.
- Current warnings: no missing citations, no final undefined references, no
  overfull hboxes, no LaTeX errors, and no AAAI package errors in the final
  `main.log`. One small overfull vbox warning (`0.77646pt`) and underfull box
  warnings remain non-blocking layout warnings.
- Current Table 3 reports the main source results across
  `K={5,10,20,50,100}` while retaining the standard `K=50/100` operating
  points.
- The main manuscript body no longer uses `H001` as the method name; internal
  experiment paths still use the existing repository folder names.
- PDF SHA256:
  `ad230745e1fb833d19ddcaaf93497d7f8e698d329feb199bb9809bff8b3f24b3`.
- Font check: `pdffonts paper/aaai/main.pdf` reports embedded Type 1 fonts only;
  no Type 3 fonts.
- Visual inspection: `paper/aaai/inspection/report.md`

## Submission Decisions

Submission-side decisions are tracked in:

```text
paper/aaai/submission_plan.md
```

Current decisions:

- Do not add an external artifact URL to the anonymous review manuscript unless
  the final AAAI/OpenReview form explicitly asks for one.
- Use OpenReview supplementary upload for anonymous review artifacts if portal
  size/format constraints allow it.
- Use GitHub for post-anonymity source release and Zenodo DOI as the canonical
  fixed full-validation result-bundle release after acceptance/public release.
- Do not add a separate technical appendix PDF for the current route; the main
  paper remains self-contained, and supplementary material is only for
  reproducibility support.

## Submission Package

Submission-hygiene package generation is now scripted:

```bash
bash paper/aaai/scripts/prepare_submission_package.sh
```

Latest generated package:

- package directory:
  `release/h001_aaai27_submission_20260613_004455/`
- archive:
  `release/h001_aaai27_submission_20260613_004455.tar.zst`
- archive checksum:
  `release/h001_aaai27_submission_20260613_004455.tar.zst.sha256`
- package build log:
  `logs/h001_aaai_submission_pkg_build_20260613_004455.log`
- verification report:
  `release/h001_aaai27_submission_20260613_004455/verification_report.md`

Current status: this package predates the latest GeoCalib/Figure 1 source pass
and the PDF build
`logs/h001_aaai_pdf_build_geocalib_figure_20260613_104500.log`. Treat it as a
historical hygiene check, not the final upload package. Regenerate the flattened
package before any actual AAAI/OpenReview upload.

Verification status:

- flattened `main.tex` has no `\input{...}` or `\include{...}` commands.
- package contains only the minimal compile set: flattened `main.tex`,
  `references.bib`, `aaai2027.sty`, `aaai2027.bst`, three used figure PNGs,
  generated `.bbl`/build files, PDF, metadata-clean review PDF, checksums, and
  a package README.
- metadata-clean review PDF candidate:
  `main_review_metadata_clean.pdf`; `pdfinfo` reports empty Title, Author,
  Subject, and Keywords.
- anonymous string scan found no obvious local identity strings.
- `pdffonts` reports embedded Type 1C fonts only and no Type 3 fonts.
- archive checksum verification passed with:
  `sha256sum -c release/h001_aaai27_submission_20260613_004455.tar.zst.sha256`.
- remaining log issue is the same non-blocking small `Overfull \vbox`
  (`0.77646pt`) plus underfull box warnings.

This package is a local submission-hygiene artifact and is now stale relative
to the current GeoCalib source. The final portal upload still needs package
regeneration plus the actual OpenReview/AAAI form check for upload size/format,
source-package constraints, checklist placement, and any required artifact URL
field. Artifact/release and supplement-upload policy is fixed in
`paper/aaai/submission_plan.md`.

## Source Boundary

This is a venue-style working source. A flattened local package now exists, but
the actual AAAI/OpenReview upload should still be checked immediately before
submission because portal fields and source/supplement requirements can change.
The unresolved external decisions are artifact/code-release URL or DOI,
supplementary technical appendix/code-data upload, and whether any checklist
`partial` answer can be upgraded after the final release package is fixed.
