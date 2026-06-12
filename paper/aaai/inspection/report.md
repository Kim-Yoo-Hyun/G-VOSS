# AAAI PDF Visual/Layout Inspection

Last updated: 2026-06-11 KST

## Build Checked

- PDF: `paper/aaai/main.pdf`
- Image build log:
  `logs/h001_aaai27_tex_image_build_20260611_aaai27_hygiene_retry1.log`
- PDF build log:
  `logs/h001_aaai_pdf_build_qwen_extension_update_20260611_121205.log`
- Preview files generated locally: `/tmp/h001_aaai_pages/page-4.png` through
  `/tmp/h001_aaai_pages/page-7.png` for the latest focused check
- Page count: 9 total pages, US Letter
- Target-year route: official AAAI-27 Author Kit, checked 2026-06-11 KST
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

The PNG preview files are generated inspection artifacts and are ignored by
`paper/aaai/.gitignore`. This report is the tracked inspection record.

## Claim/Caveat QA

Facts:

- Claim/caveat QA record:
  `paper/aaai/inspection/claim_qa_20260611.md`
- QA status: `claim_caveat_qa_pass_after_final_consistency_and_content_polish`
- Checked consistency targets: full official validation as the primary route,
  Open3DSG 548/548 `recovery_relaxed_views_min2` branch, exact-label
  H001-family denominator 3,972, and residual calibration risk.
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

- Page 1: title, abstract, and introduction are readable.
- Page 2: introduction closes and related work begins.
- Page 3: problem formulation and method layout are readable.
- Page 4: experimental setup, results prose, controls, verifier/audit summary,
  and limitations are dense but readable.
- Page 5: fixed-scope table, source-boundary table, limitations tail, and
  conclusion are readable.
- Page 6: Figure 1, manuscript Table 3, and Figure 2 are readable. Open3DSG is
  the first block in Table 3; VL-SAT is the controlled anchor block.
- Page 7: Figure 3 appears before references and remains in technical content.
- Page 8: references start and fill the page.
- Page 9: AAAI reproducibility checklist appears after the references.

Inference:

- The AAAI source now uses the official AAAI-27 Author Kit files and compiles
  under a Docker image that includes the additional `newtxtext` dependencies
  required by `aaai2027.sty`.
- The current source is target-year build-ready, but not final upload-ready:
  the working source is split across `main.tex` and `sec/*.tex`, while the
  AAAI-27 author-kit instructions say final source upload should be a single
  `.tex` source plus bibliography/used graphics. A flattening/package step is
  still required before source upload if AAAI/OpenReview enforces that.
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
- Wide floats are delayed to pages 5-7, but they stay before references and are
  readable. This is acceptable for the current draft; final submission polish
  can still revisit float flow if needed.

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
4. If submitting source, flatten the working split source into a single
   `.tex` file plus `.bib` and used graphics, and exclude unused historical
   `aaai2026.*` files from the submission archive.

## AAAI-27 Submission Hygiene Check

Facts:

- Official page checked: `https://aaai.org/conference/aaai/aaai-27/main-technical-track-call/`.
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
  `7dd3b350f44292ec9c76c6ec68fe8ddf09fd835d43a10eaf2b8a24732c138d17`.

Checklist status:

- The checklist now follows the AAAI-27 Author Kit question structure.
- Current answers are intentionally conservative: several code/artifact items
  remain `partial` until the final anonymous review package and post-acceptance
  release URL/DOI/license are fixed.
- No answer should be upgraded from `partial` to `yes` until the corresponding
  final package file or manifest exists.

Supplement / appendix / ethics / review-instruction status:

- No separate supplementary PDF/ZIP is currently finalized.
- If a supplement is added, it should be treated as reviewer assistance only;
  main claims, caveats, and essential evidence must stay in the 7-page main
  paper.
- The current work uses existing public research datasets and does not
  introduce human-subject data or a new dataset, but the final submission still
  needs an ethics/responsible-research pass for dataset license/access terms,
  AI-assisted writing/tool-use disclosure if required, and anonymization.
- AAAI-27 expects qualified authors to be available for light reviewing; this
  is a submission-process obligation, not a manuscript content item.
