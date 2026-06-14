# Relative Horizontal Coordinate Audit

Status: `relative_horizontal_coordinate_audit_blocked_no_metric_execution`
Created at: `2026-05-27T12:28:46.096711+00:00`

## Claim Boundary

This is a coordinate-frame semantics gate for the optional `relative_horizontal` expansion track. It is not source-prediction metric evidence and does not change the current H001 paper claim.

## Selected Candidate Frame

| Field | Value |
| --- | --- |
| frame | scan_left_neg_x_front_neg_y |
| family | scan_xy |
| macro strict purity | 0.7725 |
| strict eligible share | 0.6403 |
| macro sign-only purity | 0.7626 |
| wrong-frame gap | 0.1231 |

## Per-Label Strict Purity

| Label | Purity | Eligible | Uncertain | Contradiction |
| --- | --- | --- | --- | --- |
| left | 0.8005 | 732 | 400 | 146 |
| right | 0.8005 | 732 | 400 | 146 |
| front | 0.7445 | 411 | 242 | 105 |
| behind | 0.7445 | 411 | 242 | 105 |

## Inverse-Pair Consistency

| Item | Value |
| --- | --- |
| rows with reverse annotation | 3570 |
| rows with expected inverse | 3570 |
| inverse consistency | 1.0 |

## Gate Decision

| Check | Passed |
| --- | --- |
| macro_strict_purity_ge_0_80 | false |
| per_label_strict_purity_ge_0_75 | false |
| strict_eligible_share_ge_0_50 | true |
| inverse_consistency_ge_0_85_when_available | true |
| wrong_frame_gap_ge_0_05 | true |
| geometry_inputs_complete | true |

## Blockers

- `macro_strict_purity_ge_0_80`
- `per_label_strict_purity_ge_0_75`
- `relative_horizontal_verifier_policy_not_frozen`
- `train_dev_calibration_not_built`
- `source_metrics_not_run`
- `bootstrap_ci_not_run`
- `failure_analysis_and_visual_audit_not_run`

## Top Frame Candidates

| Rank | Frame | Family | Macro strict | Eligible share | Macro sign-only |
| --- | --- | --- | --- | --- | --- |
| 1 | scan_left_neg_x_front_neg_y | scan_xy | 0.7725 | 0.6403 | 0.7626 |
| 2 | room_pca_left_pos_p0_front_pos_p1 | room_pca | 0.6494 | 0.5832 | 0.6298 |
| 3 | room_pca_left_pos_p1_front_neg_p0 | room_pca | 0.5818 | 0.5591 | 0.5812 |
| 4 | scan_left_pos_y_front_pos_x | scan_xy | 0.5602 | 0.623 | 0.5699 |
| 5 | room_pca_left_pos_p0_front_neg_p1 | room_pca | 0.5513 | 0.5832 | 0.5543 |
| 6 | scan_left_neg_x_front_pos_y | scan_xy | 0.528 | 0.6403 | 0.5135 |
| 7 | room_pca_left_pos_p1_front_pos_p0 | room_pca | 0.5243 | 0.5591 | 0.5119 |
| 8 | scan_left_pos_y_front_neg_x | scan_xy | 0.511 | 0.623 | 0.5059 |

## Interpretation

- The coordinate-frame gate does not yet support promoting `relative_horizontal` into the main claim.
- A failed or partial gate is useful: it prevents a broader claim from being built on coordinate convention artifacts.
