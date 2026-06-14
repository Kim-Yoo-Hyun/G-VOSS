# AAAI PDF Visual/Layout Inspection

Last updated: 2026-06-13 KST

## Build Checked

- PDF: `paper/aaai/main.pdf`
- Image build log:
  `logs/h001_aaai27_tex_image_build_20260611_aaai27_hygiene_retry1.log`
- PDF build log:
  `logs/h001_aaai_pdf_build_geocalib_figure_20260613_104500.log`
- Preview files generated locally: `/tmp/h001_aaai_geocalib_pages/page-1.png`
  and `/tmp/h001_aaai_geocalib_pages/page-5.png` through
  `/tmp/h001_aaai_geocalib_pages/page-7.png` for the latest focused check
- Page count: 9 total pages, US Letter
- Target-year route: official AAAI-27 Author Kit, checked 2026-06-11 KST;
  public AAAI-27 main-track instructions re-checked 2026-06-13 KST
- Technical content: pages 1-7
- References: start on page 7 and continue onto page 8
- Reproducibility checklist: starts after references on page 8 and continues
  onto page 9
- Build status: no missing citations, no final undefined references, no
  overfull hboxes, no LaTeX errors, and no AAAI package errors in the final
  `main.log`. The latest `latexmk` wrapper log still contains first-pass
  temporary undefined-reference warnings, which disappear in final `main.log`.
- Remaining layout warnings: one small `Overfull \vbox` (`0.77646pt`) plus
  underfull box warnings. No Type 3 fonts; `pdffonts` reports embedded Type 1
  fonts only.
- PDF SHA256:
  `ad230745e1fb833d19ddcaaf93497d7f8e698d329feb199bb9809bff8b3f24b3`.
- Naming status: the reviewer-facing method acronym is `GeoCalib`; `H001` no
  longer appears in the manuscript body source files.

The PNG preview files are generated inspection artifacts and are ignored by
`paper/aaai/.gitignore`. This report is the tracked inspection record.

## Claim/Caveat QA

Facts:

- Claim/caveat QA record:
  `paper/aaai/inspection/claim_qa_20260611.md`
- QA status: `claim_caveat_qa_pass_after_final_consistency_and_content_polish`
- Checked consistency targets: full official validation as the primary route,
  Open3DSG 548/548 `recovery_relaxed_views_min2` branch, exact-label
  geometry-checkable denominator 3,972, and residual calibration risk.
- Patched paper-facing experiment table artifacts that still had historical
  127-scan values or incomplete boundary rows: Table 1, Table 2, Table 3, and
  Table 5 across `.md`, `.csv`, and `.json` as applicable.
- Added final reviewer-defense wording for: not a hand-coded verifier, not a
  recovery-branch threshold-tuning step, exact-label denominator not relaxed,
  and Open3DSG denominator caveat retained through the 533/548 sensitivity
  branch.
- Docker PDF rebuild after the QA patch exited 0:
  `logs/h001_aaai_pdf_build_final_consistency_20260611_020517.log`

Inference:

- The paper source and tracked table artifacts now use the same
  full-validation claim boundary. Historical 127-scan numbers remain only in
  planning/sensitivity documents where they are explicitly marked as historical
  or sensitivity evidence.

## Page-Level Findings

Facts:

- Page 1: `GeoCalib` title, abstract, and introduction are readable.
- Page 2: introduction closes and related work begins.
- Page 3: problem formulation and method layout are readable.
- Page 4: experimental setup, results prose, controls, verifier/audit summary,
  and limitations are dense but readable.
- Page 5: fixed-scope table, source-boundary table, and manuscript Table 3 are
  readable. Table 3 now reports `K={5,10,20,50,100}` for both Recall and
  Violation, with Open3DSG first and VL-SAT as the controlled anchor block.
- Page 6: redrawn Figure 1, Figure 2, Figure 3, and limitations text are
  readable.
- Page 7: limitations tail, conclusion, and references appear in order.
- Page 8: references start and fill the page.
- Page 9: AAAI reproducibility checklist appears after the references.

Inference:

- The AAAI source now uses the official AAAI-27 Author Kit files and compiles
  under a Docker image that includes the additional `newtxtext` dependencies
  required by `aaai2027.sty`.
- The current source is target-year build-ready, but not final upload-ready:
  the working source is split across `main.tex` and `sec/*.tex`, while the
  AAAI-27 author-kit instructions say final source upload should be a single
  `.tex` source plus bibliography/used graphics. A local flattened package now
  exists under `release/h001_aaai27_submission_20260613_004455/`; actual portal
  upload requirements still need a final check immediately before submission.
- The AAAI-27 main-track call confirms a 7-page technical-content limit plus
  references, supplementary-material options, required reproducibility
  checklist, generative-AI responsibility, reviewer availability, responsible
  research, and reproducibility expectations. The final portal instructions
  still need one last check for whether the checklist is included in the main
  PDF or uploaded separately.
- Figure 2 and Figure 3 are single-column in the AAAI version to avoid wide
  floats drifting after references.
- The 2026-06-06 table-policy pass temporarily expanded the PDF to 10 pages;
  the compression pass restored 9 pages while preserving the full-validation
  main table policy and historical sensitivity wording.
- Wide floats stay before references and are readable. Table 3 is now placed
  with the other main evidence tables rather than after the conclusion.
- Figure 1 now uses a literature-survey-aligned evidence-record visual form:
  relation-source graph, identity-preserved edge evidence, and reliable
  relation graph with recall/violation readout.

## Verdict

Visual/layout inspection passed for AAAI-style draft continuation:

- build clean: yes
- technical content within 7 pages: yes
- references after technical content: yes
- reproducibility checklist after references: yes
- Open3DSG-main framing preserved: yes
- full-validation main table policy preserved: yes
- historical old 377/388 vs R2 388/388 sensitivity wording preserved: yes
- full-validation claim/caveat consistency after QA patch: yes
- target-year author-kit route: AAAI-27, build verified
- blocking visual issue: none
- reviewer-facing method name: `GeoCalib`
- manuscript-body `H001` strings: none

Required before submission:

1. Re-check final OpenReview/AAAI-27 portal instructions immediately before
   upload, especially checklist placement, supplementary upload form, source
   package contents, anonymization, and PDF metadata.
2. Re-check checklist answers after final artifact/code-release packaging,
   especially `partial` items for code release, preprocessing code, source
   code, comments, seeds, computing infrastructure, significance testing, and
   final hyperparameter/config manifest.
3. Decide whether to upload a supplementary technical appendix / code-data ZIP.
   Critical evidence must remain in the main paper because AAAI-27 says
   reviewers are not required to review supplementary material.
4. If submitting source, use or regenerate the local flattened package and
   exclude unused historical `aaai2026.*` files from the portal archive.

## AAAI-27 Submission Hygiene Check

Facts:

- Official page checked: `https://aaai.org/conference/aaai/aaai-27/main-technical-track-call/`.
- Latest public-instruction re-check: 2026-06-13 KST.
- Official author kit checked: `https://aaai.org/authorkit27/`, redirecting to
  `https://aaai.org/wp-content/uploads/2026/05/AuthorKit27.zip`.
- Author kit zip SHA256:
  `e28c6ac9bc6eb3b4e2d849547d2cefb5162610ee39d0a12e0dc62d1126b44a7d`.
- Local style SHA256:
  `aaai2027.sty` =
  `391bce82815bf698b8e382dd3ae7e30c75d7ab46df140cb295b1266016bc8623`;
  `aaai2027.bst` =
  `5db7765ba99de5c1e4686f9b3940a0add9c5e702f2164514462bec130ccb6e3c`.
- Docker image used: `h001-aaai-tex:20260611`, image id prefix
  `461fc997c889`.
- PDF SHA256:
  `ad230745e1fb833d19ddcaaf93497d7f8e698d329feb199bb9809bff8b3f24b3`.

Checklist status:

- The checklist now follows the AAAI-27 Author Kit question structure.
- Current answers are intentionally conservative. The computing-infrastructure
  answer is now `yes` because exact local hardware/software and Docker image
  ids are recorded. Several code/artifact items remain `partial` until portal
  upload, public URL/DOI, and release license files are actually fixed.
- No answer should be upgraded from `partial` to `yes` until the corresponding
  final package file or manifest exists.

## Local Submission Package

Facts:

- Package script:
  `paper/aaai/scripts/prepare_submission_package.sh`
- Latest package directory:
  `release/h001_aaai27_submission_20260613_004455/`
- Latest package archive:
  `release/h001_aaai27_submission_20260613_004455.tar.zst`
- Archive checksum file:
  `release/h001_aaai27_submission_20260613_004455.tar.zst.sha256`
- Archive SHA256:
  `144470f5fcf2d11ad07f69cae53bbfe69cb72ed5044235507f94c8dc88efc48f`
- Build log:
  `logs/h001_aaai_submission_pkg_build_20260613_004455.log`
- Verification report:
  `release/h001_aaai27_submission_20260613_004455/verification_report.md`

Verification result:

- Flattened source has no `\input{...}` or `\include{...}` commands.
- Package build exits 0 in Docker image `h001-aaai-tex:20260611`.
- Metadata-clean review PDF candidate has empty Title, Author, Subject, and
  Keywords in `pdfinfo`.
- Anonymous string scan found no obvious local identity strings.
- Embedded fonts have no Type 3 entries.
- Archive checksum verification passes.
- Remaining log warning is the same non-blocking `Overfull \vbox`
  (`0.77646pt`) plus underfull box warnings.

Inference:

- Source flattening/package hygiene is no longer the blocking item. The
  remaining blockers are external: final OpenReview/AAAI form requirements,
  artifact/code-release URL or DOI, supplement/code-data upload choice, and
  checklist `partial` answer review after the release package is fixed.

Supplement / appendix / ethics / review-instruction status:

- Supplement decision is fixed in `paper/aaai/submission_plan.md`: no separate
  technical appendix PDF for the current route; use code/data supplementary
  material only as reproducibility support if the portal accepts the current
  size/format.
- The full-validation result bundle is the preferred anonymous review artifact
  if upload constraints allow it:
  `release/h001_full_validation_results_20260611_025158.tar.zst`.
- If the portal requires `.zip`, create a wrapper at upload time rather than
  keeping a duplicate 1.4G archive in the repo now.
- Supplementary material is reviewer assistance only; main claims, caveats, and
  essential evidence stay in the 7-page main paper.
- The current work uses existing public research datasets and does not
  introduce human-subject data or a new dataset, but the final submission still
  needs an ethics/responsible-research pass for dataset license/access terms,
  AI-assisted writing/tool-use disclosure if required, and anonymization.
- AAAI-27 expects qualified authors to be available for light reviewing; this
  is a submission-process obligation, not a manuscript content item.
