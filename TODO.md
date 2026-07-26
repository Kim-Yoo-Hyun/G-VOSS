# TODO

Last updated: 2026-07-25 KST.

This file is the current task board. Detailed commands and artifact recovery
belong in docs/reproducibility.md; exact result paths belong in the RelCompat3D
experiment README and result manifest.

## Now

- [ ] Resolve the 36.78 pt first-page vertical overfull without changing
  margins, font size, or using negative vertical spacing.
- [ ] Complete the required generative-AI role disclosure in the manuscript or
  submission system according to the actual use.
- [ ] Promote a final upload bundle after the first-page layout fix.
- [ ] Review the large deletion set and create a clean submission commit.

## Next

- [ ] Publish from a fresh repository or clean-history branch so archived and
  deleted large files are not exposed through prior Git history.
- [ ] Verify all public paths, anonymous metadata, licenses, and README commands
  from a clean checkout with the required external artifact bundle.
- [ ] Run final font, page-size, page-count, citation, reference, figure, and
  checksum checks on the exact upload PDFs.

## Recently Completed

- [x] Removed all superseded local release bundles and retained only
  `release/relcompat3d_aaai27_openreview_20260726_214500/`.
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
- [x] Selected paper/aaai/main_teaser_aaai27.pdf as the main manuscript
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
