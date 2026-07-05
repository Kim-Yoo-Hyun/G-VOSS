# Relative-Horizontal Source Inventory After Reference-Frame Protocol Plan

## Status

```text
status = h002_compatibility_dataset_v3_relative_horizontal_source_inventory_after_reference_frame_protocol_plan_ready
selected_path = relative_horizontal_inventory_ready_for_candidate_materialization_plan_with_frame_qe_controls
validation_errors = 0
next_todo = compatibility_dataset_v3_relative_horizontal_candidate_materialization_plan_after_source_inventory
```

This step scans train-side source capacity for the `relative_horizontal` family.
It does not materialize rows, train a model, use validation/test, or promote H002
to paper evidence.

## Command

```bash
python hypothesis/CAND-001/H002_factorized-relation-confidence/tools/compatibility_dataset_v3_relative_horizontal_source_inventory_after_reference_frame_protocol_plan.py
```

## Artifact Root

```text
artifacts/compatibility_dataset_v3_relative_horizontal_source_inventory_after_reference_frame_protocol_plan/
```

Key outputs:

- `summary.json`
- `predicate_inventory.csv`
- `axis_alignment_inventory.csv`
- `selected_axis_candidates.csv`
- `alias_inventory.csv`
- `frame_availability_inventory.csv`
- `scan_concentration.csv`
- `class_pair_concentration.csv`
- `endpoint_pair_concentration.csv`
- `capacity_summary.json`
- `anchor_preview.jsonl`
- `report.md`
- `validation_errors.jsonl`

## Predicate Inventory

```text
left = 12,016 train rows / 45,357 full rows
right = 12,016 train rows / 45,357 full rows
front = 6,766 train rows / 24,165 full rows
behind = 6,766 train rows / 24,165 full rows
in front of = 0 train rows / 0 full rows
```

Centroid, OBB, sequence/camera-pose, and multi-view availability are all `1.0`
for observed train anchors.

## Selected Axis Candidates

```text
left/right:
  axis = scene_world_x
  left sign = negative
  nonboundary rows = 22,148
  compatible rows = 16,958
  alignment = 0.765667
  same-G predicate-flip rows = 33,916

front/behind:
  axis = scene_world_y
  front sign = negative
  nonboundary rows = 12,302
  compatible rows = 9,296
  alignment = 0.755649
  same-G predicate-flip rows = 18,592
```

This is sufficient for a materialization plan, but not sufficient for a clean
paper claim by itself. The alignment is only about `0.76`, so frame-disagreement
and near-axis-boundary rows must be routed to `Q_e` or diagnostics.

## Alias Decision

`in front of` is not observed in the current train/full 3DSSG sources. It must not
be merged with `front` in the first materialization plan.

## Shortcut And Concentration

```text
top_scan_fraction = 0.004845
top_class_pair_fraction = 0.087211
```

No scan or class-pair concentration gate blocks the next plan.

## Next

Proceed to a candidate materialization plan:

```text
compatibility_dataset_v3_relative_horizontal_candidate_materialization_plan_after_source_inventory
```

The materialization plan must freeze row quotas, exclude `in front of` from main
binary rows, keep same-G predicate flips, and include wrong-frame, sign-flip,
subject-object swap, class-pair/source shortcut, and axis-boundary `Q_e` controls.
