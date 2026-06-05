# Prediction Export

Created at: `2026-06-04`
Baseline: `vlsat_closed_set`
Split: `full_official_validation`
Status: `ready`

## Inputs

- Subset file: `local_dataset/3DSSG_subset/relationships_validation.json`
- Raw dump file: `experiments/H001_geom_reliability/sources/vlsat/full_validation/raw/raw.jsonl`
- Selected scans file: `experiments/H001_geom_reliability/full_validation_transition/scope_contract/scans.txt`

## Outputs

- Predictions: `predictions.jsonl`
- Ground truth: `ground_truth.jsonl`
- Manifest: `manifest.json`

## Counts

- Subgraphs: `548`
- Directed pairs: `36808`
- Predictions: `957008`
- Ground-truth edges: `11254`

## Validation

- Passed: `True`
- Errors: `0`
- Warnings: `0`

## Interpretation

This adapter preserves semantic prediction scores and H001 join identity only.
It does not fit `p_geom_valid` and does not run final prediction-level evaluation.
