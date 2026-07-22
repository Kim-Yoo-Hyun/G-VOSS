# TODO

Last updated: 2026-07-22 KST.

This file is the current task board. Detailed commands and artifact recovery
belong in docs/reproducibility.md; exact result paths belong in the H001
experiment README and result manifest.

## Now

- [ ] Reduce the current main-teaser source build from ten pages to the
  submission limit without changing margins, font size, or using negative
  vertical spacing.
- [ ] Remove the remaining 4.43 pt overfull table row.
- [ ] Rebuild the selected manuscript, supplement, and reproducibility
  checklist in Docker.
- [ ] Regenerate and verify the anonymous release bundle after the layout fix.
- [ ] Review the large deletion set and create a clean submission commit.

## Next

- [ ] Publish from a fresh repository or clean-history branch so archived and
  deleted large files are not exposed through prior Git history.
- [ ] Verify all public paths, anonymous metadata, licenses, and README commands
  from a clean checkout with the required external artifact bundle.
- [ ] Run final font, page-size, page-count, citation, reference, figure, and
  checksum checks on the exact upload PDFs.

## Recently Completed

- [x] Selected paper/aaai/main_teaser_aaai27.pdf as the main manuscript
  artifact.
- [x] Consolidated the manuscript section sources and current paper planning
  documents.
- [x] Promoted the no-family-indicator Linear model and matched MLP estimator,
  then regenerated compact main, control, scan-level interval, runtime,
  point/mesh, and transfer evidence.
- [x] Reduced experiments/H001_geom_reliability to frozen protocols, locks, and
  compact paper/supplement outputs.
- [x] Reduced scripts/ and results/ to the active wrapper and compact result
  index.
- [x] Reduced src/geocalib to the verified release allowlist, the current
  point/mesh audit entry point, its transitive calibration dependency, and
  README files.
- [x] Retained only the focused H001 Docker configuration in the public config
  tree.
- [x] Moved H002, literature, hypothesis, historical code/config/results,
  superseded experiment outputs, and prior archive contents to the ignored
  local archive/local/pre_submission_20260722/ snapshot.
- [x] Verified 1,776 moved tracked source/config/experiment/result/script/
  literature/hypothesis/archive files against their local archive copies;
  intentionally removed logs and the pre-existing paper deletion are excluded.
- [x] Verified the active method hashes, Docker Compose configuration, Docker
  image build, and all 31 Python entry-point import smoke tests.
- [x] Retained all seven `docs/` workflow/runbook files and updated their H001
  submission and local-archive boundaries.
