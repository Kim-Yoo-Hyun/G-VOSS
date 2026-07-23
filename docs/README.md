# Documentation

`docs/` contains the repository-wide workflow rules and the RelCompat3D recovery
runbook. All existing documents are retained in the submission snapshot; this
folder is not used as a live progress log.

## Documents

- `index.md`: navigation and file ownership.
- `reproducibility.md`: RelCompat3D data, artifact, Docker, recovery, and cleanup
  runbook.
- `paper.md`: paper framing, claim boundaries, and reviewer-defense rules.
- `experiments.md`: Docker experiment and result-promotion rules.
- `literature.md`: literature-review workflow retained for future use.
- `hypothesis.md`: hypothesis workflow retained for future use.

## Submission Snapshot

The public snapshot is centered on RelCompat3D/RelCompat3D. The former literature,
hypothesis, H002, superseded experiment, and historical release payloads are
preserved locally under
`archive/local/pre_submission_20260722/` and are excluded from Git. Their
workflow documents remain here so that the research process can be restored
without making those payloads part of the submission repository.

Current status belongs in `TODO.md` and `summary.md`; compact evidence belongs
in `results/` and `experiments/RelCompat3D_geom_reliability/`; exact recovery details
belong in `docs/reproducibility.md`.
