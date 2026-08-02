# TODO

Last updated: 2026-08-01 KST.

This file is the current task board. Detailed commands and artifact recovery
belong in docs/reproducibility.md; exact result paths belong in the RelCompat3D
experiment README and result manifest.

## Now

- [ ] Complete the required generative-AI role disclosure in the manuscript or
  other venue-designated location according to the actual use.
- [ ] Review the large deletion set and create a clean submission commit.
- [ ] Verify the final author list, order, affiliations, conflicts, topics,
  title, abstract, and TL;DR in the submission system.

## Next

- [ ] Publish from a fresh repository or clean-history branch so archived and
  deleted large files are not exposed through prior Git history.
- [ ] Verify all public paths, anonymous metadata, licenses, and README commands
  from a clean checkout with the required external artifact bundle.
- [ ] Upload the Technical Supplement and updated reproducibility checklist,
  then reopen both files in the submission system. Do not upload Media or Code
  and Data Supplements during review.

## Recently Completed

- [x] Added compact section guides to the Technical Supplement. Section B now
  previews the evaluation scope, source predictions, verifier, and implementation,
  while Section C maps predicate, ordered-pair, and source-score controls to
  (T), (G), and (Z). The canonical build remains 9 US-Letter pages.
- [x] Centered the Table S14 Recall and Violation columns, applied the final
  Supplement sentence-length and terminology edits, and rebuilt the canonical
  9-page US-Letter Technical Supplement without overfull, undefined-reference,
  or graphics-inclusion warnings.
- [x] Added metric-wise bold emphasis to directly comparable Technical
  Supplement results, including all tied best values. Simplified uncommon and
  internal wording, aligned relation-family terminology with the main paper,
  retained only protocol-critical numerical details, and rebuilt the
  canonical 9-page US-Letter PDF without overfull, undefined-reference, or
  graphics-inclusion warnings.
- [x] Replaced Supplementary Figure S1 with
  `paper/aaai/supplement_figures/Figure4.pdf` and fixed the requested full-width
  layout: page 6 contains Table S9, Figure S1, and Table S10, while page 7
  contains Tables S11--S13. Existing audit, qualitative, and score-mapping
  prose now fills the former page-5 gap, and Table S14 moves onto page 8 to
  remove stretched paragraph spacing. The resulting 9-page US-Letter PDF has
  embedded fonts and no overfull, undefined-reference, or graphics-inclusion
  warning.
- [x] Replaced the repeated proximity example in Supplementary Figure S1 with
  the exact-label `desk close by chair` promotion. Its pair-local XY panel uses
  the recorded 0.436 m center distance without synthesizing point samples;
  the other panels retain their preserved elevation projections.
- [x] Moved all active and diagnostic RelCompat3D fitted-model JSON files out
  of Git tracking, archived eight canonical-path model files in the private
  Drive bundle, and added fresh-server restore, checksum, table-regeneration,
  output-location, and source-checkpoint instructions to the root README.
- [x] Removed public access from the full Drive recovery folder and retained
  a public link only for the fitted RelCompat3D model archive. Dataset-derived
  training and evaluation rows now require owner authorization.
- [x] Verified a fresh-checkout paper-level rerun in Docker. Tables 1--3 and
  Figure 3 reproduced all 291 canonical cells with maximum absolute error
  zero, and the Figure 2 XY renderer ran without the local archive.
- [x] Created and uploaded the private
  `RelCompat3D_AAAI27_release_20260730` recovery bundle to Google Drive. The
  bundle contains 21 files (100,760,138 bytes), and the final `rclone check`
  reported zero differences. Source-predictor checkpoints and the full Tier-B
  rows were deliberately not duplicated.
- [x] Clarified the two Table S7 transformation diagnostics, shortened the
  Table S8 removal labels, identified Table S14 intervals as paired bootstrap
  confidence intervals, and removed result prose that duplicated table cells.
- [x] Added the frozen primary-verifier specification to the Technical
  Supplement, separating evaluation status rules from counterfactual training
  construction; the current PDF retains all 16 tables.
- [x] Reorganized the Technical Supplement into A--C sections with A/A.1 and
  S-table/S-figure/equation numbering, retained 16 claim-supporting tables,
  and removed the post-acceptance release promise from the reviewer-facing PDF.
- [x] Finalized the review-time upload boundary around the Technical
  Supplement, removed dependencies on an attached code/data archive, and
  rebuilt the supplement and 2-page checklist without rebuilding the
  frozen main paper.
- [x] Reconstructed a label-free Figure 2 XY panel from the preserved
  qualitative case record and endpoint samples, with an exact \(4.329475\) m
  distance check and SVG, PDF, outlined-PDF, and PNG outputs under
  `paper/generated/`.
- [x] Merged the appendix/supplement, review/risk, and outline/preview document
  pairs into `paper/supplement.md`, `paper/review.md`, and
  `paper/outline.md`; removed the redundant progress document.
- [x] Removed legacy teaser/debug/build directories, unused paper renderers,
  the unused shared preamble, and `paper/generated/figures`; retained only the
  active main entry point and canonical PDFs.
- [x] Inlined the supplement preamble, synchronized supplement terminology and
  predictor-dependent control interpretation with the main paper, and rebuilt
  the 9/12/2-page canonical PDFs.
- [x] Generated and verified the synchronized release at
  `release/relcompat3d_aaai27_openreview_20260729_223000/`. The outer and inner
  manifests, 208-file ZIP, Compose config, Python compilation, extracted-source
  builds, page sizes, fonts, anonymity, and LaTeX warning checks pass.
- [x] Switched the submission path to `paper/aaai/main.tex`, restored the
  official anonymous-author block, removed unused template packages, and
  resolved the first-page vertical overfull without changing margins or fonts.
- [x] Removed manual-bold supplementary captions and 7-point interval text,
  clarified the combined train/development row counts, and clean-built the
  9/12/2-page main, supplement, and checklist.
- [x] Corrected the supplement optimizer contract and score-mapping notation,
  added body references for every supplementary table, and fixed the Open3DSG
  bibliography title.
- [x] Clean-built the main, supplement, and checklist from the pinned Docker
  image, refreshed all canonical PDFs, and independently rebuilt the LaTeX
  sources extracted from the code/data ZIP.
- [x] Exported a pseudonymized 601,140-candidate row bundle from hash-locked
  licensed inputs and reproduced all 291 canonical cells in Tables 1--3 and
  Figure 3 data with maximum absolute error zero.
- [x] Completed candidate-pool coverage and active-route, family-slot, and
  unconstrained Recall oracles for all three predictors and five K values.
  Public redistribution of the derived rows remains gated on confirmation of
  the 3RScan/3DSSG terms.
- [x] Completed matched Linear/MLP component diagnostics for pairwise-loss
  removal and transformation-averaging removal, including linked-pair margin
  distributions and transformed-view top-K membership checks.
- [x] Completed five predeclared fitting executions. Linear is exactly
  repeatable; MLP has one bounded VL-SAT K=50 Recall trade-off and the active
  seed was not reselected.
- [x] Completed the hash-locked Docker P0-3 routing-constraint controls on the
  canonical candidate pool. The matched route keeps support/contact fixed and
  shows estimator- and K-dependent effects when proximity and vertical-order
  candidates share a queue.
- [x] Completed the Docker P0-4 construct-dependence package, including an
  explicit dependency matrix and verified links to feature-removal,
  uncertainty-policy, component-removal, and Linear/MLP point-mesh audits.
- [x] Completed the hash-locked Docker P0-1 source-score mapping sensitivity
  and P0-2 closest-simple-baseline analysis on the canonical candidate pool,
  with all validations and exact canonical rerun checks passing.
- [x] Removed all superseded local release bundles and retained only the
  current synchronized release.
- [x] Regenerated a synchronized anonymous candidate release and lean
  code-and-compact-data ZIP from the current main, supplement, checklist,
  figures, method locks, source, and compact result summaries.
- [x] Resolved the prior 4.43-pt Table 2 horizontal overflow.
- [x] Synchronized the selected title across the main, supplement, checklist
  documentation, and release metadata.
- [x] Rebuilt the main, supplement, and reproducibility checklist from the
  current source in the pinned Docker image.
- [x] Synchronized `user_v6.tex` into the seven active AAAI section files,
  activated the supplied Figure 1--3 assets with outlined figure text, and
  rebuilt the selected nine-page main PDF in Docker.
- [x] Completed the Docker-based direct component-removal evaluation for the
  linked pairwise loss and transformation averaging, with all input, routing,
  reference-match, and transformation-consistency validations passing.
- [x] Migrated the active Python namespace from the retired project namespace
  to `src/relcompat3d/` and updated public documentation, Docker paths,
  manifests, and checksums.
- [x] Renamed the active `src/relcompat3d/` modules to concise role-based names,
  updated every public reference and checksum, and verified all 31 Docker CLI
  entry points.
- [x] Added a numbered 30-item manuscript revision checklist to
  `paper/user_feedback.md` while retaining the detailed reviewer rationale.
- [x] Standardized the active repository identifier and paths on
  `RelCompat3D`/`relcompat3d`, then refreshed dependent checksum locks and
  validated the renamed public tree.
- [x] Selected paper/aaai/main_aaai27.pdf as the main manuscript
  artifact.
- [x] Consolidated the manuscript section sources and current paper planning
  documents.
- [x] Promoted the no-family-indicator Linear model and matched MLP estimator,
  then regenerated compact main, control, scan-level interval, runtime,
  point/mesh, and transfer evidence.
- [x] Reduced experiments/RelCompat3D_geom_reliability to frozen protocols,
  locks, and compact paper/supplement outputs.
- [x] Reduced scripts/ and results/ to the active wrapper and compact result
  index.
- [x] Reduced src/relcompat3d to the verified release allowlist, the current
  point/mesh audit entry point, its transitive calibration dependency, and
  README files.
- [x] Retained only the focused RelCompat3D Docker configuration in the public
  config tree.
- [x] Moved H002, literature, hypothesis, historical code/config/results,
  superseded experiment outputs, and prior archive contents to the ignored
  local archive/local/pre_submission_20260722/ snapshot.
- [x] Verified 1,776 moved tracked source/config/experiment/result/script/
  literature/hypothesis/archive files against their local archive copies;
  intentionally removed logs and the pre-existing paper deletion are excluded.
- [x] Verified the active method hashes, Docker Compose configuration, Docker
  image build, and all 31 Python entry-point import smoke tests.
- [x] Retained all seven `docs/` workflow/runbook files and updated their
  RelCompat3D submission and local-archive boundaries.
