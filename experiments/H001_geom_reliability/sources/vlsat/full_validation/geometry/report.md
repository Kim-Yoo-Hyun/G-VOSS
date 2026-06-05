# Prediction Geometry Join Report

- created_at: `2026-06-04T12:00:48.181891+00:00`
- joiner: `h001-prediction-join-g2`
- predictions: `957008`
- verification_rows: `957008`
- rows_preserved: `True`
- geometry_available_rows: `220848`
- calibration_scored_rows: `220848`

## Verification Status

- `satisfied`: `89116`
- `uncertain`: `100476`
- `unsupported`: `736160`
- `violated`: `31256`

## Predicate Family Status

- `attachment_deferred`: unsupported=110424
- `proximity`: satisfied=32812, uncertain=1860, violated=2136
- `relative_horizontal`: unsupported=147232
- `relative_vertical`: satisfied=25826, uncertain=21964, violated=25826
- `support_contact`: satisfied=30478, uncertain=76652, violated=3294
- `unsupported_first_pass`: unsupported=478504

## Variant Status

- `obb_only`: satisfied=61878, uncertain=117052, unsupported=736160, violated=41918
- `point_subtype`: satisfied=89116, uncertain=100476, unsupported=736160, violated=31256
- `point_subtype_no_soft_support`: satisfied=71494, uncertain=113408, unsupported=736160, violated=35946

## Support Subtypes

- `legged_floor_support`: `7718`
- `rigid_object_on_furniture`: `56162`
- `soft_support_contact`: `46544`

## OBB To Point/Subtype Transitions

- `satisfied_to_satisfied`: `847`
- `satisfied_to_uncertain`: `2024`
- `satisfied_to_violated`: `369`
- `uncertain_to_satisfied`: `29629`
- `uncertain_to_uncertain`: `60674`
- `uncertain_to_violated`: `2925`
- `violated_to_satisfied`: `2`
- `violated_to_uncertain`: `13954`

## Notes

- This artifact preserves every prediction row.
- unsupported status means the predicate family is outside the current H001 geometry-checkable scope.
- G2 emits obb_only, point_subtype, and point_subtype_no_soft_support variants.

## Warnings

- `invalid_obb:4fbad331-465b-2a5d-8488-852fcda9513c:45:non_positive_aabb_extent`
- `invalid_obb:c2d99347-1947-2fbf-834b-f95790c125dd:7:non_positive_aabb_extent`
