# Attachment Deferred Extractor Dry Run

Status: `attachment_deferred_extractor_dry_run_ready_no_verifier`
Created at: `2026-05-27T16:34:15+00:00`

## Claim Boundary

This is a G1b evidence-only dry run. It is not a verifier, not calibration, not
source metric evidence, and not part of the current AAAI main claim.

## Row Counts

| Item | Count |
| --- | ---: |
| input rows | 36 |
| output rows | 36 |
| validation errors | 0 |

## Source Rows

- `counterfactual`: 9
- `gt_positive`: 9
- `open3dsg_ov`: 9
- `vlsat_closed_set`: 9

## Extractor Status

- `partial`: 36

## Important Boundary

The dry run uses semseg OBB and dominantNormal proxies only. Point-contact and
surface-normal estimation from segmented points are not validated yet. The
output intentionally omits `verification_status`, `p_geom_valid`, recall credit,
and reranking scores.

## Next Gate

`G1c_attachment_point_surface_estimator_validation`
