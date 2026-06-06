# Relative Lateral Policy Freeze

Status: `relative_lateral_policy_threshold_provenance_frozen_no_source_metrics`
Created at: `2026-06-06T07:32:42.266930+00:00`

## Claim Boundary

This artifact splits `left/right` into `relative_lateral` and defers
`front/behind` as `relative_depth_deferred`. It freezes denominator,
geometry policy, and threshold provenance only. It is not source metric
evidence and does not change the AAAI main claim.

## Family Split

| Family | Labels | GT rows | Status |
|---|---|---:|---|
| `relative_lateral` | `left`, `right` | 2264 | frozen candidate |
| `relative_depth_deferred` | `front`, `behind` | 1306 | deferred |

## Lateral Coordinate Evidence

| Item | Value |
|---|---:|
| selected frame | `scan_left_neg_x_front_neg_y` |
| strict purity | 0.8005 |
| strict eligible share | 0.6466 |
| strict match/contradiction | 1172 / 292 |
| sign-only purity | 0.7761 |
| distinct-left-axis wrong-frame gap | 0.0998 |

## Deferred Depth Evidence

| Item | Value |
|---|---:|
| strict purity | 0.7445 |
| strict eligible share | 0.6294 |
| strict match/contradiction | 612 / 210 |

## Train/Dev Provenance

- train/dev source: `/workspace/local_dataset/3DSSG_subset/relationships_train.json`
- train lateral rows: `1538`
- dev lateral rows: `378`
- train depth-deferred rows: `874`
- dev depth-deferred rows: `224`

## Promotion Limits

- `train_dev_policy_lock_or_calibration_fit_not_run`
- `relative_lateral_source_metrics_not_run`
- `controls_not_run`
- `bootstrap_ci_not_run`
- `failure_analysis_and_visual_audit_not_run`
- `main_claim_requires_explicit_user_confirmation`
