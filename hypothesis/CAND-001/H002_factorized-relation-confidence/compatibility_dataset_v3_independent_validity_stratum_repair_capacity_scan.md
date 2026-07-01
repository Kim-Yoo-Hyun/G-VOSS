# H002 Independent Validity Stratum Repair Capacity Scan

## Status

```text
status = h002_compatibility_dataset_v3_independent_validity_stratum_repair_capacity_scan_ready_for_materialization_plan
selected_path = materialize_exact_predicate_class_stratum_repaired_independent_validity_target
validation_errors = 0
next_todo = compatibility_dataset_v3_independent_validity_stratum_repair_materialization_plan
```

## Purpose

The previous independent-validity target was blocked because `predicate_x_class_pair` recovered the
label with high accuracy. This scan checks whether full train contains enough mixed positive/negative
rows within exact semantic strata:

```text
predicate_label + subject_class_label + object_class_label
```

If capacity is sufficient, the next materialization can balance labels within those exact strata and
remove the strongest shortcut.

## Full Train Counts

```text
total_match_rows = 4818996
selected_family_rows = 741384
primary_rows = 29121
primary_positive = 8704
primary_negative = 20417
source_z_join_rate_primary = 1.0
geometry_g_join_rate_primary = 1.0
```

Family counts:

| Family | Positive | Negative |
| --- | ---: | ---: |
| `relative_vertical` | 1140 | 19350 |
| `support_contact_pose_conditioned` | 7564 | 1067 |

Predicate counts:

| Predicate | Positive | Negative |
| --- | ---: | ---: |
| `higher than` | 570 | 4970 |
| `lower than` | 570 | 14380 |
| `lying on` | 1643 | 685 |
| `standing on` | 5921 | 382 |

## Capacity

| Control Axis | Groups | Mixed Groups | Raw Balanced Capacity | Scan-Capped Capacity |
| --- | ---: | ---: | ---: | ---: |
| `family` | 2 | 2 | 4414 | 4414 |
| `predicate_label` | 4 | 4 | 4414 | 4414 |
| `subject_object_class_pair` | 2223 | 243 | 11378 | 10870 |
| `predicate_x_class_pair` | 3024 | 39 | 2384 | 2252 |
| `predicate_x_class_pair_x_rank_band` | 4698 | 77 | 2378 | 2122 |

Repair gate:

```text
min_repaired_primary_rows = 800
min_repaired_per_class = 400
min_mixed_exact_strata = 30
min_scan_capped_rows = 600

exact_predicate_class_mixed_groups = 39
exact_predicate_class_balanced_capacity = 2384
exact_predicate_class_scan_capped_capacity = 2252
repair_ready = true
```

## Decision

Full train has enough exact semantic-stratum capacity to attempt repair. The next target should be
materialized by selecting only strata that contain both labels and balancing positive/negative rows
within each exact `predicate_x_class_pair` stratum.

Rejected routes:

- class-pair-only repair, because it does not control the strongest `predicate_x_class_pair`
  shortcut.
- using `geometry_status`, `p_geom_valid`, `consistency_score`, or residual as model input, because
  those are construction summaries.
- freezing independent validity permanently, because full train capacity is sufficient for one more
  controlled materialization attempt.

## Boundary

- Train-only full-train capacity scan.
- No validation/test usage.
- No candidate rows were materialized.
- No learned model was run.
- No H001 artifact was modified.
- This is not paper evidence.

## Next

```text
compatibility_dataset_v3_independent_validity_stratum_repair_materialization_plan
```
