# Rules v1 Report

Created at: `2026-04-30T03:09:53.056243+00:00`
Scan id: `f62fd5fd-9a3f-2f44-883a-1e5cf819608e`
Rule version: `h001-rules-v1`

## Validation

- Passed: `True`
- Errors: `0`
- Warnings: `4`

## Counts

- `all_edge_count`: `772`
- `input_edge_count`: `772`
- `point_evidence_records`: `32`
- `support_contact_edge_count`: `32`
- `floor_support_edge_count`: `16`
- `floor_support_satisfied_count`: `13`
- `point_evidence_available_count`: `32`
- `point_evidence_missing_count`: `0`
- `v1_review_queue_count`: `13`
- `primary_metric_denominator`: `141`

## Support Contact Status

- `satisfied`: `19`
- `uncertain`: `1`
- `violated`: `12`

## Support Contact Transitions

- `v0_uncertain_to_v1_satisfied`: `10`
- `v0_uncertain_to_v1_violated`: `3`
- `v0_violated_to_v1_satisfied`: `9`
- `v0_violated_to_v1_uncertain`: `1`
- `v0_violated_to_v1_violated`: `9`

## Interpretation

- This is a one-scan smoke test, not benchmark evidence.
- `support_contact` now uses point/local-surface evidence as the primary verifier signal.
- Remaining `uncertain` and `violated` support/contact edges require review before qualitative thesis use.

## Next Action

Review triage is recorded in `v1_review_report.md`.

Next: prepare a minimal visual inspection pass before multi-scan replication.
