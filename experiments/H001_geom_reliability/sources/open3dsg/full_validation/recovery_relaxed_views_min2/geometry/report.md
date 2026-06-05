# Prediction Geometry Join Report

- created_at: `2026-06-04T18:18:30.195582+00:00`
- joiner: `h001-prediction-join-g2`
- predictions: `695916`
- verification_rows: `695916`
- rows_preserved: `True`
- geometry_available_rows: `160596`
- calibration_scored_rows: `160596`

## Verification Status

- `satisfied`: `68054`
- `uncertain`: `70520`
- `unsupported`: `535320`
- `violated`: `22022`

## Predicate Family Status

- `attachment_deferred`: unsupported=80298
- `proximity`: satisfied=24510, uncertain=1142, violated=1114
- `relative_horizontal`: unsupported=107064
- `relative_vertical`: satisfied=18506, uncertain=16520, violated=18506
- `support_contact`: satisfied=25038, uncertain=52858, violated=2402
- `unsupported_first_pass`: unsupported=347958

## Variant Status

- `obb_only`: satisfied=45269, uncertain=87484, unsupported=535320, violated=27843
- `point_subtype`: satisfied=68054, uncertain=70520, unsupported=535320, violated=22022
- `point_subtype_no_soft_support`: satisfied=53373, uncertain=82742, unsupported=535320, violated=24481

## Support Subtypes

- `legged_floor_support`: `6332`
- `rigid_object_on_furniture`: `40380`
- `soft_support_contact`: `33586`

## OBB To Point/Subtype Transitions

- `satisfied_to_satisfied`: `619`
- `satisfied_to_uncertain`: `1386`
- `satisfied_to_violated`: `248`
- `uncertain_to_satisfied`: `24417`
- `uncertain_to_uncertain`: `43251`
- `uncertain_to_violated`: `2154`
- `violated_to_satisfied`: `2`
- `violated_to_uncertain`: `8221`

## Notes

- This artifact preserves every prediction row.
- unsupported status means the predicate family is outside the current H001 geometry-checkable scope.
- G2 emits obb_only, point_subtype, and point_subtype_no_soft_support variants.

## Warnings

- `invalid_obb:4fbad331-465b-2a5d-8488-852fcda9513c:45:non_positive_aabb_extent`
- `invalid_obb:c2d99347-1947-2fbf-834b-f95790c125dd:7:non_positive_aabb_extent`
