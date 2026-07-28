# TODO

Last updated: 2026-07-28 KST.

This file is the current task board. Detailed commands and artifact recovery
belong in docs/reproducibility.md; exact result paths belong in the RelCompat3D
experiment README and result manifest.

## Now

- [ ] Complete the required generative-AI role disclosure in the manuscript or
  other venue-designated location according to the actual use.
- [ ] Review the large deletion set and create a clean submission commit.

## Next

- [ ] Publish from a fresh repository or clean-history branch so archived and
  deleted large files are not exposed through prior Git history.
- [ ] Verify all public paths, anonymous metadata, licenses, and README commands
  from a clean checkout with the required external artifact bundle.
- [ ] Run final font, page-size, page-count, citation, reference, figure, and
  checksum checks on the exact upload PDFs.

## Recently Completed

- [x] Switched the submission path to `paper/aaai/main.tex`, restored the
  official anonymous-author block, removed unused template packages, and
  resolved the first-page vertical overfull without changing margins or fonts.
- [x] Removed manual-bold supplementary captions and 7-point interval text,
  clarified the combined train/development row counts, and clean-built the
  9/10/2-page main, supplement, and checklist.
- [x] Corrected the supplement optimizer contract and score-mapping notation,
  added body references for every supplementary table, and fixed the Open3DSG
  bibliography title.
- [x] Clean-built the main, supplement, and checklist from the pinned Docker
  image, refreshed all canonical PDFs, and independently rebuilt the LaTeX
  sources extracted from the code/data ZIP.
- [x] Regenerated and verified the synchronized release at
  `release/relcompat3d_aaai27_openreview_20260728_214915/`. The outer manifest,
  internal ZIP manifest, JSON, Python, Compose, anonymity, page-count, font, and
  filename checks pass. The bundle conservatively excludes stable source
  identifiers and source-derived row bundles.
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
