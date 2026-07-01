# Compatibility Dataset V3 Support/Contact Visual/Mesh Audit Target Plan

## Result

```text
artifact_root = artifacts/compatibility_dataset_v3_support_contact_visual_mesh_audit_target_plan/
status = h002_compatibility_dataset_v3_support_contact_visual_mesh_audit_target_plan_ready_for_source_inventory
selected_path = plan_visual_mesh_audit_target_source_before_materialization
validation_errors = 0
next_todo = compatibility_dataset_v3_support_contact_visual_mesh_audit_source_inventory
```

## Purpose

This step fixes the target contract for the selected H002 route:

```text
support_contact_human_visual_mesh_audit_target
```

It does not materialize rows, fill labels, train a model, run a learned smoke, or use
validation/test rows. The goal is to define the independent audit target source before any packet
generation.

## Selected Relations

```text
lying on
standing on
supported by
```

Source capacity from the prior train-only inventory:

```text
support/contact rows = 161498
distinct scans = 1157
distinct directed pairs = 75763
lying on = 60652
standing on = 50245
supported by = 50601
scan asset complete rate = 1.0
mesh contact surface possible rate = 1.0
sequence multiview possible rate = 1.0
```

## Target Contract

The label source is visible visual/mesh audit evidence, not `source_score`, `rank`, `queue_kind`,
old `geometry_status`, old `p_geom_valid`, or GT-missing status.

Main target axes:

- `C_e`: predicate-geometry compatibility from `T_e` and predicate-independent `G_e`.
- `Q_e`: evidence quality / observability from mesh, point, and multiview availability.
- `p_obs`: whether the current evidence is sufficient for accept/reject.
- `p_rel`: accept vs reject only after `p_obs = 1`.

Label policy:

- `accept`: visual/mesh evidence supports the candidate predicate.
- `reject`: visual/mesh evidence contradicts the predicate or supports a better counter relation.
- `abstain`: evidence is insufficient, ambiguous, occluded, or ontology-overlapping.

Important constraint:

```text
No-GT is never a negative label by itself.
```

`supported by` is treated as a broad/superordinate support predicate. It is not automatically a
clean negative for `standing on`; if a more specific relation is visually better, that is recorded
through `review_counter_relation`.

## Packet Boundary

Visible packet fields include relation text, mesh/point/multiview evidence paths, visible
contact/pose/coverage summaries, and blank review fields.

Hidden during label creation:

```text
source_score
source_rank
rank_band
source_id
queue_kind
geometry_status
p_geom_valid
label_match_status
construction_bucket
hidden_stratum
```

## Planned Size

```text
target_total_rows = 480
minimum_total_rows = 360
minimum_per_predicate = 80
minimum_accept = 80
minimum_reject = 80
minimum_abstain = 60
```

The plan intentionally asks for mixed strata, not positive-only mining:

- clear accept anchors.
- same-family hard rejects.
- coverage/observability stress rows.
- hard-surface capped controls.
- same-scene/class/coverage matched counter examples.

## Gates

Pre-materialization gates:

- train-only source.
- visible packet excludes hidden/source/construction fields.
- predicate and class-pair capacity passes.
- scan, hard-surface, and subject-object class-pair caps pass.

Post-label gates:

- accept/reject/abstain class mass passes.
- predicate/class/source-only shortcut probes stay below threshold.
- same-family hard contrast remains after label lock.
- `p_obs`/`Q_e` are separated from `p_rel`.

## Outputs

Key generated files:

- `artifacts/compatibility_dataset_v3_support_contact_visual_mesh_audit_target_plan/audit_target_contract.json`
- `artifacts/compatibility_dataset_v3_support_contact_visual_mesh_audit_target_plan/runner_contract.json`
- `artifacts/compatibility_dataset_v3_support_contact_visual_mesh_audit_target_plan/visible_packet_schema.csv`
- `artifacts/compatibility_dataset_v3_support_contact_visual_mesh_audit_target_plan/hidden_field_policy.csv`
- `artifacts/compatibility_dataset_v3_support_contact_visual_mesh_audit_target_plan/label_policy.csv`
- `artifacts/compatibility_dataset_v3_support_contact_visual_mesh_audit_target_plan/target_axes.csv`
- `artifacts/compatibility_dataset_v3_support_contact_visual_mesh_audit_target_plan/sampling_plan.csv`
- `artifacts/compatibility_dataset_v3_support_contact_visual_mesh_audit_target_plan/shortcut_gate_plan.csv`
- `artifacts/compatibility_dataset_v3_support_contact_visual_mesh_audit_target_plan/feature_boundary.csv`
- `artifacts/compatibility_dataset_v3_support_contact_visual_mesh_audit_target_plan/reviewer_risks.csv`
- `artifacts/compatibility_dataset_v3_support_contact_visual_mesh_audit_target_plan/report.md`

## Next

```text
compatibility_dataset_v3_support_contact_visual_mesh_audit_source_inventory
```

This next step should inventory actual candidate rows and packet sources under the visible/hidden
field split fixed here.
