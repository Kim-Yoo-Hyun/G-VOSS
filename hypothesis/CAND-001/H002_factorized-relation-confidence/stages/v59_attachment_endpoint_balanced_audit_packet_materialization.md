# V59 Attachment Endpoint-Balanced Audit Packet Materialization

## Purpose

v58 audit packet plan을 실제 packet directory, neutral packet-local image names, reviewer-visible
sheet, hidden materialized manifest로 materialize한다.

이 단계는 packet materialization만 수행한다. Label fill, label ingestion, target-independence
audit, posterior smoke는 아직 수행하지 않는다.

Input:

```text
artifacts/train_rga_full/open3dsg_train_full/rga/
  reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_audit_packet_plan/
  match_rows.jsonl
```

Output:

```text
artifacts/train_rga_full/open3dsg_train_full/rga/
  reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_audit_packet_materialization/
```

Script:

```text
tools/reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_audit_packet_materialization.py
```

## Result

```text
status = h002_reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_audit_packet_materialization_ready_for_leakage_review
next_todo = reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_audit_packet_leakage_review
validation_errors = 0
visible_leakage_hits = 0
posterior_smoke_allowed = false
multi_view_as_model_input = false
```

## Counts

```text
visible_review_rows = 320
packet_dirs = 320
materialized_hidden_manifest_rows = 320
total_materialized_images = 5836
primary_attachment_reliability_candidate = 256
connected_diagnostic_only = 64
T1_strong_pair_visual = 75
T2_individual_visual_plus_mesh = 245
primary_T1_strong_pair_visual = 62
primary_T2_individual_visual_plus_mesh = 194
```

Existing GT match axis:

```text
gt_match_axis_joined_rows = 320
exact_match = 1
family_match = 5
pair_has_other_predicate = 81
no_gt_for_pair = 233
```

## Direction Preserved

v59 preserves the two-axis evaluation plan:

```text
primary target = future human-audited reliability label
auxiliary axis = existing GT relation match
```

The future mismatch analysis must compare:

```text
GT match & reliability accept
GT match & reliability reject
No GT & reliability accept
No GT & reliability reject
Abstain
```

This keeps H002 from collapsing back into ordinary GT-only relation prediction. Existing GT is
retained, but it is used as an auxiliary analysis axis rather than the main reliability label.

## Materialization Policy

Visible packet assets use neutral names such as:

```text
subject_crop_01.jpg
subject_view_01.jpg
object_crop_01.jpg
object_view_01.jpg
```

The following stay hidden:

```text
source paths
scan/subgraph/instance ids
proxy role and selection route
typed witness and construction metadata
geometry_status and p_geom_valid
rank and source score
existing GT match fields
```

## Boundary

- Train-only H002 hypothesis artifact.
- No validation/test rows were used.
- No labels were filled.
- No posterior was trained or evaluated.
- Multi-view/mesh is audit/confirmation evidence only, not model input.
- H001 and paper artifacts were not modified.

## Next

```text
reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_audit_packet_leakage_review
```
