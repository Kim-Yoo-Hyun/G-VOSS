# V52 Attachment Audit Packet Target Independence

## Purpose

v51에서 생성한 `attachment_deferred` v19 packet target이 posterior smoke로 넘어갈 수
있는지 class mass와 shortcut-independence 관점에서 검증한다.

Input:

```text
artifacts/train_rga_full/open3dsg_train_full/rga/
  reliability_target_v19_attachment_deferred_independent_evidence_audit_packet_label_ingestion/
```

Output:

```text
artifacts/train_rga_full/open3dsg_train_full/rga/
  reliability_target_v19_attachment_deferred_independent_evidence_audit_packet_target_independence_audit/
```

Script:

```text
tools/reliability_target_v19_attachment_deferred_independent_evidence_audit_packet_target_independence_audit.py
```

## Result

```text
status = h002_reliability_target_v19_attachment_deferred_audit_packet_target_independence_audit_blocked_positive_sparse_and_shortcut_risk
next_todo = reliability_target_v19_attachment_deferred_independent_evidence_audit_packet_path_decision_after_audit
rows = 240
validation_errors = 0
posterior_smoke_allowed = false
```

Primary target:

```text
relation_binary_rows = 125
relation_binary_counts = {1: 26, 0: 99}
relation_class_mass_pass = false
relation_strict_clear_slices = 0
relation_diagnostic_clear_slices = 0
```

Auxiliary/diagnostic targets:

```text
geometry_support_rows = 140
geometry_support_counts = {1: 41, 0: 99}

connected_diagnostic_rows = 62
connected_diagnostic_counts =
  diagnostic_connected_possible: 15
  diagnostic_connected_ambiguous: 47
```

Shortcut audit:

```text
full_quick_probe_risk_flags = 56
slice_blocking_risk_flags = 1185
slice_audit_rows = 144
slice_risk_rows = 2592
```

Dominant risk examples:

```text
relation_binary subject_object_visible_pair accuracy = 1.000
relation_binary scan_id_hidden accuracy = 0.968
relation_binary subgraph_id_hidden accuracy = 0.992
relation_binary primary_reason_v19 accuracy = 1.000
geometry_support_binary subject_object_visible_pair accuracy = 0.971
connected_diagnostic subject_object_visible_pair accuracy = 1.000
```

## Interpretation

v52 blocks posterior smoke for two separate reasons.

1. Class mass fails. The primary target has only 26 positive rows against the predeclared
   minimum-per-class 50 gate.
2. Shortcut risk remains. Endpoint identity, scan/subgraph grouping, and label-construction reason
   can explain the target too easily.

This does not mean the H002 direction is false. It means the current v19 packet target is still not a
method-evaluation target. The independent visual/mesh packet helped label provenance, but it did not
create a balanced, shortcut-controlled reliability target.

## Boundary

- Train-only H002 hypothesis artifact.
- No validation/test rows were used.
- No posterior was trained or evaluated.
- Hidden fields, evidence tier, packet role, scan/subgraph ids, and packet paths are audit/control
  fields only, not model inputs.
- Multi-view and mesh remain audit/confirmation evidence only.
- H001 and paper artifacts were not modified.

## Next

```text
reliability_target_v19_attachment_deferred_independent_evidence_audit_packet_path_decision_after_audit
```
