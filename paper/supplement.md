# RelCompat3D Technical Supplement Guide

Last updated: 2026-08-01 KST

This document is the authoritative map for the Technical Supplement. The
active wrapper is `aaai/supplement.tex`, the content source is
`aaai/sec/supplement.tex`, and the canonical upload artifact is
`aaai/supplement_aaai27.pdf`.

The current clean build is 9 US-Letter pages and 567,090 bytes. Its SHA-256 is
`2f7ca7f7c7cadd2dff763b23c76a2d1d20a26033706ff990aacd1908cba121c5`.

## 1. Role and Claim Boundary

The supplement supports the main paper with method details, reproducibility
information, controls, sensitivities, and extended results. The main paper
remains self-contained, and reviewers are not required to read this document.

The supplement does not broaden the claim to dataset-level generalization,
independent ground truth for geometric validity, universal routing or fusion
optimality, support/contact correction, or generation of missing relation
candidates.

## 2. Current A--C Structure

### A. Supplementary Method Details

- notation;
- counterfactual construction and information use;
- all 17 ordered-pair measurements;
- Linear and MLP architecture, optimization, and parameter counts;
- transformation consistency, family-sequence preservation, and prefix
  utility properties.

### B. Reproducibility and Experimental Setup

- 1,061/117/157 train/development/evaluation scans;
- 548 contexts and 3,972 exact-match ground-truth relations;
- VL-SAT, Open3DSG, and SGFN preprocessing;
- observed source-score ranges;
- the primary-verifier measurements, status boundaries, and support/contact
  score;
- fixed software environment and separate predictor execution.

### C. Additional Results Supporting Main Claims

- the control mapping for the separated (T), (G), and (Z) factors;
- component and feature removals;
- point- and mesh-based audit for both estimators and all \(K\);
- qualitative proximity, vertical-order, and support/contact cases;
- source-score mappings, robust-density baseline, matched MLP controls, and
  routing constraints;
- paired scan-level intervals;
- \(K=100\) family composition;
- verifier-uncertainty sensitivity;
- five-seed and construction-parameter robustness.

The robustness and scope checks close Section C rather than forming a separate
low-priority section. They do not introduce additional main comparisons. The
previous exploratory ReplicaSSG/FROSS table, direct-verifier diagnostics, and
candidate-oracle results are not included in the review PDF. Compact scope
conclusions are retained only where they clarify the main claim boundary.

Sections A--C each begin with a compact scope sentence. The Section C opening
connects predicate, ordered-pair, and source-score controls to (T), (G),
and (Z) before presenting the detailed results.

## 3. Figure and Table Inventory

The PDF contains 16 tables and one figure.

| Evidence group | Contents | Priority |
| --- | --- | --- |
| Method specification | Notation, counterfactual rules, information-use boundary, 17 features | Essential |
| Evaluation specification | Primary-verifier measurements, thresholds, and nondecidable handling | Essential |
| Design evidence | Component removal, transformation diagnostics, feature removal | Essential |
| Main extensions | Full point/mesh audit, matched MLP controls, paired intervals | Essential |
| Baseline and routing | Score mappings, robust density, matched route | High |
| Scope and reporting | Family composition, uncertainty policies | High |
| Qualitative evidence | Proximity and vertical changes plus support/contact preservation | High |

The figure is illustrative rather than a systematic or independently
annotated validity audit.

## 4. Numbering and Navigation

- `\appendix` and `\setcounter{secnumdepth}{2}` produce A/A.1 numbering.
- Tables, figures, and equations use S1, S2, ... numbering to avoid confusion
  with the main paper.
- No table of contents is added because the AAAI style suppresses it and the
  opening overview already maps Sections A--C.
- Table S2 is a full-width table at the top of page 2, Table S3 is
  one-column, and the primary-verifier specification is Table S5.
- Page 6 contains Table S9, Figure S1, and Table S10. Page 7 is a table-only
  page containing Tables S11--S13. Their analysis begins on page 8, and Tables
  S14--S16 remain adjacent to their corresponding text.

## 5. Review and Release Boundary

Only `aaai/supplement_aaai27.pdf` is uploaded as the Technical Supplement.
No Media Supplement or Code and Data Supplement is uploaded during review.
The PDF contains no author-owned web link and no promise about the timing of
artifact release.

The planned public release of the RelCompat3D implementation and
machine-readable results is an internal post-acceptance task and a
post-publication reproducibility-checklist commitment. Licensed 3RScan/3DSSG
assets and third-party checkpoints will not be redistributed.

## 6. Writing and Formatting Contract

- Use the terminology of the main paper.
- Use `validation split` for the dataset partition and `validation scenes` for
  the evaluated scenes.
- Use `source relation score`, `ordered-pair measurements`, `family-aware
  re-ranking`, and `verifier-derived Violation`.
- Do not present compatibility as a calibrated probability.
- Explain the changed condition before each result and report only the pattern
  needed to support or bound the claim.
- Use roman captions without manually bolded lead phrases.
- Use at least 9-point table text.
- In performance tables, bold the preferred value within each predictor and
  matched comparison. Bold all ties and do not compare unrelated families or
  diagnostic quantities.

## 7. Final Verification

After each source change:

1. build `supplement.tex` in the pinned Docker image;
2. verify A--C and S-numbering in the rendered PDF;
3. check that every table and figure is referenced;
4. check undefined citations/references and overfull boxes;
5. verify US Letter, PDF 1.5, embedded non-Type-3 fonts, and anonymity;
6. verify that the PDF is below the 10 MB Technical Supplement limit;
7. update the canonical supplement PDF and its recorded hash.
