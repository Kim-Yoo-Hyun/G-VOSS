# H002 Support/Contact Individual Predicate Sanitized View Smoke Plan

## Status

```text
artifact_root = artifacts/compatibility_dataset_v3_support_contact_individual_predicate_sanitized_view_smoke_plan/
status = h002_compatibility_dataset_v3_support_contact_individual_predicate_sanitized_view_smoke_plan_ready
rows = 640
positive / negative = 320 / 320
predicate_counts = lying on 320 / standing on 320
cv_groups = 258
mixed_label_cv_groups = 155
validation_errors = 0
learned_smoke_executed = false
next_todo = compatibility_dataset_v3_support_contact_individual_predicate_sanitized_view_smoke_runner
```

## Input Contract

The learned smoke must read only:

```text
artifacts/compatibility_dataset_v3_support_contact_individual_predicate_sanitized_view_smoke_plan/smoke_ready_view.jsonl
```

Allowed feature blocks:

```text
T_e
G_e_mesh_pose_contact
Q_e
```

Metadata-only fields:

```text
example_id
cv_group_id
schema_version
split
target_y
```

`cv_group_id` is a hashed scan-level split group. Raw `scan_id` is used only to
construct this group id and is not exposed as a model feature.

Blocked as model features:

```text
raw materialized rows
hidden manifest fields
scan_id / subject_id / object_id / directed_pair_id
source score / rank
H001 p_geom_valid
label_match_status
candidate_role
route_name
construction fields
```

## Planned Models

```text
M0_intercept
M1_semantic_only_T
M2_geometry_only_G
M3_TG_concat
M4_TG_predicate_geometry_interaction   # primary C_e smoke
M5_TGQ_factorized_observability
S1_predicate_label_shortcut
S2_class_pair_shortcut
S3_quality_shortcut
```

The primary test is `M4_TG_predicate_geometry_interaction`. It asks whether
`standing on` and `lying on` require different interpretations of the same
predicate-independent support/contact geometry evidence.

## Planned Controls

```text
wrong_T_same_G
shuffled_G_global
shuffled_G_within_predicate
no_interaction_concat
```

## Promotion Gates

- `M1/S1/S2/S3` should remain `<= 0.60` AUROC.
- `M4` or `M5` should reach `>= 0.70` AUROC.
- `M4` or `M5` should beat `max(M1, M2)` by `>= 0.05` AUROC.
- If `M2_geometry_only_G` is within `0.02` AUROC of `M4/M5`, the result is a
  geometry-dominance diagnostic rather than factorized compatibility evidence.
- `wrong_T_same_G` and shuffled-geometry controls must degrade.

## Boundary

- train-only smoke plan
- no learned smoke executed
- no validation/test usage
- no paper evidence promotion
- no H001 artifact modification

## Next

```text
compatibility_dataset_v3_support_contact_individual_predicate_sanitized_view_smoke_runner
```
