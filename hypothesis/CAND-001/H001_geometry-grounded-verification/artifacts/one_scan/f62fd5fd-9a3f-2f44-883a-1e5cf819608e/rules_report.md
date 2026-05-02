# Rule Verifier

Created at: `2026-04-30T03:09:43.421003+00:00`
Scan id: `f62fd5fd-9a3f-2f44-883a-1e5cf819608e`
Geometry source: `semseg_obb_v0`
Rule version: `h001-rules-v0`

## Validation

- Passed: `True`
- Errors: `0`
- Warnings: `3`

## Counts

- `input_edges`: `772`
- `output_edges`: `772`
- `expected_edges`: `772`
- `manual_review_queue`: `30`
- `primary_family_edges`: `148`
- `primary_metric_denominator`: `129`
- `diagnostic_only_edges`: `342`
- `unsupported_edges`: `282`
- `uncertain_edges`: `361`

## Status Counts

- `satisfied`: `108`
- `uncertain`: `361`
- `unsupported`: `282`
- `violated`: `21`

## Predicate Families

- `attachment_deferred`: `19` (unsupported=19)
- `proximity`: `68` (satisfied=68)
- `relative_horizontal`: `342` (uncertain=342)
- `relative_vertical`: `48` (satisfied=40, uncertain=6, violated=2)
- `size_comparison_deferred`: `14` (unsupported=14)
- `support_contact`: `32` (uncertain=13, violated=19)
- `unsupported_first_pass`: `249` (unsupported=249)

## Primary Family Metrics

| Family | Satisfied | Violated | Uncertain | Denominator | Violation rate | Uncertain rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `proximity` | 68 | 0 | 0 | 68 | 0.000 | 0.000 |
| `relative_vertical` | 40 | 2 | 6 | 42 | 0.048 | 0.125 |
| `support_contact` | 0 | 19 | 13 | 19 | 1.000 | 0.406 |

## Top Reason Codes

- `horizontal_frame_not_validated`: `342`
- `horizontal_candidate_matches`: `334`
- `unsupported_predicate`: `249`
- `proximity_distance_within_threshold`: `68`
- `vertical_order_matches`: `40`
- `deferred_predicate_family`: `33`
- `support_contact_requires_manual_inspection`: `32`
- `support_vertical_gap_too_large`: `19`
- `support_object_aabb_too_coarse`: `13`
- `horizontal_candidate_conflicts`: `8`
- `vertical_margin_too_small`: `6`
- `support_projected_overlap_too_low`: `4`

## Manual Review Queue

- Queue size: `30`
- `uncertain` `support_contact` `sofa --standing on--> floor` score=`0.6666666666666666` reason=`support_contact_requires_manual_inspection,support_object_aabb_too_coarse`
- `uncertain` `support_contact` `table --standing on--> floor` score=`0.6666666666666666` reason=`support_contact_requires_manual_inspection,support_object_aabb_too_coarse`
- `uncertain` `support_contact` `cabinet --standing on--> floor` score=`0.6666666666666666` reason=`support_contact_requires_manual_inspection,support_object_aabb_too_coarse`
- `uncertain` `support_contact` `cabinet --standing on--> floor` score=`0.6666666666666666` reason=`support_contact_requires_manual_inspection,support_object_aabb_too_coarse`
- `uncertain` `support_contact` `chair --standing on--> floor` score=`0.6666666666666666` reason=`support_contact_requires_manual_inspection,support_object_aabb_too_coarse`
- `violated` `support_contact` `cabinet --standing on--> floor` score=`0.3333333333333333` reason=`support_contact_requires_manual_inspection,support_projected_overlap_too_low,support_vertical_gap_too_large`
- `violated` `support_contact` `stool --standing on--> floor` score=`0.3333333333333333` reason=`support_contact_requires_manual_inspection,support_projected_overlap_too_low,support_vertical_gap_too_large`
- `violated` `support_contact` `chair --standing on--> floor` score=`0.3333333333333333` reason=`support_contact_requires_manual_inspection,support_projected_overlap_too_low,support_vertical_gap_too_large`
- `violated` `support_contact` `lamp --standing on--> cabinet` score=`0.3333333333333333` reason=`support_contact_requires_manual_inspection,support_projected_overlap_too_low,support_vertical_gap_too_large`
- `uncertain` `support_contact` `chair --standing on--> floor` score=`0.6666666666666666` reason=`support_contact_requires_manual_inspection,support_object_aabb_too_coarse`

## Known Limitations

- This is a one-scan smoke test, not benchmark evidence.
- The verifier uses `semseg_obb_v0`; support/contact decisions can be distorted by coarse OBB-derived AABB geometry.
- `relative_horizontal` is diagnostic only and excluded from primary violation-rate metrics.
- `unsupported` and `uncertain` edges are not hard relation failures.

## Next Action

Review `review_queue.jsonl`, especially support/contact, proximity, and vertical relation edges.
