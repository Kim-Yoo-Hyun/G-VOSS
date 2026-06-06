# Prediction Geometry Join Report

- created_at: `2026-06-05T18:06:29.517530+00:00`
- joiner: `h001-prediction-join-g2`
- predictions: `498212`
- verification_rows: `498212`
- rows_preserved: `True`
- geometry_available_rows: `114972`
- calibration_scored_rows: `114972`

## Verification Status

- `satisfied`: `49320`
- `uncertain`: `49829`
- `unsupported`: `383240`
- `violated`: `15823`

## Predicate Family Status

- `attachment_deferred`: unsupported=57486
- `proximity`: satisfied=17734, uncertain=718, violated=710
- `relative_horizontal`: unsupported=76648
- `relative_vertical`: satisfied=13430, uncertain=11464, violated=13430
- `support_contact`: satisfied=18156, uncertain=37647, violated=1683
- `unsupported_first_pass`: unsupported=249106

## Variant Status

- `obb_only`: satisfied=32712, uncertain=62915, unsupported=383240, violated=19345
- `point_subtype`: satisfied=49320, uncertain=49829, unsupported=383240, violated=15823
- `point_subtype_no_soft_support`: satisfied=38844, uncertain=58889, unsupported=383240, violated=17239

## Support Subtypes

- `legged_floor_support`: `4592`
- `rigid_object_on_furniture`: `29760`
- `soft_support_contact`: `23134`

## OBB To Point/Subtype Transitions

- `satisfied_to_satisfied`: `376`
- `satisfied_to_uncertain`: `1018`
- `satisfied_to_violated`: `154`
- `uncertain_to_satisfied`: `17778`
- `uncertain_to_uncertain`: `31426`
- `uncertain_to_violated`: `1529`
- `violated_to_satisfied`: `2`
- `violated_to_uncertain`: `5203`

## Notes

- This artifact preserves every prediction row.
- unsupported status means the predicate family is outside the current H001 geometry-checkable scope.
- G2 emits obb_only, point_subtype, and point_subtype_no_soft_support variants.

## Warnings

- `invalid_obb:4fbad331-465b-2a5d-8488-852fcda9513c:45:non_positive_aabb_extent`
- `invalid_obb:c2d99347-1947-2fbf-834b-f95790c125dd:7:non_positive_aabb_extent`
