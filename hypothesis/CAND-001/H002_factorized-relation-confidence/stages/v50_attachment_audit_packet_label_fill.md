# V50 Attachment Audit Packet Label Fill

## Purpose

v49에서 leakage review를 통과한 `attachment_deferred` audit packet을 사용해
reviewer-visible packet label을 채운다. 이 단계는 label materialization이지 posterior
evidence가 아니다.

Input:

```text
artifacts/train_rga_full/open3dsg_train_full/rga/
  reliability_target_v19_attachment_deferred_independent_evidence_audit_packet_materialization/
  reliability_target_v19_attachment_deferred_independent_evidence_audit_packet_leakage_review/
```

Output:

```text
artifacts/train_rga_full/open3dsg_train_full/rga/
  reliability_target_v19_attachment_deferred_independent_evidence_audit_packet_label_fill/
```

Script:

```text
tools/reliability_target_v19_attachment_deferred_independent_evidence_audit_packet_label_fill.py
```

## Result

```text
status = h002_reliability_target_v19_attachment_deferred_independent_evidence_audit_packet_label_filled_codex_visible_packet
next_todo = reliability_target_v19_attachment_deferred_independent_evidence_audit_packet_label_ingestion
rows = 240
validation_errors = 0
hidden_manifest_read = false
posterior_smoke_allowed = false
```

Label distribution:

```text
review_relation_reliability =
  accept_reliable_attachment: 26
  reject_unreliable_attachment: 99
  abstain_uncertain: 53
  diagnostic_connected_possible: 15
  diagnostic_connected_ambiguous: 47

review_geometry_support =
  supports: 41
  contradicts: 99
  ambiguous: 100

review_uncertainty =
  low: 28
  medium: 135
  high: 15
  diagnostic_only: 62
```

Primary binary target preview:

```text
binary_primary_usable_rows = 125
primary_positive_rows = 26
primary_negative_rows = 99
diagnostic_connected_rows = 62
abstain_rows = 53
```

Predicate split:

```text
attached to:
  accept = 9
  reject = 53
  abstain = 20

hanging on:
  accept = 17
  reject = 46
  abstain = 33

connected to:
  diagnostic_possible = 15
  diagnostic_ambiguous = 47
```

## Boundary

- Train-only H002 hypothesis artifact.
- Hidden manifest was not read during label fill.
- Source path, scan id, v18 labels, geometry status, rank/machine hint, semantic score/rank, and
  `p_geom_valid` were not used.
- Packet markdown and packet-local image availability were used only as reviewer-visible audit
  evidence.
- `connected to` remains diagnostic-only.
- No posterior smoke, validation/test use, or paper evidence promotion occurred.
- H001 and paper artifacts were not modified.

## Interpretation

v50 completes the packet label-fill gate, but it does not unlock posterior smoke by itself.
The primary binary preview is `26/99`, so positive-sparse risk remains. This could mean:

1. The v19 packet label policy is intentionally conservative.
2. The current selected attachment rows are dominated by unreliable/support/proximity/confound cases.
3. The next ingestion and target-independence audit may again block posterior smoke if class mass or
   shortcut controls fail.

Therefore the correct next step is label ingestion, not posterior execution. Ingestion must join the
filled packet labels with hidden audit metadata and then audit class mass, predicate/tier balance,
endpoint/object-label shortcut risk, and whether T1/T2 evidence tiers create an accidental shortcut.

## Next

```text
reliability_target_v19_attachment_deferred_independent_evidence_audit_packet_label_ingestion
```
