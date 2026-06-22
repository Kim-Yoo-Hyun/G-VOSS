# H001_v2 Source Inventory

Last updated: 2026-06-22 KST

This file freezes the read-only H001 artifact inventory for the first
H001_v2 implementation pass. H001_v2 may inspect these paths, derive copied
intermediate files under its own `artifacts/` root, and write reports under
this branch. It must not modify the files listed here.

## Calibration Source

Primary calibration artifact:

`archive/hypothesis_records/hypothesis/CAND-001/H001_geometry-grounded-verification/artifacts/calibration/train_dev_calib/`

| File | Status | Role |
| --- | --- | --- |
| `manifest.json` | ready | Calibration manifest and provenance. |
| `table.jsonl` | 5,809 rows | Train/dev positive and counterfactual calibration rows. |
| `negatives.jsonl` | 3,244 rows | Counterfactual negatives used by calibration export. |
| `report.md` | ready | Human-readable calibration report. |

Manifest summary:

- `status`: `ready`
- `split_name`: `train_dev_calib`
- `row_schema_version`: `h001_calibration_row_v1`
- rows: 2,565 positive + 3,244 counterfactual negative = 5,809
- families: `support_contact` 2,845, `proximity` 2,114, `relative_vertical` 850
- scans/subgraphs: 32 scans / 225 subgraphs
- validation: passed, with one recorded invalid-OBB warning

Use in H001_v2:

- Fit or select the risk-control policy only from this calibration source or a
  documented derivative made under the H001_v2 artifact root.
- Do not select `alpha`, `delta`, `tau_grid`, family scope, or final `tau*`
  from full-validation source metrics.

Open issue for implementation:

- `table.jsonl` contains calibration labels and geometry fields, but not the
  source prediction ranking distribution used at full validation. The first
  dry run should therefore verify whether the calibration rows contain enough
  `p_geom_valid` / violation target information for threshold selection. If
  not, create a branch-local calibration join plan before any source metrics.

## VL-SAT Full Validation Source

Primary source root:

`experiments/H001_geom_reliability/sources/vlsat/full_validation/`

| File | Status | Role |
| --- | --- | --- |
| `adapter/predictions.jsonl` | 957,008 rows | Source predictions and semantic/rank fields. |
| `adapter/ground_truth.jsonl` | 11,254 rows | Source-aligned ground truth rows. |
| `adapter/manifest.json` | ready | Adapter provenance. |
| `geometry/verification.jsonl` | 957,008 rows | Prediction-aligned geometry verification and calibrated scores. |
| `geometry/manifest.json` | ready | Geometry provenance. |
| `metrics/metrics.json` | ready | Existing H001 source metrics for comparison only. |
| `metrics/report.md` | ready | Existing metric report for comparison only. |
| `bootstrap_ci/summary.json` | ready | Existing H001 bootstrap summary for comparison only. |
| `failure_rows/rows.jsonl` | ready | Existing H001 failure rows for later qualitative checks. |

Observed schema fields:

- `adapter/predictions.jsonl`: `scan_id`, `subgraph_id`, `prediction_id`,
  `edge`, `predicate`, `scores`, `ranks`, `baseline_name`, `split_name`
- `geometry/verification.jsonl`: prediction identity fields plus `semantic`,
  `geometry`, `verification`, `verification_status`, `verification_variants`,
  `calibration`, and `consistency_score`

Use in H001_v2:

- Evaluate only after `tau*` is selected from allowed calibration artifacts.
- Existing `metrics/` and `bootstrap_ci/` are comparison baselines, not tuning
  inputs.
- H001_v2 outputs must go under this branch's artifact root or a future
  explicitly named H001_v2 experiment root, not under this H001 source root.

## Open3DSG Full Validation Source

Primary source root:

`experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2/`

| File | Status | Role |
| --- | --- | --- |
| `adapter/predictions.jsonl` | 695,916 rows | Source predictions and semantic/rank fields. |
| `adapter/manifest.json` | ready | Adapter provenance. |
| `geometry/verification.jsonl` | 695,916 rows | Prediction-aligned geometry verification and calibrated scores. |
| `geometry/manifest.json` | ready | Geometry provenance. |
| `metrics/metrics.json` | ready | Existing H001 source metrics for comparison only. |
| `metrics/report.md` | ready | Existing metric report for comparison only. |
| `bootstrap_ci/summary.json` | ready | Existing H001 bootstrap summary for comparison only. |
| `failure_rows/rows.jsonl` | ready | Existing H001 failure rows for later qualitative checks. |
| `table_caveats/report.md` | ready | Existing Open3DSG caveat/provenance wording. |

Observed schema fields:

- `adapter/predictions.jsonl`: `scan_id`, `subgraph_id`, `prediction_id`,
  `edge`, `predicate`, `scores`, `ranks`, `baseline_name`, `split_name`
- `geometry/verification.jsonl`: prediction identity fields plus `semantic`,
  `geometry`, `verification`, `verification_status`, `verification_variants`,
  `calibration`, and `consistency_score`

Use in H001_v2:

- Treat this as the open-vocabulary source case study inherited from H001.
- Do not tune a separate Open3DSG-only threshold from this source unless it is
  explicitly declared as diagnostic and Bonferroni-controlled in the protocol.
- Preserve existing recovery/caveat wording if H001_v2 is later reported.

## Derived Output Root

The default H001_v2 output root is:

`hypothesis/CAND-001/H001_v2_risk_controlled_reranking/artifacts/`

Required first derived outputs:

- `calibration_threshold_selection/manifest.json`
- `calibration_threshold_selection/report.md`
- `calibration_threshold_selection/thresholds.json`
- `calibration_threshold_selection/selection_curve.jsonl`

Source evaluation outputs are blocked until threshold selection succeeds:

- `source_eval/vlsat_full_validation/`
- `source_eval/open3dsg_recovery_relaxed_views_min2/`

## No-Overwrite Guard

Any implementation script for H001_v2 must fail before writing if the requested
output path is under one of these read-only roots:

- `experiments/H001_geom_reliability/sources/vlsat/full_validation/`
- `experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2/`
- `archive/hypothesis_records/hypothesis/CAND-001/H001_geometry-grounded-verification/`

The script should also refuse to overwrite an existing H001_v2 output directory
unless an explicit `--overwrite` flag is provided.
