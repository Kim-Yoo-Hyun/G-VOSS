# Compatibility Dataset V3 Support/Contact Pose-Conditioned Candidate Materialization

## Status

```text
status = h002_compatibility_dataset_v3_support_contact_pose_conditioned_candidate_materialization_ready_for_schema_shortcut_audit
selected_path = materialize_pose_conditioned_support_contact_candidates_from_frozen_anchor_preview
validation_errors = 0
next_todo = compatibility_dataset_v3_support_contact_pose_conditioned_schema_shortcut_audit
```

## Purpose

This stage materializes the frozen support/contact pose-conditioned target into concrete candidate
rows. It does not run learned smoke, train a model, select additional anchors, change thresholds,
or use validation/test rows.

The target is the same-`G_e` predicate flip:

```text
anchor G_e + lying on
anchor G_e + standing on
```

For each anchor, the two rows share identical geometry evidence. The target label changes only
with the predicate-conditioned pose interpretation.

## Inputs

```text
plan = artifacts/compatibility_dataset_v3_support_contact_pose_conditioned_candidate_materialization_plan/
frozen_anchor_preview = artifacts/compatibility_dataset_v3_support_contact_pose_conditioned_capacity_scan/anchor_candidate_preview.jsonl
```

The materializer reuses the frozen `200` anchors exactly.

## Outputs

```text
artifact_root = artifacts/compatibility_dataset_v3_support_contact_pose_conditioned_candidate_materialization/
candidate_rows = candidate_rows.jsonl
smoke_ready_candidate_view = smoke_ready_candidate_view.jsonl
hidden_manifest = hidden_manifest.jsonl
schema_shortcut_precheck = schema_shortcut_precheck.csv
manifest = manifest.json
summary = summary.json
validation_errors = validation_errors.jsonl
```

## Counts

```text
anchor_groups = 200
candidate_rows = 400
smoke_ready_rows = 400
hidden_manifest_rows = 400
positive_rows = 200
negative_rows = 200
lying_on_rows = 200
standing_on_rows = 200
lying_like_anchors = 100
upright_anchors = 100
hard_surface_rows = 0
semseg_complete_rows = 400
point_complete_rows = 240
validation_errors = 0
```

`point_complete_rows` is lower than `candidate_rows` because aligned PLY contact features are
optional evidence. Missing point-contact evidence is represented through `Q_e`, not treated as a
materialization failure.

## Model-Safe Fields

The smoke-ready candidate view contains only:

```text
T_e
Z_e_safe
G_e_mesh_pose_contact
Q_e_safe
target_y
cv_group_id
row_id
```

Hidden/audit-only fields are kept out of the smoke-ready feature surface:

```text
scan_id
subject_id
object_id
visible_pair
hard_surface_pair
source_predicates
queue_kinds
anchor_pose_state
G_e_hash
```

Precheck result:

```text
row_count = pass
anchor_count = pass
rows_per_anchor = pass
label_balance = pass
predicate_counts = pass
anchor_state_counts = pass
same_G_e_pair_integrity = pass
paired_label_integrity = pass
smoke_ready_hidden_token_absent = pass
hard_surface_rows = pass
learned_smoke_blocked = pass
```

## Interpretation

This completes the row-level materialization needed for the support/contact pose-conditioned
compatibility target. The artifact is still not paper evidence. It is a train-only hypothesis-stage
candidate dataset that must pass a formal schema/shortcut audit before any learned smoke runner is
allowed.

Next:

```text
compatibility_dataset_v3_support_contact_pose_conditioned_schema_shortcut_audit
```
