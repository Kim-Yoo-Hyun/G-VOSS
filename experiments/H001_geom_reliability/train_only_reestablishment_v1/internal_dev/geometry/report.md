# Prediction Geometry Join Report

- created_at: `2026-07-10T15:12:18.112008+00:00`
- joiner: `h001-prediction-join-g2`
- predictions: `139368`
- verification_rows: `139368`
- rows_preserved: `True`
- geometry_available_rows: `139368`
- calibration_scored_rows: `139368`

## Verification Status

- `satisfied`: `56505`
- `uncertain`: `63841`
- `violated`: `19022`

## Predicate Family Status

- `proximity`: satisfied=20768, uncertain=1116, violated=1344
- `relative_vertical`: satisfied=15882, uncertain=14692, violated=15882
- `support_contact`: satisfied=19855, uncertain=48033, violated=1796

## Variant Status

- `obb_only`: satisfied=38654, uncertain=74677, violated=26037
- `point_subtype`: satisfied=56505, uncertain=63841, violated=19022
- `point_subtype_no_soft_support`: satisfied=44942, uncertain=72371, violated=22055

## Support Subtypes

- `legged_floor_support`: `4856`
- `rigid_object_on_furniture`: `35084`
- `soft_support_contact`: `29744`

## OBB To Point/Subtype Transitions

- `satisfied_to_satisfied`: `464`
- `satisfied_to_uncertain`: `1283`
- `satisfied_to_violated`: `257`
- `uncertain_to_satisfied`: `19391`
- `uncertain_to_uncertain`: `37940`
- `uncertain_to_violated`: `1538`
- `violated_to_uncertain`: `8810`
- `violated_to_violated`: `1`

## Notes

- This artifact preserves every prediction row.
- unsupported status means the predicate family is outside the current H001 geometry-checkable scope.
- G2 emits obb_only, point_subtype, and point_subtype_no_soft_support variants.

## Warnings

- `invalid_obb:ee527b51-0df9-2dae-829e-a0543a6e4074:13:non_positive_aabb_extent`
