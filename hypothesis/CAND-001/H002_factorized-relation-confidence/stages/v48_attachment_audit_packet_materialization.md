# V48 Attachment Audit Packet Materialization

Date: 2026-06-23 KST

## Purpose

v47 audit packet plan을 실제 packet directory와 reviewer-visible sheet로 materialize했다.

이 단계는 packet materialization만 수행한다. 새 label을 채우거나 posterior smoke를 실행하지 않았다.

## Artifact

```text
artifacts/train_rga_full/open3dsg_train_full/rga/
  reliability_target_v19_attachment_deferred_independent_evidence_audit_packet_materialization/
    summary.json
    report.md
    visible_review_sheet.tsv
    packet_index.jsonl
    materialized_hidden_manifest.jsonl
    visible_leakage_hits.jsonl
    validation_errors.jsonl
    packets/
```

Script:

```text
tools/reliability_target_v19_attachment_deferred_independent_evidence_audit_packet_materialization.py
```

## Status

```text
status = h002_reliability_target_v19_attachment_deferred_independent_evidence_audit_packet_materialization_ready_for_leakage_review
next_todo = reliability_target_v19_attachment_deferred_independent_evidence_audit_packet_leakage_review
validation_errors = 0
visible_leakage_hits = 0
posterior_smoke_allowed = false
multi_view_as_model_input = false
```

## Counts

```text
visible_review_rows = 240
packet_dirs = 240
materialized_hidden_manifest_rows = 240
total_materialized_images = 4466
```

Packet roles:

```text
primary_attachment_reliability_candidate = 160
connected_diagnostic_only = 62
uncertainty_or_coverage_audit_only = 18
```

Evidence tiers:

```text
T1_strong_pair_visual = 43
T2_individual_visual_plus_mesh = 197
```

Primary evidence tiers:

```text
T1_strong_pair_visual = 31
T2_individual_visual_plus_mesh = 129
```

## Materialization Policy

Visible packet assets use neutral packet-local names such as:

```text
subject_crop_01.jpg
subject_view_01.jpg
object_crop_01.jpg
object_view_01.jpg
```

Original asset paths, scan ids, subgraph ids, subject/object instance ids, and original filenames
remain only in `materialized_hidden_manifest.jsonl`.

## Interpretation

The audit packet set is ready for a formal leakage review. The internal materialization script already
reports `visible_leakage_hits = 0`, but the next stage should still independently inspect visible
sheet/markdown filenames and fields before any label fill.

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
reliability_target_v19_attachment_deferred_independent_evidence_audit_packet_leakage_review
```
