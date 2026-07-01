# Compatibility Dataset V3 Support/Contact Pose-Conditioned Schema Shortcut Audit

## Status

```text
status = h002_compatibility_dataset_v3_support_contact_pose_conditioned_schema_shortcut_audit_ready_for_sanitized_view_smoke_plan
validation_errors = 0
next_todo = compatibility_dataset_v3_support_contact_pose_conditioned_sanitized_view_smoke_plan
```

## Purpose

This stage audits the 400-row support/contact pose-conditioned candidate dataset before any learned
smoke test. The audit checks whether the target can be solved by schema leakage, hidden
construction fields, or single-field shortcuts.

The important boundary is:

```text
candidate_rows.jsonl = audit/provenance artifact
smoke_ready_view.jsonl = model-input candidate for the next smoke plan
feature_blocks = only model feature root
```

## Inputs

```text
artifact_root = artifacts/compatibility_dataset_v3_support_contact_pose_conditioned_candidate_materialization/
candidate_rows = candidate_rows.jsonl
input_smoke_ready_candidate_view = smoke_ready_candidate_view.jsonl
hidden_manifest = hidden_manifest.jsonl
```

## Outputs

```text
artifact_root = artifacts/compatibility_dataset_v3_support_contact_pose_conditioned_schema_shortcut_audit/
smoke_ready_view = smoke_ready_view.jsonl
smoke_ready_model_view_contract = smoke_ready_model_view_contract.json
shortcut_probes = shortcut_probes.csv
shortcut_probe_details = shortcut_probe_details.jsonl
blocked_field_audit = blocked_field_audit.csv
feature_path_audit = feature_path_audit.csv
group_integrity_audit = group_integrity_audit.csv
summary = summary.json
validation_errors = validation_errors.jsonl
```

## Counts

```text
candidate_rows = 400
smoke_ready_rows = 400
groups = 200
label_counts = {
  0: 200,
  1: 200
}
predicate_counts = {
  lying on: 200,
  standing on: 200
}
validation_errors = 0
```

## Shortcut Result

Allowed model-feature probes:

```text
predicate_label = 0.500
subject_class_label = 0.500
object_class_label = 0.500
subject_object_class_pair = 0.500
source_score_available = 0.500
source_rank_available = 0.500
Q_e flags = 0.500
all single G_e numeric threshold probes = 0.500
allowed_feature_high_or_medium_risk = 0
```

Blocked raw high-risk probes:

```text
raw_row_id = 1.000
target_label_self = 1.000
hidden_pose_state_x_predicate = 1.000
hidden_G_hash_x_predicate = 1.000
```

These high-risk probes are expected and acceptable only because they are excluded from
`feature_blocks`.

## Group Integrity

The audit verified:

```text
groups = 200
rows_per_group = 2
predicates_per_group = lying on + standing on
labels_per_group = one positive + one negative
same_G_e_per_group = true
group_integrity_errors = 0
```

## Interpretation

The target is not solved by a single allowed semantic, geometry, or observability field. This is the
desired schema property for the next smoke step: any learned improvement must come from
predicate-geometry compatibility, not from predicate-only, geometry-only, object-class-only, or
metadata leakage.

Learned smoke is still not run here. The next step should first freeze the sanitized-view smoke
plan and controls.

Next:

```text
compatibility_dataset_v3_support_contact_pose_conditioned_sanitized_view_smoke_plan
```
