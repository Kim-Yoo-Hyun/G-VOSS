# Attachment Deferred Scope Audit

Status: `attachment_deferred_scope_schema_ready_no_metric_execution`
Created at: `2026-05-27T16:05:10.781220+00:00`

## Claim Boundary

This audit does not change the current H001 paper claim. `attachment_deferred` is a future upgrade path and remains outside paper metrics until its attachment-specific evidence extractor, verifier, calibration, controls, GT evaluation, source metrics, bootstrap CI, and audit gates pass.

## Denominator

| Item | Count |
| --- | --- |
| current H001 GT denominator | 2545 |
| attachment_deferred GT rows | 967 |
| expanded candidate denominator | 3512 |
| all held-out GT rows | 7505 |
| expanded denominator share | 0.468 |

## Attachment GT Labels

| Label | GT rows |
| --- | --- |
| attached to | 808 |
| hanging on | 126 |
| connected to | 33 |

## Source Prediction Rows

| Source | attachment_deferred rows |
| --- | --- |
| VL-SAT | 77748 |
| Open3DSG | 57300 |

## Existing Verification Status

The current geometry join intentionally treats `attachment_deferred` as out of scope.

| Source | Status | Rows |
| --- | --- | --- |
| vlsat | unsupported | 77748 |
| open3dsg | unsupported | 57300 |

## Evidence Schema Decision

- Reuse OBB distance/overlap and segmented point evidence where available.
- Add attachment-specific surface/contact/normal/gravity fields before any verifier.
- Treat object affordance as optional context, not as a proof of physical validity.
- Preserve exact predicate-label recall for `attached to`, `hanging on`, and `connected to`.

## Next Gate

`G1_attachment_evidence_extractor_design`

## Blockers

- `attachment_evidence_extractor_not_implemented`
- `surface_type_and_normal_estimation_not_validated`
- `local_point_contact_policy_not_frozen`
- `attachment_verifier_not_implemented`
- `train_dev_calibration_not_built`
- `gt_counterfactual_verifier_eval_not_run`
- `source_metrics_not_run`
- `bootstrap_ci_not_run`
- `failure_analysis_and_visual_audit_not_run`
- `function_reasoning_pilot_blocked_until_relation_metrics_pass`
