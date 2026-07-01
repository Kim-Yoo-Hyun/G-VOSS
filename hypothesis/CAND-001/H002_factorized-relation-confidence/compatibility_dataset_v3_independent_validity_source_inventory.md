# H002 Independent Validity Source Inventory

## Status

```text
stage = compatibility_dataset_v3_independent_validity_source_inventory
status = h002_compatibility_dataset_v3_independent_validity_source_inventory_ready_for_materialization_plan
selected_path = materialize_gt_anchored_independent_validity_rows
validation_errors = 0
next_todo = compatibility_dataset_v3_independent_validity_materialization_plan
```

## Artifact

```text
script = tools/compatibility_dataset_v3_independent_validity_source_inventory.py
artifact_root = artifacts/compatibility_dataset_v3_independent_validity_source_inventory/
input_plan = artifacts/compatibility_dataset_v3_independent_validity_target_plan/
input_match_rows = artifacts/train_rga_full/open3dsg_train_full/rga/match_rows.jsonl
```

Generated files:

- `summary.json`
- `next_plan_contract.json`
- `family_inventory_table.csv`
- `capacity_decision_table.csv`
- `target_pool_table.csv`
- `candidate_pool_preview.jsonl`
- `validation_errors.jsonl`
- `report.md`

## Inventory Result

The source inventory scanned the full train-side `match_rows.jsonl` stream:

```text
total_match_rows_scanned = 4818996
selected_primary_rows = 741384
families_ready = relative_vertical, support_contact_pose_conditioned
```

Both primary families pass the source `Z_e`, geometry `G_e`, positive, strong-negative, and
no-GT-policy gates.

| Family | Rows | Source `Z_e` Join | Geometry `G_e` Join | Exact GT Satisfied | Strong Negatives | No-GT Satisfied Abstain |
| --- | --- | --- | --- | --- | --- | --- |
| `relative_vertical` | `370692` | `1.0` | `1.0` | `1140` | `19350` | `105242` |
| `support_contact_pose_conditioned` | `370692` | `1.0` | `1.0` | `7564` | `1067` | `83463` |

## Capacity Decision

Materialization planning is allowed for both families:

```text
relative_vertical:
  positive_exact_gt_satisfied = 1140
  strong_negative_gt_pair_other_predicate_unsatisfied = 19350
  geometry_g_join_rate = 1.0
  materialization_feasible = true

support_contact_pose_conditioned:
  positive_exact_gt_satisfied = 7564
  strong_negative_gt_pair_other_predicate_unsatisfied = 1067
  geometry_g_join_rate = 1.0
  materialization_feasible = true
```

## Target Pool Policy

Allowed positive:

```text
exact GT match + geometry_status = satisfied
```

Allowed negative candidate:

```text
pair has another GT predicate or same-family mismatch + geometry_status = unsatisfied
```

Abstain/audit:

```text
no-GT + geometry satisfied
no-GT + geometry unsatisfied
geometry uncertain
GT exact match + geometry unsatisfied
```

The key point is that no-GT rows are counted as abstain/audit pools. They are not used as negative
labels.

## Next

The next stage can write a materialization plan for GT-anchored independent validity rows:

```text
compatibility_dataset_v3_independent_validity_materialization_plan
```

Required plan items:

- row quotas by family and target role;
- blocked-field schema;
- balanced or explicitly weighted class plan;
- hard-negative matching policy;
- abstain/no-GT handling policy;
- next schema/shortcut audit gate.

## Boundary

- Train-only source inventory.
- No validation/test usage.
- No row materialization.
- No learned model trained.
- No H001 artifact modification.
- No paper-level evidence promotion.
