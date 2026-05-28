# Attachment Deferred Point/Surface Validation

Status: `attachment_deferred_point_surface_validation_ready_no_verifier`
Created at: `2026-05-27T16:55:08+00:00`

## Claim Boundary

This is the G1c point/surface estimator validation step. It is not a
verifier, not calibration, not source metric evidence, and not part of
the current AAAI main claim.

## Row Counts

| Item | Count |
| --- | ---: |
| input rows | 36 |
| output rows | 36 |
| validation errors | 0 |
| ready rows | 36 |
| point available rows | 36 |
| normal available rows | 36 |
| near-contact rows | 27 |

## Source Rows

- `counterfactual`: 9
- `gt_positive`: 9
- `open3dsg_ov`: 9
- `vlsat_closed_set`: 9

## Extractor Status

- `ready`: 36

## Surface Normal Classes

- `horizontal_up`: 14
- `slanted`: 1
- `vertical`: 21

## Important Boundary

Rows with point contact are still evidence rows only. They intentionally
omit `verification_status`, `p_geom_valid`, recall credit, and reranking
scores. A later G2 verifier-policy document must define satisfied,
violated, and uncertain states before any source metrics are run.

## Next Gate

`G2_attachment_verifier_policy_design`
