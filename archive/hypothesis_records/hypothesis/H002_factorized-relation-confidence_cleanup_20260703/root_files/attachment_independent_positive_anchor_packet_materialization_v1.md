# Attachment Independent Positive Anchor Packet Materialization V1

Created: 2026-06-25 KST

## Purpose

Materialize reviewer-facing multi-view and mesh evidence packets for the `560` train-only
mixed-strata attachment candidates selected by
`attachment_independent_positive_anchor_candidate_mining_v1`.

This stage prepares evidence for independent label fill. It does not fill labels, train a
posterior, promote paper evidence, use validation/test data, or modify H001 artifacts.

## Runner

```bash
python hypothesis/CAND-001/H002_factorized-relation-confidence/tools/attachment_independent_positive_anchor_packet_materialization_v1.py
```

## Outputs

```text
artifact_root = artifacts/attachment_independent_positive_anchor_packet_materialization_v1/
summary = artifacts/attachment_independent_positive_anchor_packet_materialization_v1/summary.json
visible_review_sheet_with_packets = artifacts/attachment_independent_positive_anchor_packet_materialization_v1/visible_review_sheet_with_packets.csv
packet_manifest = artifacts/attachment_independent_positive_anchor_packet_materialization_v1/packet_manifest.jsonl
materialized_hidden_manifest = artifacts/attachment_independent_positive_anchor_packet_materialization_v1/materialized_hidden_manifest.jsonl
label_ready_manifest = artifacts/attachment_independent_positive_anchor_packet_materialization_v1/label_ready_manifest.jsonl
visible_leakage_hits = artifacts/attachment_independent_positive_anchor_packet_materialization_v1/visible_leakage_hits.jsonl
```

## Result

```text
status = h002_attachment_independent_positive_anchor_packet_materialization_v1_ready_for_label_fill
packet_rows = 560
packet_status_counts = ready: 560
label_ready_rows = 560
non_ready_rows = 0
validation_errors = 0
visible_leakage_hits = 0
next_todo = attachment_independent_positive_anchor_label_fill_v1
```

Coverage:

```text
subject_image_rows = 560 / 560
object_image_rows = 560 / 560
contact_sheet_rows = 560 / 560
mesh_packet_rows = 560 / 560
total_subject_images = 2174
total_object_images = 2204
```

Query-level readiness:

```text
Q1_hanging_on_positive_anchor = 116 ready
Q2_hanging_on_hard_negative = 120 ready
Q3_attached_to_structural_positive_anchor = 118 ready
Q4_attached_to_hard_negative = 113 ready
Q5_connected_near_or_overlap_diagnostic = 40 ready
Q5_connected_far_or_functional_ambiguous_diagnostic = 40 ready
Q6_primary_uncertain_buffer = 13 ready
```

## Boundary

- Train split only.
- Multi-view and mesh evidence are audit evidence only at this stage.
- Source score, rank, construction proxy, cell id, GT-match, scan id, and object ids remain hidden
  from reviewer-facing surfaces.
- Visible packet leakage scan passed with `0` hits.
- The output is label-fill-ready, not posterior-smoke-ready.

## Interpretation

The packet materialization blocker is cleared. The selected positive-anchor batch now has complete
reviewer-facing visual/mesh evidence for all `560` rows, so the next meaningful step is to fill
independent accept/reject/abstain labels from these packets and then run ingestion plus target
independence audit.

