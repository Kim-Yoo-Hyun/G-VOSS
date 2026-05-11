# Open3DSG Metric/Join Contract

Status: `blocked_runtime_inputs_missing`
Created at: `2026-05-09T15:11:11+00:00`

## Fact

- The Open3DSG metric runner contract is frozen before Open3DSG runtime metrics exist.
- This command does not train Open3DSG, inspect predictions, compute metrics, or assign failure labels.
- It writes blocked outputs when required runtime inputs are missing.

## Runtime Inputs

- `predictions_jsonl`: status `missing_required`, rows `None`, path `experiments/H001_geom_reliability/sources/open3dsg/adapter/predictions.jsonl`
- `ground_truth_jsonl`: status `present`, rows `7505`, path `hypothesis/CAND-001/H001_geometry-grounded-verification/artifacts/evaluation/vlsat_closed_set/hardened/ground_truth.jsonl`
- `geometry_jsonl`: status `missing_required`, rows `None`, path `experiments/H001_geom_reliability/sources/open3dsg/geometry/verification.jsonl`
- `calibration_model_json`: status `present`, rows `199`, path `hypothesis/CAND-001/H001_geometry-grounded-verification/artifacts/calibration/p_geom_valid_smoke/model.json`
- `family_calibration_model_json`: status `present`, rows `744`, path `hypothesis/CAND-001/H001_geometry-grounded-verification/artifacts/calibration/p_geom_valid_family/model.json`

## Blocked

- `predictions_jsonl:missing_required:experiments/H001_geom_reliability/sources/open3dsg/adapter/predictions.jsonl`
- `geometry_jsonl:missing_required:experiments/H001_geom_reliability/sources/open3dsg/geometry/verification.jsonl`

## Output Contract

- `metrics.json` must expose semantic-only, probabilistic rerank, rule-verified, and family-specific control conditions when real inputs exist.
- Table 6 must remain blocked until `metrics.json` status is `ready`.

## Claim Boundary

This is a contract/blocked-input artifact only. It is not Open3DSG metric evidence until reproduced checkpoint predictions, geometry join, and metric calculations exist.
