# H002 Size-Relative Candidate Materialization Plan After Source Inventory

Date: 2026-06-29 KST

## Purpose

`size_relative` source inventory가 충분하다는 것을 확인한 뒤, 실제 row를 만들기 전에
materialization policy를 고정했다. 이 단계는 plan 단계이며, row materialization,
schema audit, learned smoke는 아직 수행하지 않았다.

## Artifact

```text
artifact_root = artifacts/compatibility_dataset_v3_size_relative_candidate_materialization_plan_after_source_inventory/
status = h002_compatibility_dataset_v3_size_relative_candidate_materialization_plan_after_source_inventory_ready
selected_path = materialize_size_relative_same_g_predicate_flip_rows
validation_errors = 0
next_todo = compatibility_dataset_v3_size_relative_candidate_materialization_after_plan
```

Generated files:

- `materialization_contract.json`
- `row_quota_plan.csv`
- `feature_schema.csv`
- `blocked_fields.csv`
- `control_plan.csv`
- `output_manifest_plan.csv`
- `summary.json`
- `report.md`
- `validation_errors.jsonl`

## Frozen Row Plan

Primary compatibility rows:

```text
primary_groups = 1200
primary_rows = 2400
positive_rows = 1200
negative_rows = 1200
subject_bigger_groups = 600
subject_smaller_groups = 600
bigger than rows = 1200
smaller than rows = 1200
```

Diagnostic-only rows:

```text
ambiguous_size_groups = 50
ambiguous_size_rows = 100
gt_geometry_conflict_groups = 36
gt_geometry_conflict_rows = 72
```

The diagnostic rows must not enter the primary `C_e` binary target.

## Core Materialization Rule

Each primary group must produce two rows with identical `G_e_size` and different
semantic predicate `T_e`.

```text
same scan + same subject + same object + same G_e_size

row A: predicate = bigger than
row B: predicate = smaller than
```

If the subject is geometrically bigger, `bigger than` is positive and `smaller than`
is negative. If the subject is geometrically smaller, the labels are reversed.

This is necessary because `size_relative` can otherwise collapse into a simple
geometry threshold verifier. Under this plan, geometry-only sees the same `G_e_size`
for both rows in a group, so it should not solve the compatibility target by itself.

## Caps

```text
max_groups_per_class_pair = 240
max_groups_per_class_pair_direction = 120
max_groups_per_scan = 24
```

These caps reduce class-pair and scan dominance. They do not make the artifact
paper-level evidence; they only define the next train-only materialization contract.

## Model-Safe Feature Boundary

Allowed in the main compatibility view:

- `T_e.predicate_text`
- `T_e.relation_family`
- continuous `G_e_size` log ratios:
  - `log_volume_ratio_s_over_o`
  - `log_max_extent_ratio_s_over_o`
  - `log_footprint_area_ratio_s_over_o`
  - `log_vertical_extent_ratio_s_over_o`

Allowed only for observability / `Q_e` view:

- `abs_log_volume_ratio`
- `pair_obb_available`

Blocked from the first main view:

- source/GT/construction fields
- target labels
- discretized rule labels such as `direction_by_volume`
- `volume_ratio_band`
- scan/object identity
- class labels and class-pair fields
- `Z_e` source score/rank, because this probe uses GT anchors rather than a relation-source score

## Required Controls

- schema leakage check
- geometry-only control
- semantic-only control
- `T_e x G_e_size` compatibility interaction
- wrong-T control
- shuffled-G within class-pair control
- shuffled-G global control
- hidden class-pair shortcut probe
- ambiguous-size rows excluded from primary binary target

## Boundary

- Train-only plan.
- No rows materialized in this stage.
- No learned smoke or training run.
- No validation/test source used.
- No H001 artifacts modified.
- Not paper-level evidence.

## Next

```text
compatibility_dataset_v3_size_relative_candidate_materialization_after_plan
```
