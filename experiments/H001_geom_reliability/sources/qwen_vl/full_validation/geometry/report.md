# Prediction Geometry Join Report

- created_at: `2026-06-11T18:16:11.533165+00:00`
- joiner: `h001-prediction-join-g2`
- predictions: `35131`
- verification_rows: `35131`
- rows_preserved: `True`
- geometry_available_rows: `32236`
- calibration_scored_rows: `32236`

## Verification Status

- `satisfied`: `20269`
- `uncertain`: `7918`
- `unsupported`: `2895`
- `violated`: `4049`

## Predicate Family Status

- `attachment_deferred`: unsupported=1978
- `proximity`: satisfied=13315, uncertain=54, violated=20
- `relative_vertical`: satisfied=3634, uncertain=4663, violated=3782
- `support_contact`: satisfied=3320, uncertain=3201, violated=247
- `unsupported_first_pass`: unsupported=917

## Variant Status

- `obb_only`: satisfied=17122, uncertain=11276, unsupported=2895, violated=3838
- `point_subtype`: satisfied=20269, uncertain=7918, unsupported=2895, violated=4049
- `point_subtype_no_soft_support`: satisfied=18676, uncertain=9612, unsupported=2895, violated=3948

## Support Subtypes

- `legged_floor_support`: `1272`
- `rigid_object_on_furniture`: `3990`
- `soft_support_contact`: `1506`

## OBB To Point/Subtype Transitions

- `satisfied_to_satisfied`: `74`
- `satisfied_to_uncertain`: `84`
- `satisfied_to_violated`: `15`
- `uncertain_to_satisfied`: `3246`
- `uncertain_to_uncertain`: `3081`
- `uncertain_to_violated`: `232`
- `violated_to_uncertain`: `36`

## Notes

- This artifact preserves every prediction row.
- unsupported status means the predicate family is outside the current H001 geometry-checkable scope.
- G2 emits obb_only, point_subtype, and point_subtype_no_soft_support variants.

## Warnings

- `invalid_obb:4fbad331-465b-2a5d-8488-852fcda9513c:45:non_positive_aabb_extent`
- `invalid_obb:c2d99347-1947-2fbf-834b-f95790c125dd:7:non_positive_aabb_extent`
