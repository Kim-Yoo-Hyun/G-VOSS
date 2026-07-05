# Relative-Horizontal Candidate Materialization Plan After Source Inventory

## Status

```text
status = h002_compatibility_dataset_v3_relative_horizontal_candidate_materialization_plan_after_source_inventory_ready
selected_path = materialize_relative_horizontal_same_g_predicate_flip_rows_with_frame_qe_controls
validation_errors = 0
next_todo = compatibility_dataset_v3_relative_horizontal_candidate_materialization_after_plan
```

This step freezes the train-only materialization plan for `relative_horizontal`.
It does not materialize rows, train a model, use validation/test, or promote H002
to paper evidence.

## Command

```bash
python hypothesis/CAND-001/H002_factorized-relation-confidence/tools/compatibility_dataset_v3_relative_horizontal_candidate_materialization_plan_after_source_inventory.py
```

## Artifact Root

```text
artifacts/compatibility_dataset_v3_relative_horizontal_candidate_materialization_plan_after_source_inventory/
```

Key outputs:

- `summary.json`
- `materialization_contract.json`
- `row_quota_plan.csv`
- `frame_selection_plan.csv`
- `target_construction_plan.csv`
- `qe_policy.csv`
- `feature_schema.csv`
- `blocked_fields.csv`
- `control_plan.csv`
- `output_manifest_plan.csv`
- `next_runner_contract.json`
- `report.md`
- `validation_errors.jsonl`

## Frozen Quota

```text
primary_groups = 1,200
primary_rows = 2,400
positive_rows = 1,200
negative_rows = 1,200

left/right groups = 600
front/behind groups = 600

left rows = 600
right rows = 600
front rows = 600
behind rows = 600
in front of rows = 0
```

Diagnostic rows are planned separately:

```text
axis_boundary_diagnostic_groups = 160
axis_boundary_diagnostic_rows = 320
opposing_frame_diagnostic_groups = 160
opposing_frame_diagnostic_rows = 320
```

## Frame Selection

```text
left/right:
  selected_frame = scene_world_x
  sign_rule = left negative / right positive
  alignment = 0.765667
  available same-G flip rows = 33,916

front/behind:
  selected_frame = scene_world_y
  sign_rule = front negative / behind positive
  alignment = 0.755649
  available same-G flip rows = 18,592
```

The selected frames are source-inventory candidates, not final paper evidence.
The alignment is not clean enough to treat world-frame compatibility as ground
truth without `Q_e` and diagnostic controls.

## Target Construction

The primary target uses same-G predicate flips:

```text
row A: same directed pair geometry, predicate = left/front
row B: same directed pair geometry, predicate = right/behind
```

Only one row in each group is compatible under the frozen frame sign rule.
Both rows have identical `G_e_horizontal`; the target should require
`T_e x G_e_horizontal` interaction rather than geometry-only scoring.

## Q_e Policy

Do not force the following rows into the primary binary target:

- axis-boundary rows: `abs(selected signed offset) < 0.10m`
- frame-disagreement rows: GT predicate opposes selected world-axis sign
- `in front of`: unobserved in current train/full sources

These rows are `Q_e`/`p_obs` or diagnostic rows.

## Required Controls

```text
schema leakage
geometry-only
semantic-only
T_e x G_e interaction
wrong-T
axis sign flip
wrong-frame rotation
subject-object swap
class-pair hidden probe
Q_e diagnostic exclusion
```

## Next

Run the train-only materialization:

```text
compatibility_dataset_v3_relative_horizontal_candidate_materialization_after_plan
```

The materialization runner must create model-safe rows, hidden provenance,
same-G group manifests, and schema prechecks without exposing target/source,
construction, scan, endpoint, discretized-axis, or class-pair shortcut fields in
the main model view.
