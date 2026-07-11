# AAAI-Style Manuscript Source

Last updated: 2026-07-12 KST

This directory is the AAAI-style LaTeX source conversion of the GeoCalib/H001 paper.
It is separate from `archive/paper/iccv/` so venue-specific formatting decisions do not
overwrite each other.

## Template Route

- Route chosen: AAAI Press LaTeX submission style.
- Paper-facing title: `GeoCalib: Calibrating Geometric Consistency for Reliable 3D Scene Graph Relations`
- Current style files:
  - `aaai2027.sty`
  - `aaai2027.bst`
- Official AAAI-27 anonymous template:
  `official/AnonymousSubmission2027.tex`; standalone checklist template:
  `official/ReproducibilityChecklist.tex`.
- Active sources: `main.tex`, `supplement.tex`, and
  `reproducibility_checklist_main.tex`. The checklist is a separate OpenReview
  upload and is no longer appended to the paper PDF.
- Verified outputs (2026-07-12 KST): `main_aaai27.pdf` (9 pages: technical
  content through page 7, references only on pages 8--9),
  `supplement_aaai27.pdf` (1 page), and
  `reproducibility_checklist_aaai27.pdf` (2 pages). All are US Letter, have
  zero Type 3 fonts, and have no unresolved citations/references or blocking
  LaTeX/overfull errors.
- Current Docker image/logs: `h001-aaai27-tex:20260712`, final main rebuild
  `logs/h001_aaai27_main_build_20260712.log`, and supplement/checklist triplet
  verification `logs/h001_aaai27_final_triplet_build_20260712.log`.
- Current OpenReview upload set:
  `release/h001_aaai27_openreview_20260712_083625/`.

AAAI-27 policy verified on 2026-07-12 KST:

- Main paper: at most 7 technical pages and 9 total pages; pages after 7 are
  references only.
- OpenReview upload fields and live limits: paper PDF 10 MB, standalone
  checklist PDF 5 MB, technical-supplement PDF 10 MB, code/data ZIP 50 MB,
  and optional media ZIP 50 MB.
- Supplementary material is optional, anonymous, and not required reading.
  External paper code/data repository links, including anonymous repository
  links, are not accepted in place of the uploaded code/data supplement.
- Official policy owners are the AAAI-27 main-track call, submission
  instructions, supplementary-material page, and the live OpenReview
  submission invitation. Portal metadata is summarized in the release
  directory's `submission_metadata.md`.

## Historical AAAI-26 Route

The entries below record the superseded AAAI-26 conversion and are not the
current submission instructions.

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

Historical AAAI-26 constraints from the official submission page:

- Papers use AAAI two-column style on US Letter.
- Submissions are anonymous for double-blind review.
- Regular submissions allow up to 7 pages of technical content plus additional
  pages for references and the reproducibility checklist.
- The PDF must be trouble-free and high-resolution with Type 1 or TrueType
  fonts.
- The reproducibility checklist is included after the references and does not
  count toward the page limit. The current draft includes the checklist in
  `sec/9_reproducibility_checklist.tex`. That file is now legacy and is not
  included by the active AAAI-27 source.

## Content Status

- Current source state should use `GeoCalib` in manuscript-facing prose and
  reserve `H001` for internal experiment/provenance paths.
- Open3DSG is framed as the main open-vocabulary relation-source case study.
- VL-SAT is framed as the controlled reproduced anchor.
- Low-K reporting is accepted for K = `{5,10,20,50,100}`. Current-source
  point-metric provenance is available in the paper-facing `metrics_k_sweep/`
  roots, and K=1 is not a paper metric.
- The active Method section is framework-first. It defines the calibrated
  product (`family_conditional_risk = semantic_score * p_geom_valid_family`)
  and the pre-specified scale-robust rank-average as two soft GeoCalib fusion
  instantiations; neither is claimed universally dominant.
- `probabilistic_recalibrated` remains in the paper as the pooled calibrated
  ablation/baseline: `semantic_score * p_geom_valid`. It is distinct from the
  calibrator-only/no-source-score control, which ranks by `p_geom_valid`
  without semantic score. Because that calibrator retains predicate/family and
  interaction features, it is not true `G`-only; the separate strict factor
  audit now supplies that condition.
- Factor contract in the active source: `T_e` = predicate/family semantics,
  raw `G_e` = predicate-independent same-pair geometry, `Z_e` = source
  confidence, `C_e=P(y_cal=1|T_e,G_e)`, and `Z_e notin C_e`. `y_cal` is the
  constructed train/dev target, not direct human physical validity.
- Strict factor-isolation and counterfactual controls are complete and reported
  in Results. They remain a separate mechanism audit outside the SGFN gate;
  failed pooled-interaction structural checks block a generic interaction claim.
- Legacy metric JSON keys remain unchanged unless full metric/table
  regeneration is intentionally rerun.
- Qwen-VL is a completed third-source extension and should not replace the
  VL-SAT/Open3DSG main-source framing unless explicitly promoted.
- Selected paired subgraph-bootstrap ranges are reported in prose; they measure
  evaluation-context uncertainty, not repeated-training variance.
- The current source keeps the Open3DSG caveats explicit: selected official
  non-averaged checkpoint, filtered train/dev provenance, full-validation
  exact-label denominator 3,972, 548/548 recovery-policy branch,
  533/548 covered branch as sensitivity evidence, and residual calibration risk.
- Controls, GT verifier evaluation, the two-pass Codex LLM proxy audit, and
  visual sanity checks are prose-backed reviewer-defense evidence.

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
- PDF build log: `logs/h001_aaai_pdf_build_family_main_20260625_084157.log`
- Output: `paper/aaai/main.pdf`
- Page count: 10 total pages
- Technical content: pages 1-7
- References: pages 8-9
- Reproducibility checklist: page 10
- Current warnings: targeted grep found no missing citations, undefined
  references, overfull hboxes, LaTeX errors, or AAAI package errors in the
  latest `main.log`; `pdffonts` reports Type 1 fonts only. Remaining underfull
  box warnings are non-blocking.
- Visual inspection: `paper/aaai/inspection/report.md`

Top-tier style review build:

- Review note: `paper/top_tier_review.md`
- PDF build log: `logs/h001_aaai_pdf_build_top_tier_review_20260625_095933.log`
- Output: `paper/aaai/main_top_tier_review.pdf`
- Treat `main_top_tier_review.pdf` as the reviewed manuscript snapshot, not as
  a byte-for-byte copy of the ignored `main.pdf` build artifact. If the review
  snapshot is regenerated, build from the reviewed source and write the target
  PDF explicitly.
- The original `paper/aaai/main.pdf` is preserved.
- Main deltas: Figure 1 is now a failure-example-to-method schematic; the old
  claim-boundary table was demoted to prose; controls moved to a compact
  diagnostics table; implementation-facing condition names were replaced by
  manuscript-facing names in tables; references now start without a forced
  page break to avoid an empty final technical-content column.

Reference-expansion source-validation build:

- Survey note: `literature/geocalib_reference_expansion_20260625.md`
- PDF build log: `logs/h001_aaai_pdf_build_reference_expansion_20260625_130811.log`
- Output: `paper/aaai/main_reference_expansion.pdf`
- Page count: 9 total pages
- References: start on page 7
- Reproducibility checklist: page 9
- The original `paper/aaai/main.pdf` is preserved.
- Main deltas: `paper/references.bib` now has 34 used entries; Related Work is
  grouped into direct relation predictors, open-vocabulary 3D graphs,
  geometry-aware relation evidence, and calibration/reliability; `\method`
  now expands to the paper-facing name `GeoCalib`.

Reviewer-process cleanup validation build:

- Output: `paper/aaai/main_reviewer_cleanup.pdf`
- Page count: 9 total pages
- Page size: US Letter
- The original `paper/aaai/main.pdf` is preserved.
- Main deltas: paper-planning docs now match the current table order
  (`Table 1` scope, `Table 2` main source results, `Table 3`
  controls/diagnostics), and Qwen-VL boundary wording moved out of Related Work
  into Experimental Setup / Limitations.
- Targeted checks found no stale current-table wording, missing citations,
  undefined references, overfull hboxes, LaTeX errors, or package errors.

Framework-first SGFN confirmation build:

- Output: `paper/aaai/main_framework_first.pdf`.
- Final build log:
  `logs/h001_aaai_pdf_build_framework_first_final4_20260710.log`, exit 0.
- Page count: 10 total; technical content pages 1--7, references start on page
  8, and the reproducibility checklist starts on page 10.
- Main change: GeoCalib is framed as the calibrated geometry-consistency
  framework. Calibrated product and pre-specified rank-average are two soft
  fusion instantiations; the prospective SGFN K=100 table confirms the
  framework-level joint gate without claiming formula or family dominance.
- That snapshot discloses verifier-derived V, `support_contact` regression,
  the then-pending independent-human boundary, v1/v2/v3 pre-inference
  provenance, and 11 self-GT denominator rows.
- Final checks find US Letter output, Type 1 fonts only, and no final missing
  citation, undefined reference, overfull hbox, LaTeX/package, or fatal error.
- Visual render root:
  `logs/h001_aaai_framework_first_final_render_20260710/`.

Factor-isolated framework build:

- Output: `paper/aaai/main_factorized_framework.pdf`.
- Build log:
  `logs/h001_aaai_pdf_build_factorized_framework_20260710.log`, exit 0.
- Status: 10 US-Letter pages; technical content ends on page 7, references are
  pages 8--9, and checklist is page 10. Type 3 fonts, final missing
  citations/references, LaTeX errors, and overfull boxes are zero.
- Content: explicit `T_e/G_e/Z_e/C_e` factorization, constructed `y_cal`
  provenance, `Z_e notin inputs(C_e)` leakage boundary, product/rank-average
  `F(Z_e,C_e)` framing, and accurate calibrator-only/no-`Z_e` control naming.
  At that snapshot, factor-isolation diagnostics were not yet presented as
  completed results.
- Visual render root:
  `logs/h001_aaai_factorized_framework_render_20260710/`.
- The original `paper/aaai/main.pdf` remains preserved.

LLM proxy-audit and completed-factor build:

- Output: `paper/aaai/main_llm_proxy_audit.pdf`.
- Build log: `logs/h001_aaai_pdf_build_llm_proxy_audit_20260711.log`, exit 0.
- Status: 10 US-Letter pages; technical content is pages 1--7, references are
  pages 8--9, and checklist is page 10. Type 3 fonts, final missing
  citations/references, LaTeX errors, and overfull boxes are zero.
- Content: Codex is explicitly named as the LLM physical-validity proxy
  annotator/evaluator; both blinded pass distributions, agreement, same-model
  dependence, and non-human boundary are reported. The strict true-$G$ and
  counterfactual controls are also reported in Results.
- PDF SHA-256:
  `548dca31bb10256472ef89273c589d06acefa1140b8943238cb31c9d9a2901b9`.

Replica negative-transfer disclosure build:

- Main output: `paper/aaai/main_replica_disclosure.pdf`.
- Supplement output: `paper/aaai/supplement_replica_negative.pdf`.
- Build logs:
  `logs/h001_aaai_pdf_build_replica_disclosure_20260712.log` and
  `logs/h001_aaai_supplement_build_replica_negative_20260712.log`.
- Main status: 10 US-Letter pages; technical content pages 1--7, references
  pages 8--9, checklist page 10. Supplement status: one US-Letter page.
- Both have Type 3 fonts, final missing citations/references, LaTeX errors, and
  overfull boxes equal to zero. Main/supplement SHA-256 values are
  `3158ec793fb55d7f9431784a5e7569647571d5bf95ff0e55518eceb0010e8e28`
  and `9c51f561473ca17e8a2a164147c2c68575f7f1beefa08984eab8cd954c560fa3`.
- Content decision: SGFN remains positive source-level prospective evidence;
  untouched ReplicaSSG/FROSS is disclosed as a frozen negative-transfer result
  that blocks dataset-level generality.

## Source Boundary

The target-year format and live OpenReview fields are now verified. Use
`release/h001_aaai27_openreview_20260712_083625/` for upload. The earlier
`release/h001_aaai27_submission_20260712_005127.tar.zst` is a preserved compact
handoff snapshot, not the active OpenReview field bundle.
