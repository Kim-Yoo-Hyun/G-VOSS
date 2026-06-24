# V57 Attachment Endpoint-Balanced Source Inventory

## Purpose

v56에서 생성한 320-row endpoint-balanced candidate set이 label/audit evidence를 만들 수 있을
정도로 multi-view/sequence/mesh source를 갖는지 확인한다.

이 단계는 source inventory이며 label fill, audit packet materialization, posterior smoke가 아니다.

Input:

```text
artifacts/train_rga_full/open3dsg_train_full/rga/
  reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_candidate_mining/
local_dataset/3RScan/scans/
```

Output:

```text
artifacts/train_rga_full/open3dsg_train_full/rga/
  reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_source_inventory/
```

Script:

```text
tools/reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_source_inventory.py
```

## Result

```text
status = h002_reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_source_inventory_ready_for_audit_packet_plan
source_inventory_gate_pass = true
next_todo = reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_audit_packet_plan
validation_errors = 0
posterior_smoke_allowed = false
multi_view_as_model_input = false
```

## Counts

```text
rows = 320
primary_rows = 256
primary_both_have_crop_rows = 256
primary_possible_covisible_or_same_view_rows = 256
primary_audit_ready_rows = 256
connected_diagnostic_rows = 64
connected_diagnostic_audit_ready_rows = 64
audit_ready_rows = 320
both_have_crop_rows = 320
strong_pair_visual_ready_rows = 75
```

Visual context:

```text
same_frame_covisible_strong = 75
same_view_rank_weak_proxy = 245
```

Audit-ready state:

```text
strong_pair_visual_audit_ready = 75
individual_visual_plus_mesh_audit_ready = 245
```

Scan-level source availability:

```text
unique_scans = 247
scan_exists = 247
multi_view_exists = 247
sequence_exists = 247
mesh_ready = 247
```

## Gate

```text
primary_rows_with_subject_and_object_crops_min_200 = true
primary_rows_with_possible_covisible_or_same_view_context_min_120 = true
attached_and_hanging_each_audit_ready_min_50 = true
connected_diagnostic_audit_ready_min_32 = true
```

## Interpretation

v57 confirms that the v20 candidate set has enough independent source evidence for an audit packet
plan. However, only 75/320 rows have strong same-frame co-visible evidence; the remaining 245 rows
are individual-view-plus-mesh audit-ready. Therefore the next audit packet should preserve this
tier distinction instead of treating all rows as equally strong visual evidence.

This still does not make the target posterior-ready. Labels, ingestion, and target-independence audit
are still required.

## Boundary

- Train-only H002 hypothesis artifact.
- No validation/test rows were used.
- No labels were filled.
- No posterior was trained or evaluated.
- Multi-view/mesh is audit/confirmation evidence only, not model input.
- H001 and paper artifacts were not modified.

## Next

```text
reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_audit_packet_plan
```
