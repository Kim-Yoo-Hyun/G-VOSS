# AAAI PDF Visual/Layout Inspection

Last updated: 2026-06-06 KST

## Build Checked

- PDF: `paper/aaai/main.pdf`
- Image build log: `logs/h001_aaai_tex_image_build_full_validation_20260605_100108.log`
- PDF build log: `logs/h001_aaai_pdf_build_compression_20260606_105126.log`
- Preview files generated locally: `/tmp/h001_aaai_pages/page-4.png` through
  `/tmp/h001_aaai_pages/page-7.png` for the latest focused check
- Page count: 9 total pages, US Letter
- Technical content: pages 1-7
- References: page 8
- Reproducibility checklist: page 9
- Build status: no missing citations, no undefined references, no overfull
  hboxes, no LaTeX errors, and no AAAI package errors in the latest build log

The PNG preview files are generated inspection artifacts and are ignored by
`paper/aaai/.gitignore`. This report is the tracked inspection record.

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

- The AAAI source now respects the high-level AAAI-26 structure of up to 7
  technical pages plus additional reference/checklist pages.
- The current AAAI-26 source now uses the official AAAI-26 Author Kit style
  files. It is still not final submission-ready because a future target-year
  AAAI kit must be rechecked if the submission year changes, and checklist
  answers should be revisited after the final artifact/code-release package is
  fixed.
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
- blocking visual issue: none

Required before submission:

1. Re-check the exact target-year official AAAI author kit if the submission
   target changes beyond AAAI-26.
2. Re-check checklist answers after final artifact/code-release packaging,
   especially `partial/no` items.
3. Re-check supplementary/appendix and ethics/review instructions from the
   official AAAI target-year page.
