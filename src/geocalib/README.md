# GeoCalib Code

This folder contains direct Python entry points used by Docker compose.

## Current Claim Path

The current paper-facing claim uses the `support_contact`, `proximity`, and
`relative_vertical` families with VL-SAT and Open3DSG source rows. Core
entry points are:

- `build_tables.py`
- `bootstrap_metrics.py`
- `evaluate_predictions.py`
- `evaluate_gt_verifier.py`
- `export_predictions.py`
- `export_open3dsg_predictions.py`
- `join_predictions.py`
- `stage_vlsat.py`
- `prepare_vlsat_full_validation_runtime.py`
- `run_vlsat_dump.py`
- Open3DSG staging, adapter, metric-scope, raw-identity, failure-analysis, and
  caveat-report scripts.

Shared repository paths live in `paths.py`. Use those constants for durable
H001 roots instead of repeating `archive/hypothesis_records/...` literals.

## Extension Code

Qwen-VL, `attachment_deferred`, `relative_horizontal`, and `relative_lateral`
scripts are retained because they are runnable Docker entry points or preserved
extension/audit routes. They do not extend the current main claim unless the
paper claim boundary is explicitly promoted and the matching evidence gates are
rerun.

## Boundary

Do not put generated row-level outputs, caches, checkpoints, or source-specific
run artifacts here. Keep those under `experiments/`, `results/`, ignored local
roots, or `archive/` according to the repository runbooks.
