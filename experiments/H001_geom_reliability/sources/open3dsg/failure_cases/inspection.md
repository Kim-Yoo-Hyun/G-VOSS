# Open3DSG Qualitative Failure Case Inspection

Status: `qualitative_case_inspection_ready`
Created at: `2026-05-19T03:34:02.622536+00:00`

## Scope

This report inspects the sampled Open3DSG qualitative queue generated from real prediction, GT, geometry, and metric joins.
It does not add a metric and does not perform an independent visual audit.

## Inspection Verdict

- The queue supports the H001 failure mechanism: semantically plausible relation predictions can be physically inconsistent at the relation/object-pair level.
- The failure pattern is family-structured rather than a generic score artifact.
- Geometry-aware reranking also has promotion/retention cases, so paper wording must report recall and violation jointly.
- Some violated cases still receive high calibrated probability, so rule-verified and probabilistic variants must remain separate in tables.
- No taxonomy change is made in this inspection.

## Counts

- selected cases: `36`
- demoted by geometry-aware reranking: `23`
- promoted or retained by geometry-aware reranking: `13`
- violated but p_geom_valid > 0.9: `10`
- p_geom_valid range: `8.947e-08` to `0.9994`
- semantic rank range: `1` to `426`
- geometry rank range: `5` to `432`

### By Category

- `geometry_contradiction`: 14
- `semantic_and_geometry_failure`: 22

### By Family

- `proximity`: 8
- `relative_vertical`: 18
- `support_contact`: 10

### By Reason Code

- `far_in_normalized_xy`: 8
- `horizontal_plane_found`: 3
- `plane_gap_large`: 3
- `point_subtype_delegated_to_obb_for_family`: 26
- `positive_float_gap_large`: 7
- `subtype_rigid_object_on_furniture`: 3
- `subtype_soft_support_contact`: 7
- `vertical_order_contradicts_predicate`: 18

## Mechanism Notes

- `semantic_plausibility_can_conflict_with_geometry`: 23 of 36 selected cases are demoted by geometry-aware reranking. Several have semantic top-50 ranks but low p_geom_valid or explicit geometry reason codes.
- `failure_is_family_structured`: proximity failures concentrate in far_in_normalized_xy; relative_vertical failures concentrate in vertical_order_contradicts_predicate; support_contact failures expose float-gap or support-plane contradictions.
- `reranking_has_recall_tradeoff_cases`: 13 selected cases are promoted or retained by geometry-aware ranking. These are useful for explaining why the paper must report recall and violation jointly.
- `calibration_is_not_equivalent_to_hard_rule_validity`: 10 selected cases are rule-violated but have p_geom_valid > 0.9. These residual cases justify reporting rule-verified, probabilistic, and family-specific variants separately.
- `qualitative_queue_is_not_a_human_audit`: The queue is deterministic diagnostic evidence from prediction/GT/geometry joins. It should guide figure selection and failure narratives, not be reported as a representative visual audit.

## Representative Demotions

| case | category | family | predicate | pair | transition | sem -> geom rank | p_geom_valid | reason |
| --- | --- | --- | --- | --- | --- | ---: | ---: | --- |
| `open3dsg_case_019` | `semantic_and_geometry_failure` | `relative_vertical` | `higher than` | floor -> curtain | `demoted_out_of_top50` | 1 -> 432 | 0.001603 | `point_subtype_delegated_to_obb_for_family; vertical_order_contradicts_predicate` |
| `open3dsg_case_029` | `semantic_and_geometry_failure` | `relative_vertical` | `higher than` | floor -> window | `demoted_out_of_top50` | 1 -> 432 | 0.0006029 | `point_subtype_delegated_to_obb_for_family; vertical_order_contradicts_predicate` |
| `open3dsg_case_030` | `semantic_and_geometry_failure` | `relative_vertical` | `higher than` | floor -> ceiling | `demoted_out_of_top50` | 1 -> 432 | 8.947e-08 | `point_subtype_delegated_to_obb_for_family; vertical_order_contradicts_predicate` |
| `open3dsg_case_031` | `semantic_and_geometry_failure` | `relative_vertical` | `higher than` | floor -> ceiling | `demoted_out_of_top50` | 1 -> 432 | 5.164e-05 | `point_subtype_delegated_to_obb_for_family; vertical_order_contradicts_predicate` |
| `open3dsg_case_032` | `semantic_and_geometry_failure` | `relative_vertical` | `higher than` | floor -> ceiling | `demoted_out_of_top50` | 2 -> 432 | 1.341e-07 | `point_subtype_delegated_to_obb_for_family; vertical_order_contradicts_predicate` |
| `open3dsg_case_033` | `semantic_and_geometry_failure` | `relative_vertical` | `higher than` | floor -> ceiling | `demoted_out_of_top50` | 1 -> 431 | 3.2e-07 | `point_subtype_delegated_to_obb_for_family; vertical_order_contradicts_predicate` |
| `open3dsg_case_034` | `semantic_and_geometry_failure` | `relative_vertical` | `higher than` | floor -> pipe | `demoted_out_of_top50` | 2 -> 432 | 5.399e-06 | `point_subtype_delegated_to_obb_for_family; vertical_order_contradicts_predicate` |
| `open3dsg_case_035` | `semantic_and_geometry_failure` | `relative_vertical` | `higher than` | floor -> ceiling | `demoted_out_of_top50` | 2 -> 432 | 8.716e-06 | `point_subtype_delegated_to_obb_for_family; vertical_order_contradicts_predicate` |

## Representative Promotion Or Retention Tradeoffs

| case | category | family | predicate | pair | transition | sem -> geom rank | p_geom_valid | reason |
| --- | --- | --- | --- | --- | --- | ---: | ---: | --- |
| `open3dsg_case_022` | `semantic_and_geometry_failure` | `relative_vertical` | `lower than` | radiator -> floor | `promoted_into_top100` | 400 -> 55 | 0.9969 | `point_subtype_delegated_to_obb_for_family; vertical_order_contradicts_predicate` |
| `open3dsg_case_008` | `geometry_contradiction` | `relative_vertical` | `lower than` | object -> cabinet | `promoted_into_top100` | 426 -> 91 | 0.9973 | `point_subtype_delegated_to_obb_for_family; vertical_order_contradicts_predicate` |
| `open3dsg_case_021` | `semantic_and_geometry_failure` | `relative_vertical` | `lower than` | doorframe -> floor | `promoted_into_top50` | 352 -> 47 | 0.9987 | `point_subtype_delegated_to_obb_for_family; vertical_order_contradicts_predicate` |
| `open3dsg_case_027` | `semantic_and_geometry_failure` | `support_contact` | `lying on` | pack -> floor | `promoted_into_top100` | 391 -> 92 | 0.9578 | `positive_float_gap_large; subtype_soft_support_contact` |
| `open3dsg_case_007` | `geometry_contradiction` | `relative_vertical` | `lower than` | chair -> floor | `promoted_into_top50` | 339 -> 50 | 0.9994 | `point_subtype_delegated_to_obb_for_family; vertical_order_contradicts_predicate` |
| `open3dsg_case_013` | `geometry_contradiction` | `support_contact` | `supported by` | box -> wardrobe | `promoted_into_top100` | 366 -> 84 | 0.9975 | `horizontal_plane_found; plane_gap_large; subtype_rigid_object_on_furniture` |
| `open3dsg_case_026` | `semantic_and_geometry_failure` | `support_contact` | `lying on` | door -> floor | `promoted_into_top50` | 286 -> 36 | 0.998 | `positive_float_gap_large; subtype_soft_support_contact` |
| `open3dsg_case_012` | `geometry_contradiction` | `support_contact` | `supported by` | item -> refrigerator | `promoted_into_top50` | 258 -> 46 | 0.9964 | `horizontal_plane_found; plane_gap_large; subtype_rigid_object_on_furniture` |

## Residual Calibration Risk Cases

| case | category | family | predicate | pair | transition | sem -> geom rank | p_geom_valid | reason |
| --- | --- | --- | --- | --- | --- | ---: | ---: | --- |
| `open3dsg_case_007` | `geometry_contradiction` | `relative_vertical` | `lower than` | chair -> floor | `promoted_into_top50` | 339 -> 50 | 0.9994 | `point_subtype_delegated_to_obb_for_family; vertical_order_contradicts_predicate` |
| `open3dsg_case_009` | `geometry_contradiction` | `relative_vertical` | `lower than` | doorframe -> floor | `stayed_in_topk` | 45 -> 5 | 0.9993 | `point_subtype_delegated_to_obb_for_family; vertical_order_contradicts_predicate` |
| `open3dsg_case_028` | `semantic_and_geometry_failure` | `support_contact` | `lying on` | vase -> floor | `stayed_in_topk` | 49 -> 6 | 0.9988 | `positive_float_gap_large; subtype_soft_support_contact` |
| `open3dsg_case_021` | `semantic_and_geometry_failure` | `relative_vertical` | `lower than` | doorframe -> floor | `promoted_into_top50` | 352 -> 47 | 0.9987 | `point_subtype_delegated_to_obb_for_family; vertical_order_contradicts_predicate` |
| `open3dsg_case_026` | `semantic_and_geometry_failure` | `support_contact` | `lying on` | door -> floor | `promoted_into_top50` | 286 -> 36 | 0.998 | `positive_float_gap_large; subtype_soft_support_contact` |
| `open3dsg_case_013` | `geometry_contradiction` | `support_contact` | `supported by` | box -> wardrobe | `promoted_into_top100` | 366 -> 84 | 0.9975 | `horizontal_plane_found; plane_gap_large; subtype_rigid_object_on_furniture` |
| `open3dsg_case_008` | `geometry_contradiction` | `relative_vertical` | `lower than` | object -> cabinet | `promoted_into_top100` | 426 -> 91 | 0.9973 | `point_subtype_delegated_to_obb_for_family; vertical_order_contradicts_predicate` |
| `open3dsg_case_022` | `semantic_and_geometry_failure` | `relative_vertical` | `lower than` | radiator -> floor | `promoted_into_top100` | 400 -> 55 | 0.9969 | `point_subtype_delegated_to_obb_for_family; vertical_order_contradicts_predicate` |

## Family Mechanism Examples

| case | category | family | predicate | pair | transition | sem -> geom rank | p_geom_valid | reason |
| --- | --- | --- | --- | --- | --- | ---: | ---: | --- |
| `open3dsg_case_001` | `geometry_contradiction` | `proximity` | `close by` | heater -> trash can | `demoted_out_of_top50` | 17 -> 263 | 0.2304 | `far_in_normalized_xy; point_subtype_delegated_to_obb_for_family` |
| `open3dsg_case_005` | `geometry_contradiction` | `relative_vertical` | `higher than` | desk -> lamp | `demoted_out_of_top50` | 25 -> 422 | 0.001915 | `point_subtype_delegated_to_obb_for_family; vertical_order_contradicts_predicate` |
| `open3dsg_case_010` | `geometry_contradiction` | `support_contact` | `lying on` | lamp -> side table | `demoted_out_of_top50` | 21 -> 401 | 0.02479 | `positive_float_gap_large; subtype_soft_support_contact` |
| `open3dsg_case_019` | `semantic_and_geometry_failure` | `relative_vertical` | `higher than` | floor -> curtain | `demoted_out_of_top50` | 1 -> 432 | 0.001603 | `point_subtype_delegated_to_obb_for_family; vertical_order_contradicts_predicate` |
| `open3dsg_case_026` | `semantic_and_geometry_failure` | `support_contact` | `lying on` | door -> floor | `promoted_into_top50` | 286 -> 36 | 0.998 | `positive_float_gap_large; subtype_soft_support_contact` |
| `open3dsg_case_030` | `semantic_and_geometry_failure` | `relative_vertical` | `higher than` | floor -> ceiling | `demoted_out_of_top50` | 1 -> 432 | 8.947e-08 | `point_subtype_delegated_to_obb_for_family; vertical_order_contradicts_predicate` |

## Paper Use

Allowed:

- Use as qualitative failure-mechanism examples tied to Table 6 and the locked taxonomy.
- Use demoted cases to show semantically plausible but physically inconsistent relations.
- Use promoted or retained cases to explain recall/violation tradeoffs.
- Use high-p but rule-violated cases to disclose residual calibration risk.
- Use family-specific reason codes to justify family-specific controls and denominator reporting.

Not allowed:

- Do not report the 36-case queue as a representative human audit.
- Do not change the locked taxonomy based on this inspection without a schema version bump.
- Do not claim broad open-vocabulary 3DSSG improvement from these qualitative cases alone.

## Outputs

- `inspection_json`: `experiments/H001_geom_reliability/sources/open3dsg/failure_cases/inspection.json`
- `inspection_md`: `experiments/H001_geom_reliability/sources/open3dsg/failure_cases/inspection.md`

## Claim Boundary

qualitative reviewer-defense artifact only; not a new metric, not a visual audit, and not evidence beyond measured H001-family scope
