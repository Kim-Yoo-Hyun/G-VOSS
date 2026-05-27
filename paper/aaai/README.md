# AAAI-Style Manuscript Source

Last updated: 2026-05-27 KST

This directory is the AAAI-style LaTeX source conversion of the H001 paper.
It is separate from `paper/iccv/` so venue-specific formatting decisions do not
overwrite each other.

## Template Route

- Route chosen: AAAI Press LaTeX submission style.
- Current style files:
  - `aaai2026.sty`
  - `aaai2026.bst`
- Official AAAI-26 submission page checked on 2026-05-26 KST:
  - https://aaai.org/conference/aaai/aaai-26/submission-instructions/
- Official AAAI-26 reproducibility checklist page checked on 2026-05-26 KST:
  - https://aaai.org/conference/aaai/aaai-26/reproducibility-checklist/
- Current style-file source:
  - Official AAAI-26 Author Kit: https://aaai.org/authorkit26-1/
- Official kit check on 2026-05-27 KST:
  - `https://aaai.org/authorkit26-1/` redirects to
    `https://aaai.org/wp-content/uploads/2025/07/AuthorKit26-1.zip`.
  - Zip SHA256:
    `d2844ec68a4a9396d749fcca5b5784809617b670863e8d4fecbfb00e444fc3af`.
  - `paper/aaai/aaai2026.sty` was replaced from
    `AuthorKit26/AnonymousSubmission/LaTeX/aaai2026.sty`.
  - `paper/aaai/aaai2026.bst` already matched the official kit.
  - Style SHA256:
    `6f90c4d7a36f4a038daf187fdd6cec9fe578aba819733b49551574a37feecd35`.
  - BST SHA256:
    `ac26e2c66047435c0ed25f21ae36ad42d731cf3d794c4a8b5f05a62141a27294`.
- AAAI-27 check on 2026-05-27 KST:
  - `https://aaai.org/conference/aaai/aaai-27/submission-instructions/`
    redirects to an older AAAI-25 page, so no official AAAI-27 author kit is
    confirmed here yet.

Important AAAI-26 constraints from the official submission page:

- Papers use AAAI two-column style on US Letter.
- Submissions are anonymous for double-blind review.
- Regular submissions allow up to 7 pages of technical content plus additional
  pages for references and the reproducibility checklist.
- The PDF must be trouble-free and high-resolution with Type 1 or TrueType
  fonts.
- The reproducibility checklist is included after the references and does not
  count toward the page limit. The current draft includes the checklist in
  `sec/9_reproducibility_checklist.tex`.

## Content Status

- Open3DSG is framed as the main open-vocabulary relation-source case study.
- VL-SAT is framed as the controlled reproduced anchor.
- The Results section includes Docker subgraph bootstrap CIs as
  evaluation-context uncertainty checks, not repeated-training variance.
- The current source keeps the Open3DSG caveats explicit:
  averaged-BLIP variant, filtered train/dev split, covered H001 scope,
  exact-label denominator, `validation_missing_preprocessed:11`, and residual
  calibration risk.
- Controls, GT verifier evaluation, structured audit, and visual sanity checks
  are prose-backed reviewer-defense evidence unless an appendix is added.

## Build

Host build has not been verified in this workspace. Use Docker for reproducible
paper builds:

```bash
docker build -f paper/aaai/Dockerfile.tex -t h001-aaai-tex:20260526 paper/aaai
docker run --rm -v "$PWD/paper:/work" -w /work/aaai h001-aaai-tex:20260526 \
  latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
```

The AAAI style forbids `hyperref` and several layout packages. Do not copy the
ICCV preamble blindly into this directory.

Verified run:

- Image build log: `logs/h001_aaai_tex_image_build_20260526_015436.log`
- PDF build log: `logs/h001_aaai_pdf_build_official_kit_20260527_024752.log`
- Output: `paper/aaai/main.pdf`
- Page count: 9 total pages
- Technical content: pages 1-7
- References: page 8
- Reproducibility checklist: page 9
- Current warnings: no missing citations, undefined references, overfull hboxes,
  LaTeX errors, or AAAI package errors in the latest build log
- Visual inspection: `paper/aaai/inspection/report.md`

## Source Boundary

This is a venue-style conversion, not a final submission. Before AAAI
submission, verify the exact target-year author kit, page limit, supplementary
material policy, reproducibility checklist format, and ethics/review
instructions from the official AAAI site.
