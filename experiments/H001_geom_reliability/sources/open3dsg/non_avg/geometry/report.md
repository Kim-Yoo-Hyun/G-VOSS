# Prediction Geometry Join Report

- created_at: `2026-06-04T11:41:04.250604+00:00`
- joiner: `h001-prediction-join-g2`
- predictions: `496600`
- verification_rows: `496600`
- rows_preserved: `True`
- geometry_available_rows: `114600`
- calibration_scored_rows: `114600`

## Verification Status

- `satisfied`: `49162`
- `uncertain`: `49674`
- `unsupported`: `382000`
- `violated`: `15764`

## Predicate Family Status

- `attachment_deferred`: unsupported=57300
- `proximity`: satisfied=17676, uncertain=714, violated=710
- `relative_horizontal`: unsupported=76400
- `relative_vertical`: satisfied=13386, uncertain=11428, violated=13386
- `support_contact`: satisfied=18100, uncertain=37532, violated=1668
- `unsupported_first_pass`: unsupported=248300

## Variant Status

- `obb_only`: satisfied=32601, uncertain=62707, unsupported=382000, violated=19292
- `point_subtype`: satisfied=49162, uncertain=49674, unsupported=382000, violated=15764
- `point_subtype_no_soft_support`: satisfied=38721, uncertain=58693, unsupported=382000, violated=17186

## Support Subtypes

- `legged_floor_support`: `4560`
- `rigid_object_on_furniture`: `29684`
- `soft_support_contact`: `23056`

## OBB To Point/Subtype Transitions

- `satisfied_to_satisfied`: `373`
- `satisfied_to_uncertain`: `1013`
- `satisfied_to_violated`: `153`
- `uncertain_to_satisfied`: `17725`
- `uncertain_to_uncertain`: `31325`
- `uncertain_to_violated`: `1515`
- `violated_to_satisfied`: `2`
- `violated_to_uncertain`: `5194`

## Notes

- This artifact preserves every prediction row.
- unsupported status means the predicate family is outside the current H001 geometry-checkable scope.
- G2 emits obb_only, point_subtype, and point_subtype_no_soft_support variants.

## Warnings

- `invalid_obb:4fbad331-465b-2a5d-8488-852fcda9513c:45:non_positive_aabb_extent`
- `invalid_obb:c2d99347-1947-2fbf-834b-f95790c125dd:7:non_positive_aabb_extent`
