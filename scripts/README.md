# Submission Script

The submission-facing script directory contains one lightweight Docker wrapper:

- `run_no_family_indicator_v1.sh`: runs the active RelCompat3D evaluation in
  `initial` or `downstream` phases, skips completed manifests, and refuses to
  overwrite nonempty incomplete outputs.

Core fitting, evaluation, audit, and figure logic remains in `src/relcompat3d/`;
Docker services and pinned environment definitions remain in `configs/relcompat3d/`.
Exact runs require the external row-level inputs documented in
`docs/reproducibility.md`.

Source-specific and superseded workflow wrappers were moved to the ignored
local snapshot under
`archive/local/pre_submission_20260722/previous_archive/scripts/`.
