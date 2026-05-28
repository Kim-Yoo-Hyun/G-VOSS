# Attachment Deferred Verifier Policy

Status: `attachment_deferred_verifier_policy_ready_no_decisions_no_metrics`
Created at: `2026-05-28T00:52:26+00:00`

## Claim Boundary

This is a G2 verifier-policy design artifact. It defines future
`satisfied` / `violated` / `uncertain` logic but does not apply the
policy to source predictions, fit calibration, compute metrics, or
change the current AAAI main claim.

## Inputs Checked

- `point_surface_manifest`: `attachment_deferred_point_surface_validation_ready_no_verifier`
- `point_surface_validation`: `passed`
- `point_surface_rows`: `36`
- `ready_rows`: `36`
- `near_contact_rows`: `27`
- `forbidden_fields_present`: `[]`

## Conservative Threshold Defaults

- near contact: `0.05` m
- uncertain contact band: `[0.05, 0.15]` m
- clear far distance: `0.3` m
- min near-contact points for satisfied: `3`
- min contact patch score for satisfied: `0.2`

## Subtypes Covered

- `attached_to_vertical_or_overhead_surface` -> `attached to`
- `attached_to_furniture_or_fixture` -> `attached to`
- `ambiguous_functional_attachment` -> `attached to`
- `hanging_from_vertical_surface` -> `hanging on`
- `hanging_from_overhead_or_fixture` -> `hanging on`
- `ambiguous_draped_or_occluded_hanging` -> `hanging on`
- `connected_adjacent_or_contiguous` -> `connected to`
- `connected_by_fixture_or_part` -> `connected to`
- `ambiguous_functional_connection` -> `connected to`

## Guardrails

- Ambiguous functional subtypes default to `uncertain`.
- Class affordance/context is never proof.
- `violated` requires clear negative geometry, not weak semantic plausibility.
- Future source metrics remain blocked until G3 calibration/counterfactual and GT verifier-evaluation gates pass.

## Next Gate

`G3_attachment_calibration_counterfactual_generation`
