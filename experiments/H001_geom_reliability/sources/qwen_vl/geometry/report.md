# Prediction Geometry Join Report

- created_at: `2026-06-11T02:59:31.370279+00:00`
- joiner: `h001-prediction-join-g2`
- predictions: `25262`
- verification_rows: `25262`
- rows_preserved: `True`
- geometry_available_rows: `23084`
- calibration_scored_rows: `23084`

## Verification Status

- `satisfied`: `14548`
- `uncertain`: `5599`
- `unsupported`: `2178`
- `violated`: `2937`

## Predicate Family Status

- `attachment_deferred`: unsupported=1529
- `proximity`: satisfied=9536, uncertain=41, violated=11
- `relative_vertical`: satisfied=2662, uncertain=3321, violated=2751
- `support_contact`: satisfied=2350, uncertain=2237, violated=175
- `unsupported_first_pass`: unsupported=649

## Variant Status

- `obb_only`: satisfied=12321, uncertain=7982, unsupported=2178, violated=2781
- `point_subtype`: satisfied=14548, uncertain=5599, unsupported=2178, violated=2937
- `point_subtype_no_soft_support`: satisfied=13466, uncertain=6754, unsupported=2178, violated=2864

## Support Subtypes

- `legged_floor_support`: `904`
- `rigid_object_on_furniture`: `2881`
- `soft_support_contact`: `977`

## OBB To Point/Subtype Transitions

- `satisfied_to_satisfied`: `47`
- `satisfied_to_uncertain`: `64`
- `satisfied_to_violated`: `12`
- `uncertain_to_satisfied`: `2303`
- `uncertain_to_uncertain`: `2154`
- `uncertain_to_violated`: `163`
- `violated_to_uncertain`: `19`

## Notes

- This artifact preserves every prediction row.
- unsupported status means the predicate family is outside the current H001 geometry-checkable scope.
- G2 emits obb_only, point_subtype, and point_subtype_no_soft_support variants.

## Warnings

- `invalid_obb:4fbad331-465b-2a5d-8488-852fcda9513c:45:non_positive_aabb_extent`
- `invalid_obb:c2d99347-1947-2fbf-834b-f95790c125dd:7:non_positive_aabb_extent`
