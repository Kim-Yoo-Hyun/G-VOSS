# H002 Independent Validity Path Decision After Schema Shortcut Audit

## Status

```text
status = h002_compatibility_dataset_v3_independent_validity_path_decision_select_stratum_repair_capacity_scan
selected_path = freeze_current_target_diagnostic_select_full_train_stratum_repair_capacity_scan
validation_errors = 0
next_todo = compatibility_dataset_v3_independent_validity_stratum_repair_capacity_scan
```

## Decision

The current independent-validity target is frozen as diagnostic evidence and is not promoted to
learned smoke.

The selected next step is a full-train stratum-repair capacity scan. The goal is to check whether
full train can provide enough accept/reject rows within exact semantic strata:

```text
predicate_label + subject_class_label + object_class_label
```

## Why Current Learned Smoke Is Rejected

The schema shortcut audit showed that the sanitized view has no hidden-field leakage, but the target
is still recoverable from allowed semantic strata:

| Probe | Accuracy | Risk |
| --- | ---: | --- |
| `predicate_x_class_pair` | 0.976562 | high |
| `subject_object_class_pair` | 0.840000 | medium |

This means a learned model would likely memorize which predicate/object-pair strata are usually
positive or negative, rather than learning predicate-geometry compatibility.

## Current Artifact Repair Capacity

| Control Axis | Groups | Mixed Groups | Balanced Capacity | Verdict |
| --- | ---: | ---: | ---: | --- |
| `family` | 2 | 2 | 3200 | enough for coarse balance |
| `predicate_label` | 4 | 4 | 2374 | enough but too weak |
| `subject_object_class_pair` | 500 | 82 | 1024 | enough but misses strongest shortcut |
| `predicate_x_class_pair` | 719 | 19 | 150 | insufficient |
| `predicate_x_class_pair_x_rank_band` | 1026 | 31 | 146 | insufficient |

The strongest shortcut is `predicate_x_class_pair`, so controlling only family, predicate, or
subject/object pair is not enough. Under exact predicate-class-pair control, the current materialized
artifact has only `150` balanced rows, far below the repair minimum:

```text
minimum_repaired_primary_rows = 800
minimum_repaired_per_class = 400
```

## Route Verdicts

| Route | Verdict |
| --- | --- |
| run learned smoke now | reject |
| drop object labels from `T_e` | reject |
| repair current artifact with exact predicate-class rebalancing | reject |
| repair current artifact with class-pair-only rebalancing | reject |
| use `geometry_status` / `p_geom_valid` as learned input | reject |
| freeze current independent-validity target as diagnostic | selected as boundary |
| full-train stratum-repair capacity scan | selected next |
| promote to paper reliability evidence | reject |

## Boundary

- Train-only path decision.
- No validation/test usage.
- No learned model was run.
- No H001 artifact was modified.
- This is not paper evidence.

## Next

```text
compatibility_dataset_v3_independent_validity_stratum_repair_capacity_scan
```
