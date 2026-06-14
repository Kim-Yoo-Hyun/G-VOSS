# Relative Horizontal Scope Audit

Status: `relative_horizontal_scope_audit_ready_no_metric_execution`
Created at: `2026-05-27T12:12:08.992072+00:00`

## Claim Boundary

This audit does not change the current H001 paper claim. `relative_horizontal` remains a separate expansion track until it passes coordinate-frame validation, verifier design, calibration, metrics, controls, bootstrap CI, and failure/audit gates.

## Denominator

| Item | Count |
| --- | --- |
| current H001 GT denominator | 2545 |
| relative_horizontal GT rows | 3570 |
| expanded candidate denominator | 6115 |
| all held-out GT rows | 7505 |
| expanded denominator share | 0.8148 |

## Relative-Horizontal GT Labels

| Label | GT rows |
| --- | --- |
| left | 1132 |
| right | 1132 |
| front | 653 |
| behind | 653 |

## Source Prediction Rows

| Source | relative_horizontal rows |
| --- | --- |
| VL-SAT | 103664 |
| Open3DSG | 76400 |

## Existing Verification Status

The current geometry join intentionally treats `relative_horizontal` as out of scope.

| Source | Status | Rows |
| --- | --- | --- |
| vlsat | unsupported | 103664 |
| open3dsg | unsupported | 76400 |

## Required First Gate

- Freeze coordinate-frame semantics for `left/right/front/behind`.
- Add a wrong-frame or axis-flip control before metric promotion.
- Keep exact predicate-label recall; family grouping must not collapse labels.
- Keep the current main paper claim unchanged until all promotion gates pass.

## Blockers

- `coordinate_frame_semantics_unverified`
- `relative_horizontal_verifier_not_implemented`
- `train_dev_calibration_not_built`
- `gt_counterfactual_verifier_eval_not_run`
- `source_metrics_not_run`
- `bootstrap_ci_not_run`
- `failure_analysis_and_visual_audit_not_run`
