# V46 Attachment Source Inventory

Date: 2026-06-23 KST

## Purpose

v45에서 정의한 independent evidence contract가 실제 local source에서 실행 가능한지 확인했다.
대상은 v18 attachment rows 전체 240개이며, 새 label을 채우거나 posterior smoke를 실행하지 않았다.

Inventory는 다음만 측정한다.

```text
subject/object crop availability
same-frame or same-view-rank visual context
sequence availability
mesh/point-cloud asset availability
audit-ready state
missing reason
```

## Artifact

```text
artifacts/train_rga_full/open3dsg_train_full/rga/
  reliability_target_v19_attachment_deferred_independent_evidence_source_inventory/
    summary.json
    report.md
    inventory_rows.jsonl
    inventory_table.csv
    scan_summary.json
    validation_errors.jsonl
```

Script:

```text
tools/reliability_target_v19_attachment_deferred_independent_evidence_source_inventory.py
```

## Status

```text
status = h002_reliability_target_v19_attachment_deferred_independent_evidence_source_inventory_ready
next_todo = reliability_target_v19_attachment_deferred_independent_evidence_audit_packet_plan
validation_errors = 0
source_inventory_gate_pass = true
posterior_smoke_allowed = false
multi_view_as_model_input = false
```

## Main Counts

```text
rows = 240
primary_rows = 160
primary_both_have_crop_rows = 160
primary_possible_covisible_or_same_view_rows = 160
primary_audit_ready_rows = 160
strong_pair_visual_ready_rows = 43
```

By visual context:

```text
same_frame_covisible_strong = 43
same_view_rank_weak_proxy = 197
```

By audit-ready state:

```text
strong_pair_visual_audit_ready = 43
individual_visual_plus_mesh_audit_ready = 197
```

Primary predicate availability:

```text
attached to: rows 80, audit_ready 80, same_frame_strong 17, same_view_rank_weak 63
hanging on: rows 80, audit_ready 80, same_frame_strong 14, same_view_rank_weak 66
```

Scan asset summary:

```text
unique_scans = 202
scan_exists = 202
multi_view_exists = 202
sequence_exists = 202
mesh_ready = 202
```

## Gate Result

```text
primary_rows_with_subject_and_object_crops_min_100 = true
primary_rows_with_possible_covisible_or_same_view_context_min_60 = true
hanging_or_attached_each_audit_ready_min_30 = true
```

## Interpretation

Source availability is sufficient for an audit packet, but not all rows have strong same-frame
co-visible evidence. Most rows have individual subject/object views plus mesh/sequence assets, while
only 43 rows have exact origin-frame overlap.

Therefore the next step should not treat every row as equally visual-confirmed. The audit packet plan
must separate:

```text
strong_pair_visual_audit_ready
individual_visual_plus_mesh_audit_ready
```

The former can support stronger visual confirmation. The latter should be audited as independent
object-identity and mesh/context evidence, not as direct co-visible relation evidence.

## Boundary

This stage does not:

- fill new labels
- mine new candidates
- train posterior
- create deployable multi-view features
- use validation/test data
- modify H001 or paper artifacts

## Next

```text
reliability_target_v19_attachment_deferred_independent_evidence_audit_packet_plan
```
