# Relative Horizontal Bucket Inspection

Status: `relative_horizontal_bucket_inspection_ready_no_metric_execution`
Created at: `2026-05-27T14:47:55.705142+00:00`

## Claim Boundary

This inspection is threshold-free diagnostic evidence for the optional `relative_horizontal` expansion track. It does not run source metrics and does not change the current H001 paper claim.

## Threshold-Free Evidence

| Evidence | Value |
| --- | --- |
| selected frame | scan_left_neg_x_front_neg_y |
| inverse consistency | 1.0 |
| wrong-frame gap | 0.1231 |
| front/behind strict match:contradiction | 2.9143 |
| front/behind strict purity | 0.7445 |
| front/behind sign-only purity | 0.7491 |
| left/right strict purity | 0.8005 |

## Per-Label Buckets

| Label | Rows | Strict match | Strict uncertain | Strict contradiction | Strict purity | Sign-only purity |
| --- | --- | --- | --- | --- | --- | --- |
| left | 1132 | 586 | 400 | 146 | 0.8005 | 0.7761 |
| right | 1132 | 586 | 400 | 146 | 0.8005 | 0.7761 |
| front | 653 | 306 | 242 | 105 | 0.7445 | 0.7491 |
| behind | 653 | 306 | 242 | 105 | 0.7445 | 0.7491 |

## Front / Behind Ambiguity

| Flag | Count |
| --- | --- |
| axis_margin_ambiguous | 230 |
| conflicting_axis_dominates | 430 |
| strong_projected_overlap | 44 |

## Diagnostic Decision

- Recommendation: `do_not_promote_relative_horizontal_to_main_claim`
- Rationale: The selected frame shows nontrivial signal through inverse consistency and wrong-frame gap, but front/behind still has substantial contradiction and ambiguity buckets. This supports scope-boundary or appendix discussion, not expanded source metrics.

## Next Step

- Do not run expanded-family VL-SAT/Open3DSG metrics yet.
- If this track continues, add a targeted visual check or stronger frame metadata analysis for `front`/`behind` first.
