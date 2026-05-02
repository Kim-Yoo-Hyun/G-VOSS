# Point Support Evidence

Created at: `2026-04-30T03:09:48.545675+00:00`
Scan id: `f62fd5fd-9a3f-2f44-883a-1e5cf819608e`
Point rule version: `ply_points_v1`

## Validation

- Passed: `True`
- Errors: `0`
- Warnings: `2`

## Counts

- `support_contact_edges_total`: `32`
- `target_object_ids`: `34`
- `missing_point_object_ids`: `0`
- `point_evidence_available_count`: `32`
- `floor_support_edges`: `16`
- `floor_support_recovered_edges`: `13`
- `manual_labels_loaded`: `30`

## Point Status Counts

- `point_satisfied`: `19`
- `point_uncertain`: `1`
- `point_violated`: `12`

## Status Transitions

- `obb_uncertain_to_point_satisfied`: `10`
- `obb_uncertain_to_point_violated`: `3`
- `obb_violated_to_point_satisfied`: `9`
- `obb_violated_to_point_uncertain`: `1`
- `obb_violated_to_point_violated`: `9`

## Manual Label To Point Status

- `candidate_real_violation_or_geometry_mismatch`: point_satisfied=1
- `geometry_artifact_likely`: point_satisfied=5, point_violated=1
- `needs_point_geometry`: point_satisfied=3
- `not_in_manual_review`: point_satisfied=10, point_uncertain=1, point_violated=11

## Headline Metrics

- `floor_support_recovery_rate`: `0.8125`
- `point_uncertain_rate`: `0.03125`
- `obb_failure_to_point_satisfied_count`: `19`

## Interpretation

- This is a support/contact smoke test, not benchmark evidence.
- The key question is whether point/local-surface evidence recovers OBB-only support/contact failures.
- If many floor-support edges remain uncertain, the next refinement should use a stronger local plane or support surface estimator.

## Next Action

Compare `point_comparison.jsonl` against the OBB-only verifier output and decide whether to revise the support/contact rule.
