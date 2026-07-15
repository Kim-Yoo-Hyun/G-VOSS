# Prediction Geometry Join Report

- created_at: `2026-07-14T09:01:54.987678+00:00`
- joiner: `h001-prediction-join-g2`
- predictions: `690924`
- verification_rows: `690924`
- rows_preserved: `True`
- geometry_available_rows: `159444`
- calibration_scored_rows: `159444`

## Verification Status

- `satisfied`: `67648`
- `uncertain`: `69916`
- `unsupported`: `531480`
- `violated`: `21880`

## Predicate Family Status

- `attachment_deferred`: unsupported=79722
- `proximity`: satisfied=24348, uncertain=1126, violated=1100
- `relative_horizontal`: unsupported=106296
- `relative_vertical`: satisfied=18396, uncertain=16356, violated=18396
- `support_contact`: satisfied=24904, uncertain=52434, violated=2384
- `unsupported_first_pass`: unsupported=345462

## Variant Status

- `obb_only`: satisfied=44964, uncertain=86869, unsupported=531480, violated=27611
- `point_subtype`: satisfied=67648, uncertain=69916, unsupported=531480, violated=21880
- `point_subtype_no_soft_support`: satisfied=53040, uncertain=82099, unsupported=531480, violated=24305

## Support Subtypes

- `legged_floor_support`: `6268`
- `rigid_object_on_furniture`: `40092`
- `soft_support_contact`: `33362`

## OBB To Point/Subtype Transitions

- `satisfied_to_satisfied`: `603`
- `satisfied_to_uncertain`: `1371`
- `satisfied_to_violated`: `246`
- `uncertain_to_satisfied`: `24299`
- `uncertain_to_uncertain`: `42950`
- `uncertain_to_violated`: `2138`
- `violated_to_satisfied`: `2`
- `violated_to_uncertain`: `8113`

## Notes

- This artifact preserves every prediction row.
- unsupported status means the predicate family is outside the current H001 geometry-checkable scope.
- G2 emits obb_only, point_subtype, and point_subtype_no_soft_support variants.

## Warnings

- `invalid_obb:4fbad331-465b-2a5d-8488-852fcda9513c:45:non_positive_aabb_extent`
- `invalid_obb:c2d99347-1947-2fbf-834b-f95790c125dd:7:non_positive_aabb_extent`
