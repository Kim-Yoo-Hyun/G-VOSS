# H002 R7 Attachment Observability Class-Pair Repair Candidate Mining

## Status

```text
artifact_root = artifacts/compatibility_dataset_v3_attachment_observability_class_pair_repair_candidate_mining/
status = h002_compatibility_dataset_v3_attachment_observability_class_pair_repair_candidate_mining_ready_for_packet_materialization_plan
validation_errors = 0
next_todo = compatibility_dataset_v3_attachment_observability_class_pair_repair_packet_materialization_plan
```

## Selection

The mining step selected controlled train-only candidates from exact
`predicate_label + subject_label + object_label` cells that contain both
accept-proxy and reject-proxy rows.

| Predicate | Accept Proxy | Reject Proxy | Uncertain Proxy | Total |
| --- | ---: | ---: | ---: | ---: |
| `attached to` | 80 | 120 | 40 | 240 |
| `hanging on` | 80 | 120 | 40 | 240 |
| `connected to` | 0 | 0 | 0 | 0 |

Summary:

- selected rows: `480`
- unique scans: `340`
- unique exact class pairs: `160`
- mixed exact class-pair groups: `attached to 80`, `hanging on 80`
- role counts: accept proxy `160`, reject proxy `240`, uncertain proxy `80`
- geometry buckets: far `240`, mid/ambiguous `80`, near/overlap-family `160`
- coverage: joined no-uncertainty `279`, joined with uncertainty `201`

## Outputs

- `candidate_rows_internal.jsonl`: hidden/internal train-only candidate rows.
- `packet_request_manifest.jsonl`: rows required for the next packet
  materialization plan.
- `quota_audit.csv`: target-vs-selected quota audit.
- `selection_group_manifest.csv`: exact predicate/class-pair seed cells used for
  mixed candidate selection.
- `summary.json`, `report.md`, `validation_errors.jsonl`.

## Interpretation

The previous R7 shortcut blocker can be addressed at the candidate source level:
both primary predicates now have selected accept/reject candidates inside mixed
exact class-pair cells. This does not yet validate the H002 observability route.
It only prepares a controlled candidate pool for packet materialization and later
label ingestion.

The object-label distribution is intentionally anchor-heavy (`wall`, `ceiling`,
`door`, `shelf`, `window`, etc.) because attachment/hanging relations require
anchoring structures. This should be audited again after label ingestion because
object-label and anchor priors may still be predictive.

## Boundary

- Train-only candidate mining.
- No validation/test use.
- No H001 artifacts modified.
- No human labels filled or ingested.
- No packet images/mesh/crops generated.
- No model-safe rows or learned smoke.
- Proxy role, geometry bucket, coverage proxy, GT match status, source rank, and
  source confidence are hidden construction/audit fields, not model input.

