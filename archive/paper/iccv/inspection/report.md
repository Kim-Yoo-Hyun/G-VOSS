# ICCV PDF Visual/Layout Inspection

Last updated: 2026-05-26 KST

## Build Checked

- PDF: `paper/iccv/main.pdf`
- Build log: `logs/h001_iccv_pdf_build_20260526_013847.log`
- Preview files generated locally: `page-1.png` through `page-9.png`,
  plus `contact_sheet.png`
- Page count: 9 ICCV review-style pages, letter size
- Build status: no missing citations, no undefined references, and no overfull
  hbox warnings in the latest build log

The PNG preview files are generated inspection artifacts and are ignored by
`paper/iccv/.gitignore`. This report is the tracked inspection record.

## Page-Level Findings

Facts:

- Page 1: title, abstract, and introduction are readable.
- Page 2: related work layout is readable.
- Page 3: problem formulation and method layout are readable.
- Page 4: method closes, Experimental Setup starts, and Results begins.
- Page 5: fixed-scope and source-boundary tables are readable. Result prose
  begins and states the Open3DSG-first interpretation before the main source
  table appears.
- Page 6: Figure 1 and Figure 2 are readable.
- Page 7: Table 3 is the main source-results table, with Open3DSG rows first
  and VL-SAT rows second. Figure 3 appears below it and is readable.
- Page 8: Conclusion fits on the page; References start in the lower left
  column and continue through the right column.
- Page 9: References continue.

Inference:

- The PDF is acceptable as an internal ICCV-style draft and is no longer blocked
  by build or obvious layout failures.
- It is not yet a final camera-ready layout, but the main table-order issue was
  reduced. Open3DSG is no longer a late standalone table; it is the first block
  in manuscript Table 3, while VL-SAT is the controlled anchor block.
- `Table 6` remains the experiment artifact name for the generated Open3DSG
  hook/status output. The current ICCV manuscript uses Table 3 for the combined
  Open3DSG-first source-results table.

## Verdict

Visual/layout inspection passed for draft continuation:

- build clean: yes
- page count known: 9
- body and Conclusion fit before the bibliography: yes
- bibliography starts: page 8
- bibliography continues: page 9
- blocking visual issue: none

Recommended next polish, if continuing paper layout work:

1. Keep Open3DSG caveats explicit in Table 3 during any future compression.
2. Treat controls, GT verifier, audit, and visual sanity checks as prose
   evidence unless an appendix is added.
3. Optional final Figure 3 polish can still be done only through a deterministic
   render path for the same locked case IDs.
