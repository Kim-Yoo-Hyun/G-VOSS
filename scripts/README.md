# Submission Scripts

The submission-facing script directory contains:

- `run_no_family_indicator_v1.sh`: runs the active RelCompat3D evaluation in
  `initial` or `downstream` phases, skips completed manifests, and refuses to
  overwrite nonempty incomplete outputs.
- `build_release_bundle.py`: packages fresh Docker-built main, supplement, and
  checklist PDFs with an anonymous allowlisted code-and-compact-data ZIP and
  SHA-256 manifests.

Core fitting, evaluation, audit, and figure logic remains in `src/relcompat3d/`;
Docker services and pinned environment definitions remain in `configs/relcompat3d/`.
Exact runs require the external row-level inputs documented in
`docs/reproducibility.md`.

Source-specific and superseded workflow wrappers were moved to the ignored
local snapshot under
`archive/local/pre_submission_20260722/previous_archive/scripts/`.
