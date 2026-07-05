# Route Map Update After Supported-By Decomposition Review

## Status

```text
artifact_root = artifacts/compatibility_dataset_v3_route_map_update_after_supported_by_decomposition_review/
status = h002_compatibility_dataset_v3_route_map_update_after_supported_by_decomposition_review_ready
selected_path = merge_r6_diagnostic_boundary_select_attachment_observability_target_plan
validation_errors = 0
next_todo = compatibility_dataset_v3_attachment_observability_target_plan
```

This stage updates the H002 route map after the R6 `supported by` review. It does not materialize rows, train a model, or use validation/test data.

## Decision

R6 `supported by` is now frozen as a diagnostic broad-label decomposition route.

R5 `standing on` / `lying on` stays separate as the support/contact predicate-geometry compatibility route.

R7 `attached to` / `hanging on` / `connected to` is selected as the next active route because it tests the observability-heavy side of H002:

```text
Q_e / p_obs first, p_rel only when observable
```

## Route Delta

- R6 status: `included_as_decomposition_route_candidate` -> `diagnostic_frozen_not_main_factorized_success`
- R6 paper role: `claim_control_or_next_probe` -> `diagnostic_broad_label_decomposition_boundary`
- R5 boundary: `standing on` / `lying on` kept separate from `supported by`
- R7 status: `queued_after_route_map_update` -> `selected_next_active_route`

## Current Claim Boundary

Main mechanism families remain:

- `relative_vertical`
- `size_relative`
- `relative_horizontal`
- `support_contact`

Diagnostic/control families:

- `proximity`
- `superordinate_support`

Blocked:

- adding `supported by` as a main mechanism row;
- claiming calibrated `p_rel` / `p_obs`;
- claiming paper-level held-out reliability;
- using visual/multiview features before the R7 audit and model-safe boundary are defined.

## Next

Run `compatibility_dataset_v3_attachment_observability_target_plan`.

The first R7 step should only define the target plan and evidence boundary. It should not materialize rows or run learned smoke yet.
