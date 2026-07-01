# H002 Independent Validity Target Plan

## Status

```text
stage = compatibility_dataset_v3_independent_validity_target_plan
status = h002_compatibility_dataset_v3_independent_validity_target_plan_ready
selected_path = select_gt_anchored_train_validity_inventory_before_materialization
validation_errors = 0
next_todo = compatibility_dataset_v3_independent_validity_source_inventory
```

## Artifact

```text
script = tools/compatibility_dataset_v3_independent_validity_target_plan.py
artifact_root = artifacts/compatibility_dataset_v3_independent_validity_target_plan/
input_synthesis = artifacts/compatibility_dataset_v3_multi_family_result_synthesis_plan/
```

Generated files:

- `summary.json`
- `selected_target_contract.json`
- `next_plan_contract.json`
- `target_option_table.csv`
- `family_capacity_table.csv`
- `source_inventory_table.csv`
- `validation_errors.jsonl`
- `report.md`

## Decision

The next target should be:

```text
GT_anchored_train_validity_target
```

This target is selected because the current two-family same-`G_e` results already prove the
controlled `C_e` mechanism. The remaining question is whether `C_e` helps when labels come from an
independent validity source rather than from the constructed same-geometry target.

Selected path:

```text
select_gt_anchored_train_validity_inventory_before_materialization
```

## Target Option Review

| Option | Verdict | Reason |
| --- | --- | --- |
| `GT_anchored_train_validity` | selected | official train GT is independent from same-`G_e` construction |
| `human_audit_accept_reject` | defer | existing labels are validation/no-GT or attachment diagnostic; new packet cost is high |
| `cross_source_agreement` | defer | current available cross-source artifacts are mostly validation-side |
| `high_precision_geometry_rule_subset` | auxiliary only | geometry-rule labels risk circularity with `G_e` |
| `no_GT_as_negative` | reject | 3DSSG annotation is incomplete, so no-GT cannot mean false |

## Family Capacity Snapshot

Official train GT has enough raw predicate mass for the two current primary families:

```text
relative_vertical:
  higher than = 1831
  lower than = 1831
  total = 3662

support_contact_pose_conditioned:
  standing on = 9992
  lying on = 2024
  total = 12016
```

Diagnostic or future families also have count, but they should not be primary materialized before
the independent target inventory:

```text
supported by = 821
attached to / hanging on / connected to = 8916
close by = 12484
left / right / front / behind = 37564
```

## Selected Target Contract

Primary families:

```text
relative_vertical = higher than / lower than
support_contact_pose_conditioned = standing on / lying on
```

Label policy:

- `C_e` positive: GT predicate and geometry evidence are compatible.
- `C_e` negative: matched counterfactual predicate or wrong-pair candidate is geometry-incompatible
  and not GT-supported.
- `C_e` abstain: no-GT but geometry-supported, low coverage, or annotation-sparse case.
- `p_obs` is observability, not relation truth.
- `p_rel` is allowed only if the next inventory finds enough observable accept/reject rows.

Forbidden policy:

- no-GT is not a negative label;
- validation/test labels are not used;
- hidden construction fields are not model input;
- H001 artifacts are read-only.

## Next

Before materializing rows, the next stage must inventory:

- GT-positive count by family/predicate;
- source `Z_e` join count from Open3DSG train raw dump;
- geometry `G_e` join count by family;
- matched hard-negative capacity;
- no-GT abstain/audit pool count;
- shortcut-risk precheck plan.

```text
compatibility_dataset_v3_independent_validity_source_inventory
```

## Boundary

- Train-only target plan.
- No validation/test usage.
- No learned model trained in this step.
- No H001 artifact modification.
- No paper-level evidence promotion.
