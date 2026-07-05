# R7 Attachment Observability Path Decision

Date: 2026-06-30

## Status

```text
artifact_root = artifacts/compatibility_dataset_v3_attachment_observability_path_decision_after_schema_shortcut_audit/
status = h002_compatibility_dataset_v3_attachment_observability_path_decision_select_class_pair_balanced_repair_mining
selected_path = attempt_one_class_pair_balanced_r7_repair_before_diagnostic_freeze
validation_errors = 0
next_todo = compatibility_dataset_v3_attachment_observability_class_pair_repair_mining_plan
```

## Decision

Do not run learned smoke on the current 560-row R7 artifact.

The selected next step is one targeted full-train class-pair-balanced repair
mining pass for `attached to` and `hanging on`. If this repair cannot create
mixed exact predicate/class-pair label cells after audit, R7 should be frozen as
diagnostic/qualitative observability evidence.

## Why Current R7 Is Blocked

| Probe | Target | Accuracy |
| --- | --- | ---: |
| `p_obs:T_subject_object_pair` | `p_obs` | 0.958929 |
| `p_obs:T_predicate_x_class_pair` | `p_obs` | 1.000000 |
| `p_rel_observable:T_subject_object_pair` | `p_rel_observable` | 0.986928 |
| `p_rel_observable:T_predicate_x_class_pair` | `p_rel_observable` | 1.000000 |

The issue is not schema leakage. The issue is target construction: current
labels are almost perfectly stratified by predicate and subject/object class
pair.

## Current Artifact Repair Capacity

| Target | Control Axis | Mixed Groups | Balanced Capacity |
| --- | --- | ---: | ---: |
| `p_obs` | `subject_object_pair` | 21 | 46 |
| `p_obs` | `predicate_x_subject_object_pair` | 0 | 0 |
| `p_rel` | `subject_object_pair` | 2 | 8 |
| `p_rel` | `predicate_x_subject_object_pair` | 0 | 0 |

This means the current 560-row artifact cannot be repaired by resampling. Exact
predicate and class-pair control is the necessary condition because
`predicate_x_class_pair` is the strongest shortcut, and its mixed capacity is
zero.

## Route Verdicts

| Route | Verdict | Reason |
| --- | --- | --- |
| run learned smoke now | reject | would measure class-pair memorization |
| drop subject/object labels from `T_e` | reject | hides the issue by weakening semantic content |
| repair current 560 rows only | reject | exact predicate/class-pair mixed capacity is zero |
| freeze R7 as diagnostic now | fallback | use only if repair mining fails |
| full-train class-pair-balanced repair mining | selected next | full train has enough candidate pool to try once |
| promote `connected to` primary | defer | no explicit topology/functional evidence |
| promote R7 to paper evidence | reject | no learned or paper-level reliability result |

## Next Mining Contract

Next TODO:

```text
compatibility_dataset_v3_attachment_observability_class_pair_repair_mining_plan
```

Required controls:

- exact predicate label within retained contrast cells
- same subject/object class pair within retained contrast cells whenever possible
- source score, rank, query id, packet id, candidate bucket, and review label stay hidden
- visual/mesh packets are audit evidence first, not raw model input
- no validation/test usage
- schema shortcut audit must be rerun after label ingestion

Minimum goals after labeling:

- at least `400` balanced primary rows
- at least `100` positive rows
- at least `20` exact predicate/class-pair mixed strata

## Boundary

- Train-only path decision.
- No new rows were materialized.
- No learned smoke was run.
- No validation/test split was used.
- H001 artifacts were not modified.
