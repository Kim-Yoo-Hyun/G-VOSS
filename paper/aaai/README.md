# AAAI-Style Manuscript Source

Last updated: 2026-06-24 KST

This directory is the AAAI-style LaTeX source conversion of the GeoCalib/H001 paper.
It is separate from `archive/paper/iccv/` so venue-specific formatting decisions do not
overwrite each other.

## Template Route

- Route chosen: AAAI Press LaTeX submission style.
- Paper-facing title: `GeoCalib: Calibrating Geometric Consistency for Reliable 3D Scene Graph Relations`
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

- Current source state should use `GeoCalib` in manuscript-facing prose and
  reserve `H001` for internal experiment/provenance paths.
- Open3DSG is framed as the main open-vocabulary relation-source case study.
- VL-SAT is framed as the controlled reproduced anchor.
- Low-K reporting is accepted for K = `{5,10,20,50,100}`. Current-source
  point-metric provenance is available in the paper-facing `metrics_k_sweep/`
  roots, and K=1 is not a paper metric.
- The active Method section frames `semantic_score * p_geom_valid` as the
  `lambda=1` instance of a risk-aware soft re-ranking utility; this is a prose
  clarification of the existing GeoCalib score, not a new tuned metric.
- Family-conditional calibrated geometry risk is the active H001_v2
  method-development direction. Paper-facing text may report the frozen
  family-calibrator artifact as `family_conditional_risk`; legacy metric JSON
  keys remain unchanged unless full metric/table regeneration is intentionally
  rerun.
- Qwen-VL is a completed third-source extension and should not replace the
  VL-SAT/Open3DSG main-source framing unless explicitly promoted.
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
docker build -f paper/aaai/Dockerfile.tex -t h001-aaai-tex:20260526 paper/aaai
docker run --rm -v "$PWD/paper:/work" -w /work/aaai h001-aaai-tex:20260526 \
  latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
```

The AAAI style forbids `hyperref` and several layout packages. Do not copy the
ICCV preamble blindly into this directory.

Verified run:

- Image build log: `logs/h001_aaai_tex_image_build_full_validation_20260605_100108.log`
- PDF build log: `logs/h001_aaai_pdf_build_h001v2_family_conditional_naming_20260624_130846.log`
- Output: `paper/aaai/main.pdf`
- Page count: 9 total pages
- Technical content: pages 1-7
- References: page 8
- Reproducibility checklist: page 9
- Current warnings: targeted grep found no missing citations, undefined
  references, overfull hboxes, LaTeX errors, or AAAI package errors in the
  latest `main.log`; `pdffonts` reports Type 1 fonts only. Remaining underfull
  box warnings are non-blocking.
- Visual inspection: `paper/aaai/inspection/report.md`

## Source Boundary

This is a venue-style conversion, not a final submission. Before upload,
verify the exact target-year author kit, portal form, page limit,
supplementary/code-data policy, reproducibility checklist format,
artifact-link/DOI requirements, and ethics/review instructions from the official
AAAI/OpenReview site. Regenerate any flattened release package created before
the GeoCalib/Figure-1 update.
