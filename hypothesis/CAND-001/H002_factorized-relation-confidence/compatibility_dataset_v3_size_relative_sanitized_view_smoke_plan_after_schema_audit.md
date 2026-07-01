# H002 Size-Relative Sanitized View Smoke Plan After Schema Audit

## Result

```text
artifact_root = artifacts/compatibility_dataset_v3_size_relative_sanitized_view_smoke_plan_after_schema_audit/
status = h002_compatibility_dataset_v3_size_relative_sanitized_view_smoke_plan_after_schema_audit_ready
validation_errors = 0
next_todo = compatibility_dataset_v3_size_relative_sanitized_view_smoke_runner_after_plan
```

This stage freezes the train-only learned-smoke input contract and comparison plan
for the `size_relative` branch. It does not train a model, does not use
validation/test data, and does not modify H001 artifacts.

## Input

```text
source_audit = artifacts/compatibility_dataset_v3_size_relative_schema_shortcut_audit_after_materialization/
source_status = h002_compatibility_dataset_v3_size_relative_schema_shortcut_audit_after_materialization_ready_for_smoke_plan
source_rows = 2400
```

## Runner-Ready View

```text
smoke_ready_view = artifacts/compatibility_dataset_v3_size_relative_sanitized_view_smoke_plan_after_schema_audit/smoke_ready_view.jsonl
schema = h002_size_relative_runner_ready_view_v1
rows = 2400
positive / negative = 1200 / 1200
cv_groups = 1200
paired groups = 1200
predicate_counts = bigger than 1200 / smaller than 1200
feature blocks = T_e + G_e_size
```

The runner-ready rows expose only:

- `T_e`: predicate label/text and relation family
- `G_e_size`: predicate-independent continuous log-ratio size geometry

`row_id`, `cv_group_id`, and `target_y` are metadata or target fields, not model
features.

## Planned Model Views

```text
M0_intercept
M1_semantic_only_T
M2_geometry_only_G_size
M3_TG_concat_no_interaction
M4_TG_size_interaction   # primary
S1_predicate_label_shortcut
S2_geometry_exact_tuple_shortcut
C1_wrong_T_same_G
C2_shuffled_G_global
C3_shuffled_G_within_predicate
C4_sign_flipped_G_control
```

The primary model is `M4_TG_size_interaction`, where predicate semantics select how
the same `G_e_size` evidence should be interpreted:

```text
expected_size_sign(predicate) * G_e_size
```

with:

```text
bigger than = +1
smaller than = -1
```

## Gates

```text
single-factor baselines <= 0.60 AUROC
primary M4 AUROC >= 0.95
M4 gain over best single-factor baseline >= 0.30 AUROC
wrong-T same-G control degrades to <= 0.60 AUROC or inverts
shuffled-G controls degrade to <= 0.60 AUROC
paired score margin positive in at least 0.90 of groups
```

## Interpretation

This stage keeps the H002 question narrow: size-ratio geometry by itself should not
solve the same-G target, and predicate text by itself should not solve it either.
The learned smoke must test whether a predicate-conditioned compatibility view can
recover the target while wrong-T and shuffled-G controls collapse.

This is still hypothesis-stage evidence. A passing smoke result would support the
`size_relative` compatibility route, but it would not yet be a paper-level result
without a Docker-reproducible experiment and held-out protocol.
