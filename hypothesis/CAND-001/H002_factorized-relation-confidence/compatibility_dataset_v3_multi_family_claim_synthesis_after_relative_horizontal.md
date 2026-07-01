# H002 Multi-Family Claim Synthesis After Relative-Horizontal

Date: 2026-06-29 KST

## Status

```text
artifact_root = artifacts/compatibility_dataset_v3_multi_family_claim_synthesis_after_relative_horizontal/
status = h002_compatibility_dataset_v3_multi_family_claim_synthesis_after_relative_horizontal_ready
selected_path = update_relation_aware_compatibility_routing_claim_with_relative_horizontal_select_table_plan_update
validation_errors = 0
next_todo = compatibility_dataset_v3_ablation_and_table_plan_update_after_relative_horizontal_synthesis
```

## Updated Claim

H002 now supports a train-only mechanism claim:

```text
Different relation families require different evidence routes, and explicit
T_e x G_e compatibility is necessary in clean vertical, size, and frame-aware
horizontal families while remaining useful but harder in support/contact.
```

This is still not a paper-level result. It is a route-level hypothesis synthesis
after controlled train-only smokes and result reviews.

## Current Route Map

| Family | Role | Claim Position |
| --- | --- | --- |
| `relative_vertical` | clean sign compatibility route | main mechanism evidence |
| `size_relative` | clean size-comparison compatibility route | main mechanism evidence with calibration caveat |
| `relative_horizontal` | frame-aware directional compatibility route | main mechanism evidence with reference-frame caveat |
| `support_contact` | challenging compatibility route | main route evidence with caveat |
| `proximity` | geometry-easy route | diagnostic / control |
| `attachment_like` | observability-heavy route | future / diagnostic |

## Boundary

Allowed:

- relation-aware evidence routing
- `C_e = compatibility(T_e, G_e)` as the current core mechanism
- family-specific routes instead of fixed semantic+geometry fusion
- `relative_horizontal` as frame-aware evidence, not complete horizontal coverage

Blocked:

- paper-level performance
- held-out/test relation reliability
- calibrated `p_rel` / `p_obs`
- complete horizontal ontology including `in front of`
- support/contact fully solved
- geometry-only reliability framework
- universal all-family generalization

## Next

Update the ablation/table plan so the current route map includes:

- clean rows: `relative_vertical`, `size_relative`, `relative_horizontal`
- challenging row: `support_contact`
- diagnostic/control rows: `proximity`, `attachment_like`, `supported by`
- controls: semantic-only, geometry-only, concat, interaction, wrong-T, shuffled-G,
  sign-flip, wrong-frame and endpoint-swap where applicable

