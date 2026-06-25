# Open3DSG recovery full-validation Qualitative Failure Case Inspection

Status: `qualitative_case_inspection_ready`
Created at: `2026-06-05T01:26:15.971078+00:00`

## Scope

This report inspects the sampled Open3DSG recovery full-validation qualitative queue generated from real prediction, GT, geometry, and metric joins.
It does not add a metric and does not perform an independent visual audit.

## Inspection Verdict

- The queue supports the H001 failure mechanism: semantically plausible relation predictions can be physically inconsistent at the relation/object-pair level.
- The failure pattern is family-structured rather than a generic score artifact.
- Geometry-aware reranking also has promotion/retention cases, so paper wording must report recall and violation jointly.
- Some violated cases still receive high calibrated probability, so rule-verified and probabilistic variants must remain separate in tables.
- No taxonomy change is made in this inspection.

## Counts

- selected cases: `36`
- demoted by geometry-aware reranking: `25`
- promoted or retained by geometry-aware reranking: `11`
- violated but p_geom_valid > 0.9: `8`
- p_geom_valid range: `7.511e-14` to `0.9999`
- semantic rank range: `1` to `421`
- geometry rank range: `48` to `432`

### By Category

- `geometry_contradiction`: 13
- `semantic_and_geometry_failure`: 23

### By Family

- `proximity`: 7
- `relative_vertical`: 19
- `support_contact`: 10

### By Reason Code

- `far_in_normalized_xy`: 7
- `horizontal_plane_found`: 6
- `plane_gap_large`: 6
- `point_subtype_delegated_to_obb_for_family`: 26
- `positive_float_gap_large`: 4
- `subtype_rigid_object_on_furniture`: 6
- `subtype_soft_support_contact`: 4
- `vertical_order_contradicts_predicate`: 19

## Mechanism Notes

- `semantic_plausibility_can_conflict_with_geometry`: 25 of 36 selected cases are demoted by geometry-aware reranking. Several have semantic top-50 ranks but low p_geom_valid or explicit geometry reason codes.
- `failure_is_family_structured`: proximity failures concentrate in far_in_normalized_xy; relative_vertical failures concentrate in vertical_order_contradicts_predicate; support_contact failures expose float-gap or support-plane contradictions.
- `reranking_has_recall_tradeoff_cases`: 11 selected cases are promoted or retained by geometry-aware ranking. These are useful for explaining why the paper must report recall and violation jointly.
- `calibration_is_not_equivalent_to_hard_rule_validity`: 8 selected cases are rule-violated but have p_geom_valid > 0.9. These residual cases justify reporting rule-verified, probabilistic, and family-specific variants separately.
- `qualitative_queue_is_not_a_human_audit`: The queue is deterministic diagnostic evidence from prediction/GT/geometry joins. It should guide figure selection and failure narratives, not be reported as a representative visual audit.

## Representative Demotions

| case | category | family | predicate | pair | transition | sem -> geom rank | p_geom_valid | reason |
| --- | --- | --- | --- | --- | --- | ---: | ---: | --- |
| `open3dsg_recovery_case_018` | `semantic_and_geometry_failure` | `relative_vertical` | `higher than` | floor -> ceiling | `demoted_out_of_top50` | 1 -> 432 | 8.716e-06 | `point_subtype_delegated_to_obb_for_family; vertical_order_contradicts_predicate` |
| `open3dsg_recovery_case_028` | `semantic_and_geometry_failure` | `relative_vertical` | `higher than` | floor -> ceiling | `demoted_out_of_top50` | 1 -> 432 | 0.0001461 | `point_subtype_delegated_to_obb_for_family; vertical_order_contradicts_predicate` |
| `open3dsg_recovery_case_029` | `semantic_and_geometry_failure` | `relative_vertical` | `higher than` | floor -> curtain | `demoted_out_of_top50` | 1 -> 432 | 0.001603 | `point_subtype_delegated_to_obb_for_family; vertical_order_contradicts_predicate` |
| `open3dsg_recovery_case_030` | `semantic_and_geometry_failure` | `relative_vertical` | `higher than` | floor -> ceiling | `demoted_out_of_top50` | 1 -> 432 | 8.027e-09 | `point_subtype_delegated_to_obb_for_family; vertical_order_contradicts_predicate` |
| `open3dsg_recovery_case_031` | `semantic_and_geometry_failure` | `relative_vertical` | `higher than` | floor -> ceiling | `demoted_out_of_top50` | 1 -> 432 | 8.947e-08 | `point_subtype_delegated_to_obb_for_family; vertical_order_contradicts_predicate` |
| `open3dsg_recovery_case_032` | `semantic_and_geometry_failure` | `relative_vertical` | `higher than` | floor -> mirror | `demoted_out_of_top50` | 1 -> 431 | 0.0009583 | `point_subtype_delegated_to_obb_for_family; vertical_order_contradicts_predicate` |
| `open3dsg_recovery_case_033` | `semantic_and_geometry_failure` | `relative_vertical` | `higher than` | floor -> ceiling | `demoted_out_of_top50` | 2 -> 432 | 1.658e-07 | `point_subtype_delegated_to_obb_for_family; vertical_order_contradicts_predicate` |
| `open3dsg_recovery_case_034` | `semantic_and_geometry_failure` | `relative_vertical` | `higher than` | floor -> ceiling | `demoted_out_of_top50` | 2 -> 432 | 2.623e-07 | `point_subtype_delegated_to_obb_for_family; vertical_order_contradicts_predicate` |

## Representative Promotion Or Retention Tradeoffs

| case | category | family | predicate | pair | transition | sem -> geom rank | p_geom_valid | reason |
| --- | --- | --- | --- | --- | --- | ---: | ---: | --- |
| `open3dsg_recovery_case_021` | `semantic_and_geometry_failure` | `relative_vertical` | `lower than` | clothes -> floor | `promoted_into_top100` | 416 -> 69 | 0.9968 | `point_subtype_delegated_to_obb_for_family; vertical_order_contradicts_predicate` |
| `open3dsg_recovery_case_007` | `geometry_contradiction` | `relative_vertical` | `lower than` | chair -> floor | `promoted_into_top100` | 421 -> 78 | 0.9998 | `point_subtype_delegated_to_obb_for_family; vertical_order_contradicts_predicate` |
| `open3dsg_recovery_case_025` | `semantic_and_geometry_failure` | `support_contact` | `supported by` | clothes -> floor | `promoted_into_top50` | 362 -> 48 | 0.9993 | `positive_float_gap_large; subtype_soft_support_contact` |
| `open3dsg_recovery_case_026` | `semantic_and_geometry_failure` | `support_contact` | `supported by` | curtain -> wall | `promoted_into_top100` | 383 -> 76 | 0.9992 | `horizontal_plane_found; plane_gap_large; subtype_rigid_object_on_furniture` |
| `open3dsg_recovery_case_006` | `geometry_contradiction` | `relative_vertical` | `lower than` | chair -> floor | `promoted_into_top50` | 347 -> 49 | 0.9999 | `point_subtype_delegated_to_obb_for_family; vertical_order_contradicts_predicate` |
| `open3dsg_recovery_case_020` | `semantic_and_geometry_failure` | `relative_vertical` | `lower than` | clutter -> floor | `promoted_into_top50` | 345 -> 50 | 0.9998 | `point_subtype_delegated_to_obb_for_family; vertical_order_contradicts_predicate` |
| `open3dsg_recovery_case_012` | `geometry_contradiction` | `support_contact` | `supported by` | box -> wardrobe | `promoted_into_top100` | 382 -> 93 | 0.9975 | `horizontal_plane_found; plane_gap_large; subtype_rigid_object_on_furniture` |
| `open3dsg_recovery_case_011` | `geometry_contradiction` | `support_contact` | `supported by` | item -> refrigerator | `promoted_into_top50` | 281 -> 50 | 0.9964 | `horizontal_plane_found; plane_gap_large; subtype_rigid_object_on_furniture` |

## Residual Calibration Risk Cases

| case | category | family | predicate | pair | transition | sem -> geom rank | p_geom_valid | reason |
| --- | --- | --- | --- | --- | --- | ---: | ---: | --- |
| `open3dsg_recovery_case_006` | `geometry_contradiction` | `relative_vertical` | `lower than` | chair -> floor | `promoted_into_top50` | 347 -> 49 | 0.9999 | `point_subtype_delegated_to_obb_for_family; vertical_order_contradicts_predicate` |
| `open3dsg_recovery_case_020` | `semantic_and_geometry_failure` | `relative_vertical` | `lower than` | clutter -> floor | `promoted_into_top50` | 345 -> 50 | 0.9998 | `point_subtype_delegated_to_obb_for_family; vertical_order_contradicts_predicate` |
| `open3dsg_recovery_case_007` | `geometry_contradiction` | `relative_vertical` | `lower than` | chair -> floor | `promoted_into_top100` | 421 -> 78 | 0.9998 | `point_subtype_delegated_to_obb_for_family; vertical_order_contradicts_predicate` |
| `open3dsg_recovery_case_025` | `semantic_and_geometry_failure` | `support_contact` | `supported by` | clothes -> floor | `promoted_into_top50` | 362 -> 48 | 0.9993 | `positive_float_gap_large; subtype_soft_support_contact` |
| `open3dsg_recovery_case_026` | `semantic_and_geometry_failure` | `support_contact` | `supported by` | curtain -> wall | `promoted_into_top100` | 383 -> 76 | 0.9992 | `horizontal_plane_found; plane_gap_large; subtype_rigid_object_on_furniture` |
| `open3dsg_recovery_case_012` | `geometry_contradiction` | `support_contact` | `supported by` | box -> wardrobe | `promoted_into_top100` | 382 -> 93 | 0.9975 | `horizontal_plane_found; plane_gap_large; subtype_rigid_object_on_furniture` |
| `open3dsg_recovery_case_021` | `semantic_and_geometry_failure` | `relative_vertical` | `lower than` | clothes -> floor | `promoted_into_top100` | 416 -> 69 | 0.9968 | `point_subtype_delegated_to_obb_for_family; vertical_order_contradicts_predicate` |
| `open3dsg_recovery_case_011` | `geometry_contradiction` | `support_contact` | `supported by` | item -> refrigerator | `promoted_into_top50` | 281 -> 50 | 0.9964 | `horizontal_plane_found; plane_gap_large; subtype_rigid_object_on_furniture` |

## Family Mechanism Examples

| case | category | family | predicate | pair | transition | sem -> geom rank | p_geom_valid | reason |
| --- | --- | --- | --- | --- | --- | ---: | ---: | --- |
| `open3dsg_recovery_case_014` | `semantic_and_geometry_failure` | `proximity` | `close by` | heater -> item | `demoted_out_of_top50` | 20 -> 413 | 0.001286 | `far_in_normalized_xy; point_subtype_delegated_to_obb_for_family` |
| `open3dsg_recovery_case_015` | `semantic_and_geometry_failure` | `proximity` | `close by` | shoes -> frame | `demoted_out_of_top100` | 57 -> 423 | 0.0002389 | `far_in_normalized_xy; point_subtype_delegated_to_obb_for_family` |
| `open3dsg_recovery_case_018` | `semantic_and_geometry_failure` | `relative_vertical` | `higher than` | floor -> ceiling | `demoted_out_of_top50` | 1 -> 432 | 8.716e-06 | `point_subtype_delegated_to_obb_for_family; vertical_order_contradicts_predicate` |
| `open3dsg_recovery_case_028` | `semantic_and_geometry_failure` | `relative_vertical` | `higher than` | floor -> ceiling | `demoted_out_of_top50` | 1 -> 432 | 0.0001461 | `point_subtype_delegated_to_obb_for_family; vertical_order_contradicts_predicate` |
| `open3dsg_recovery_case_023` | `semantic_and_geometry_failure` | `support_contact` | `standing on` | object -> ceiling | `demoted_out_of_top50` | 17 -> 424 | 0.001068 | `horizontal_plane_found; plane_gap_large; subtype_rigid_object_on_furniture` |
| `open3dsg_recovery_case_024` | `semantic_and_geometry_failure` | `support_contact` | `standing on` | floor -> picture | `demoted_out_of_top100` | 54 -> 419 | 0.008031 | `horizontal_plane_found; plane_gap_large; subtype_rigid_object_on_furniture` |

## Paper Use

Allowed:

- Use as qualitative failure-mechanism examples tied to Table 6 and the locked taxonomy.
- Use demoted cases to show semantically plausible but physically inconsistent relations.
- Use promoted or retained cases to explain recall/violation tradeoffs.
- Use high-p but rule-violated cases to disclose residual calibration risk.
- Use family-specific reason codes to justify family-conditional calibrated-risk factors and denominator reporting.

Not allowed:

- Do not report the 36-case queue as a representative human audit.
- Do not change the locked taxonomy based on this inspection without a schema version bump.
- Do not claim broad open-vocabulary 3DSSG improvement from these qualitative cases alone.

## Outputs

- `inspection_json`: `experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2/failure_cases/inspection.json`
- `inspection_md`: `experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2/failure_cases/inspection.md`

## Claim Boundary

qualitative reviewer-defense artifact only; not a new metric, not a visual audit, and not evidence beyond measured H001-family scope
