# Compatibility Dataset V2 Sanitized View Smoke Plan

Artifact root:

```text
artifacts/compatibility_dataset_v2_sanitized_view_smoke_plan/
```

Status:

```text
status = h002_compatibility_dataset_v2_sanitized_view_smoke_plan_ready
rows = 400
compatibility positive / negative = 200 / 200
paired groups = 200
validation_errors = 0
smoke_ready_view_written = true
learned_smoke_executed = false
next_todo = compatibility_dataset_v2_sanitized_view_smoke_runner
```

## Purpose

This step fixes the model-input contract before any learned smoke is run.

The previous schema audit correctly blocked raw construction metadata, but the intermediate
`sanitized_model_view.jsonl` still contained one generated-negative shortcut:

```text
Z_e.source_score_inherited_for_counterfactual accuracy = 1.000
```

This field exists because generated counterfactual rows inherit the anchor source score. It is not
deployable source-confidence evidence. Therefore this plan writes a stricter input:

```text
artifacts/compatibility_dataset_v2_sanitized_view_smoke_plan/smoke_ready_view.jsonl
```

The next learned smoke must use this file, not the raw candidate rows and not the first sanitized
view.

## Allowed Blocks

The smoke-ready view allows only:

```text
T_e
Z_e_safe
G_e_numeric
Q_e_safe
```

`Z_e_safe` keeps:

```text
source_id
source_score_available
source_score_raw
source_score_normalized
source_rank
source_rank_band
```

`Z_e_safe` removes:

```text
source_score_inherited_for_counterfactual
```

## Blocked Fields

The runner must not use these fields as features:

```text
row_role
counterfactual_type
hidden_control
G_e.geometry_source
Q_e.generated_counterfactual
Q_e.evidence_conflict_flag
geometry_status_baseline
relation_source
audit_reference
Z_e.source_score_inherited_for_counterfactual
row_id
group_id
```

`row_id` and `group_id` may be used only for bookkeeping and grouped split. They are not model
features.

## Planned Task

Primary smoke task:

```text
Task A: compatibility
target = y_compatibility
positive = anchor predicate + aligned geometry
negative = generated counterfactual predicate/geometry pair
```

This v2 smoke does not train a real `p_obs` or `p_rel` target. `Q_e_safe` is included only as a
sanitized covariate/ablation because all rows have raw numeric witness coverage.

## Planned Models

| Model | Input | Role |
| --- | --- | --- |
| `M0_intercept` | none | class-balance sanity |
| `M1_source_only_Z_safe` | `Z_e_safe` | source-confidence baseline |
| `M2_semantic_only_T` | `T_e` | semantic shortcut baseline |
| `M3_semantic_source_TZ_safe` | `T_e + Z_e_safe` | semantic/source shortcut baseline |
| `M4_geometry_numeric_G` | `G_e_numeric` | geometry-only baseline |
| `M5_compatibility_TG_numeric` | `T_e + G_e_numeric` | primary compatibility smoke |
| `M6_factorized_sanitized_TZGQ` | `T_e + Z_e_safe + G_e_numeric + Q_e_safe` | final factorized smoke |
| `S1_predicate_family_shortcut` | predicate/family only | semantic shortcut probe |
| `S2_source_score_rank_shortcut` | source score/rank only | source shortcut probe |
| `S3_object_label_pair_shortcut` | subject/object text only | object-prior shortcut probe |
| `C1_shuffled_G_within_family_control` | `T_e + shuffled G_e_numeric` | geometry-alignment control |
| `C2_wrong_T_same_G_control` | wrong predicate + same `G_e_numeric` | predicate-conditioning control |

## Runner Gates

The next runner is allowed only if:

```text
validation_errors = 0
rows = 400
positive / negative = 200 / 200
paired groups = 200
blocked fields are absent from model_views
```

Compatibility result is promising only if:

```text
M5_compatibility_TG_numeric > source/semantic shortcut baselines
M5 degrades under shuffled-G and wrong-T controls
family-specific metrics are reported for support_contact and relative_vertical
```

Failure interpretation:

- If `M2` or `S3` matches `M5`, the task is still semantic-prior dominated.
- If `M4` matches `M5`, predicate conditioning is not adding meaningful signal.
- If `C1` does not degrade, aligned geometry is not being used.
- If `C2` does not degrade, predicate semantics are not being used.

## Boundary

This plan:

- uses train-only data;
- does not run learned smoke;
- does not train a paper model;
- does not create paper-level evidence;
- does not modify H001 artifacts.

## Next

```text
compatibility_dataset_v2_sanitized_view_smoke_runner
```
