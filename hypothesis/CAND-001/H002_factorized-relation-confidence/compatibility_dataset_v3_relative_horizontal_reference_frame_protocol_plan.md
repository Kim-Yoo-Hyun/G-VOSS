# Relative-Horizontal Reference-Frame Protocol Plan

## Status

```text
status = h002_compatibility_dataset_v3_relative_horizontal_reference_frame_protocol_plan_ready
selected_path = relative_horizontal_reference_frame_source_inventory_before_materialization
validation_errors = 0
next_todo = compatibility_dataset_v3_relative_horizontal_source_inventory_after_reference_frame_protocol_plan
```

This step defines the reference-frame protocol for the `relative_horizontal`
family. It does not materialize rows, train a model, use validation/test, or
promote H002 to paper evidence.

## Command

```bash
python hypothesis/CAND-001/H002_factorized-relation-confidence/tools/compatibility_dataset_v3_relative_horizontal_reference_frame_protocol_plan.py
```

## Artifact Root

```text
artifacts/compatibility_dataset_v3_relative_horizontal_reference_frame_protocol_plan/
```

Key outputs:

- `summary.json`
- `frame_protocol.csv`
- `predicate_protocol.csv`
- `geometry_evidence_schema.csv`
- `qe_observability_schema.csv`
- `target_construction_plan.csv`
- `control_plan.csv`
- `blocked_fields.csv`
- `model_views.csv`
- `next_runner_contract.json`
- `report.md`
- `validation_errors.jsonl`

## Counts

```text
frame_protocol_rows = 4
predicate_protocol_rows = 5
geometry_schema_rows = 5
qe_schema_rows = 5
target_construction_rows = 5
control_rows = 7
blocked_field_rows = 8
model_view_rows = 5
```

## Reference-Frame Decision

`relative_horizontal` is not ready for direct row materialization because the
meaning of `left`, `right`, `front`, `behind`, and `in front of` can change under
different reference frames.

The protocol keeps four frame candidates:

```text
scene_aligned_world_xy = first source-inventory candidate
view_or_camera_frame = audit/Q_e-first candidate
object_centric_front_axis = diagnostic/deferred
layout_or_room_frame = diagnostic
```

The initial route is to inventory train-side evidence before selecting any frame
for target construction.

## Factor Contract

```text
T_e = horizontal predicate text/label
G_e_horizontal = predicate-independent signed horizontal displacement under a frozen frame
Q_e_frame = frame availability, frame disagreement, near-axis-boundary ambiguity
C_e = compatibility(T_e, G_e_horizontal), excluding Z_e
```

`Z_e` source score/rank is blocked from the first `C_e` test. `Q_e_frame` controls
whether the relation can be judged, not whether the relation is true.

## Predicate-Level Fallback

If the family-level route fails, split the family into:

```text
left/right
front/behind
in front of alias/diagnostic
```

This follows the broader H002 rule that a multi-predicate family should not be
discarded solely because the family aggregate fails.

## Required Controls

```text
same-G predicate flip
wrong-frame rotation
axis sign flip
subject-object swap
predicate alias audit
class-pair/source shortcut audit
axis-boundary abstain
```

## Next

Run the train-side source inventory:

```text
compatibility_dataset_v3_relative_horizontal_source_inventory_after_reference_frame_protocol_plan
```

The source inventory must measure anchor counts, 3RScan centroid/OBB join rate,
same-G predicate-flip capacity, frame availability, alias behavior for `front` vs
`in front of`, and class/scan/endpoint concentration before any materialization.
