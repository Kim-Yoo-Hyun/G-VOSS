# V51 Attachment Audit Packet Label Ingestion

## Purpose

v50에서 채운 `attachment_deferred` visible-packet labels를 label-lock 이후 hidden
manifest와 join해 target artifacts를 만든다. 이 단계는 target construction과 shortcut
preview를 위한 ingestion이며, posterior smoke를 실행하지 않는다.

Input:

```text
artifacts/train_rga_full/open3dsg_train_full/rga/
  reliability_target_v19_attachment_deferred_independent_evidence_audit_packet_label_fill/
  reliability_target_v19_attachment_deferred_independent_evidence_audit_packet_materialization/
```

Output:

```text
artifacts/train_rga_full/open3dsg_train_full/rga/
  reliability_target_v19_attachment_deferred_independent_evidence_audit_packet_label_ingestion/
```

Script:

```text
tools/reliability_target_v19_attachment_deferred_independent_evidence_audit_packet_label_ingestion.py
```

## Result

```text
status = h002_reliability_target_v19_attachment_deferred_independent_evidence_audit_packet_label_ingested_positive_sparse_with_probe_risk
next_todo = reliability_target_v19_attachment_deferred_independent_evidence_audit_packet_target_independence_audit
rows = 240
validation_errors = 0
posterior_smoke_allowed = false
```

Target rows:

```text
multiclass_rows = 240
primary_binary_rows = 125
connected_diagnostic_rows = 62
geometry_support_rows = 140
uncertainty_rows = 240
evidence_tier_rows = 240
abstain_rows = 115
```

Target distribution:

```text
review_relation_reliability =
  accept_reliable_attachment: 26
  reject_unreliable_attachment: 99
  abstain_uncertain: 53
  diagnostic_connected_possible: 15
  diagnostic_connected_ambiguous: 47

primary_binary_target = {1: 26, 0: 99}
geometry_support_target = {1: 41, 0: 99}
connected_diagnostic_target =
  diagnostic_connected_possible: 15
  diagnostic_connected_ambiguous: 47
```

Target viability:

```text
minimum_per_class_for_posterior = 50
reliability_positive_rows = 26
reliability_negative_rows = 99
class_mass_pass = false
quick_probe_risk_flags = 43
same_scan_mixed_primary_binary_groups = 4
same_visible_pair_mixed_primary_binary_groups = 0
same_predicate_mixed_primary_binary_groups = 2
same_evidence_tier_mixed_primary_binary_groups = 2
```

## Interpretation

v51 confirms that label ingestion itself is clean, but the target is not posterior-ready.
The main blockers are:

1. Primary binary target is positive-sparse: `26/99`.
2. Quick probe flags `43` shortcut risks.
3. Same visible-pair mixed primary binary groups are `0`, so visible endpoint identity can still
   over-explain target labels.
4. `connected to` remains diagnostic-only and cannot be used to inflate primary binary class mass.

Therefore the next step is a full target-independence audit. Posterior smoke remains blocked.

## Boundary

- Train-only H002 hypothesis artifact.
- Hidden manifest was read only after visible label fill was locked.
- Hidden scan/source fields, packet paths, image source paths, evidence tier, and packet role are
  audit/control fields, not deployable model inputs.
- No validation/test rows were used.
- No posterior was trained or evaluated.
- Multi-view and mesh remain audit/confirmation evidence only.
- H001 and paper artifacts were not modified.

## Next

```text
reliability_target_v19_attachment_deferred_independent_evidence_audit_packet_target_independence_audit
```
