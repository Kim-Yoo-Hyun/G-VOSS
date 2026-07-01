# Attachment Independent Positive Anchor Label Fill V1

Created: 2026-06-25 KST

## Purpose

Fill independent accept/reject/abstain review fields for the `560` label-ready positive-anchor
attachment packets from
`attachment_independent_positive_anchor_packet_materialization_v1`.

This stage creates a train-only audit target candidate. It does not train a posterior, use
validation/test data, promote paper evidence, or modify H001 artifacts.

## Runner

```bash
python hypothesis/CAND-001/H002_factorized-relation-confidence/tools/attachment_independent_positive_anchor_label_fill_v1.py
```

## Outputs

```text
artifact_root = artifacts/attachment_independent_positive_anchor_label_fill_v1/
summary = artifacts/attachment_independent_positive_anchor_label_fill_v1/summary.json
filled_visible_review_sheet = artifacts/attachment_independent_positive_anchor_label_fill_v1/filled_visible_review_sheet.csv
label_decisions = artifacts/attachment_independent_positive_anchor_label_fill_v1/label_decisions.jsonl
validation_errors = artifacts/attachment_independent_positive_anchor_label_fill_v1/validation_errors.jsonl
```

## Label Source

```text
reviewer_id = codex_visible_packet_proxy_labeler_v1_user_requested
label_policy = visible_endpoint_packet_conservative_attachment_v1
hidden_manifest_read = false
used_source_score_or_rank = false
used_proxy_role_or_cell_id = false
used_p_geom_valid = false
used_validation_or_test = false
```

The label fill uses reviewer-visible relation fields and packet availability from the materialized
packet sheet. It does not read the materialized hidden manifest. The labels are proxy audit labels
that must be checked by ingestion and target-independence audit before any posterior smoke.

## Result

```text
status = h002_attachment_independent_positive_anchor_label_fill_v1_completed
rows = 560
validation_errors = 0
next_todo = attachment_independent_positive_anchor_label_ingestion_v1
```

Reliability distribution:

```text
accept_reliable = 60
reject_unreliable = 246
abstain_uncertain = 254
```

Predicate-level distribution:

```text
attached to:
  accept_reliable = 30
  reject_unreliable = 95
  abstain_uncertain = 113

hanging on:
  accept_reliable = 30
  reject_unreliable = 151
  abstain_uncertain = 61

connected to:
  abstain_uncertain = 80
```

Primary binary preview:

```text
primary_binary_preview_rows = 306
primary_positive_rows = 60
primary_negative_rows = 246
connected_diagnostic_rows = 80
```

Auxiliary labels:

```text
geometry_support:
  supported = 60
  unsupported = 246
  uncertain = 254

endpoint_identity:
  clear_endpoint_identity = 449
  uncertain_endpoint_identity = 111

coverage:
  sufficient = 558
  limited = 2

uncertainty:
  none = 255
  visual_ambiguous = 97
  ontology_ambiguous = 128
  functional_connection_ambiguous = 80
```

## Interpretation

The positive-anchor repair achieved the minimum primary positive gate exactly:

```text
post_audit_min_accept_positive = 60
actual_primary_positive = 60
```

This is a useful improvement over the previous `17/91` independent attachment target, but it is not
yet sufficient for posterior smoke. The next step must ingest the labels with hidden/control
provenance and test whether the target is still identifiable after controlling predicate, endpoint,
rank, packet construction, and mixed-strata axes.

## Boundary

- train-only H002 artifact;
- no validation/test data;
- no model training;
- no posterior smoke yet;
- no paper evidence promotion;
- no H001 artifact modification;
- `connected to` remains diagnostic and is not part of the primary binary target.

