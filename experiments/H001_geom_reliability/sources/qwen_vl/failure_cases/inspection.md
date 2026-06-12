# Qwen-VL full-source Qualitative Failure Case Inspection

Status: `qualitative_case_inspection_ready`
Created at: `2026-06-11T03:01:14.089444+00:00`

## Scope

This report inspects the sampled Qwen-VL full-source qualitative queue generated from real prediction, GT, geometry, and metric joins.
It does not add a metric and does not perform an independent visual audit.

## Inspection Verdict

- The queue supports the H001 failure mechanism: semantically plausible relation predictions can be physically inconsistent at the relation/object-pair level.
- The failure pattern is family-structured rather than a generic score artifact.
- Geometry-aware reranking also has promotion/retention cases, so paper wording must report recall and violation jointly.
- Some violated cases still receive high calibrated probability, so rule-verified and probabilistic variants must remain separate in tables.
- No taxonomy change is made in this inspection.

## Counts

- selected cases: `36`
- demoted by geometry-aware reranking: `27`
- promoted or retained by geometry-aware reranking: `9`
- violated but p_geom_valid > 0.9: `7`
- p_geom_valid range: `3.224e-05` to `0.9998`
- semantic rank range: `1` to `146`
- geometry rank range: `9` to `153`

### By Category

- `geometry_contradiction`: 10
- `semantic_and_geometry_failure`: 26

### By Family

- `proximity`: 4
- `relative_vertical`: 23
- `support_contact`: 9

### By Reason Code

- `far_in_normalized_xy`: 4
- `horizontal_plane_found`: 7
- `plane_gap_large`: 7
- `point_subtype_delegated_to_obb_for_family`: 27
- `positive_float_gap_large`: 2
- `subtype_rigid_object_on_furniture`: 7
- `subtype_soft_support_contact`: 2
- `vertical_order_contradicts_predicate`: 23

## Mechanism Notes

- `semantic_plausibility_can_conflict_with_geometry`: 27 of 36 selected cases are demoted by geometry-aware reranking. Several have semantic top-50 ranks but low p_geom_valid or explicit geometry reason codes.
- `failure_is_family_structured`: proximity failures concentrate in far_in_normalized_xy; relative_vertical failures concentrate in vertical_order_contradicts_predicate; support_contact failures expose float-gap or support-plane contradictions.
- `reranking_has_recall_tradeoff_cases`: 9 selected cases are promoted or retained by geometry-aware ranking. These are useful for explaining why the paper must report recall and violation jointly.
- `calibration_is_not_equivalent_to_hard_rule_validity`: 7 selected cases are rule-violated but have p_geom_valid > 0.9. These residual cases justify reporting rule-verified, probabilistic, and family-specific variants separately.
- `qualitative_queue_is_not_a_human_audit`: The queue is deterministic diagnostic evidence from prediction/GT/geometry joins. It should guide figure selection and failure narratives, not be reported as a representative visual audit.

## Representative Demotions

| case | category | family | predicate | pair | transition | sem -> geom rank | p_geom_valid | reason |
| --- | --- | --- | --- | --- | --- | ---: | ---: | --- |
| `qwen_vl_case_014` | `semantic_and_geometry_failure` | `relative_vertical` | `higher than` | floor -> wall | `demoted_out_of_top50` | 2 -> 153 | 0.04381 | `point_subtype_delegated_to_obb_for_family; vertical_order_contradicts_predicate` |
| `qwen_vl_case_024` | `semantic_and_geometry_failure` | `relative_vertical` | `higher than` | floor -> wall | `demoted_out_of_top50` | 4 -> 132 | 0.0169 | `point_subtype_delegated_to_obb_for_family; vertical_order_contradicts_predicate` |
| `qwen_vl_case_025` | `semantic_and_geometry_failure` | `relative_vertical` | `higher than` | floor -> picture | `demoted_out_of_top50` | 1 -> 128 | 3.224e-05 | `point_subtype_delegated_to_obb_for_family; vertical_order_contradicts_predicate` |
| `qwen_vl_case_026` | `semantic_and_geometry_failure` | `relative_vertical` | `higher than` | floor -> wall | `demoted_out_of_top50` | 2 -> 129 | 0.008776 | `point_subtype_delegated_to_obb_for_family; vertical_order_contradicts_predicate` |
| `qwen_vl_case_019` | `semantic_and_geometry_failure` | `support_contact` | `supported by` | floor -> wall | `demoted_out_of_top50` | 4 -> 127 | 0.04783 | `horizontal_plane_found; plane_gap_large; subtype_rigid_object_on_furniture` |
| `qwen_vl_case_027` | `semantic_and_geometry_failure` | `relative_vertical` | `higher than` | floor -> shower curtain | `demoted_out_of_top50` | 12 -> 133 | 0.01585 | `point_subtype_delegated_to_obb_for_family; vertical_order_contradicts_predicate` |
| `qwen_vl_case_028` | `semantic_and_geometry_failure` | `relative_vertical` | `higher than` | heater -> window | `demoted_out_of_top50` | 23 -> 137 | 0.0005196 | `point_subtype_delegated_to_obb_for_family; vertical_order_contradicts_predicate` |
| `qwen_vl_case_029` | `semantic_and_geometry_failure` | `relative_vertical` | `higher than` | floor -> wall | `demoted_out_of_top50` | 8 -> 122 | 0.001973 | `point_subtype_delegated_to_obb_for_family; vertical_order_contradicts_predicate` |

## Representative Promotion Or Retention Tradeoffs

| case | category | family | predicate | pair | transition | sem -> geom rank | p_geom_valid | reason |
| --- | --- | --- | --- | --- | --- | ---: | ---: | --- |
| `qwen_vl_case_004` | `geometry_contradiction` | `relative_vertical` | `lower than` | towel -> shower | `promoted_into_top50` | 118 -> 21 | 0.9983 | `point_subtype_delegated_to_obb_for_family; vertical_order_contradicts_predicate` |
| `qwen_vl_case_016` | `semantic_and_geometry_failure` | `relative_vertical` | `lower than` | pillow -> floor | `promoted_into_top50` | 93 -> 12 | 0.9979 | `point_subtype_delegated_to_obb_for_family; vertical_order_contradicts_predicate` |
| `qwen_vl_case_005` | `geometry_contradiction` | `relative_vertical` | `lower than` | heater -> floor | `promoted_into_top100` | 146 -> 69 | 0.9998 | `point_subtype_delegated_to_obb_for_family; vertical_order_contradicts_predicate` |
| `qwen_vl_case_021` | `semantic_and_geometry_failure` | `support_contact` | `supported by` | pillow -> floor | `promoted_into_top50` | 86 -> 9 | 0.9988 | `positive_float_gap_large; subtype_soft_support_contact` |
| `qwen_vl_case_017` | `semantic_and_geometry_failure` | `relative_vertical` | `higher than` | tv -> wall | `promoted_into_top100` | 129 -> 64 | 0.8711 | `point_subtype_delegated_to_obb_for_family; vertical_order_contradicts_predicate` |
| `qwen_vl_case_022` | `semantic_and_geometry_failure` | `support_contact` | `supported by` | pillow -> floor | `promoted_into_top100` | 124 -> 67 | 0.9718 | `positive_float_gap_large; subtype_soft_support_contact` |
| `qwen_vl_case_006` | `geometry_contradiction` | `relative_vertical` | `higher than` | heater -> wall | `stayed_in_topk` | 96 -> 51 | 0.9096 | `point_subtype_delegated_to_obb_for_family; vertical_order_contradicts_predicate` |
| `qwen_vl_case_010` | `geometry_contradiction` | `support_contact` | `supported by` | ceiling -> wall | `stayed_in_topk` | 91 -> 57 | 0.8021 | `horizontal_plane_found; plane_gap_large; subtype_rigid_object_on_furniture` |

## Residual Calibration Risk Cases

| case | category | family | predicate | pair | transition | sem -> geom rank | p_geom_valid | reason |
| --- | --- | --- | --- | --- | --- | ---: | ---: | --- |
| `qwen_vl_case_005` | `geometry_contradiction` | `relative_vertical` | `lower than` | heater -> floor | `promoted_into_top100` | 146 -> 69 | 0.9998 | `point_subtype_delegated_to_obb_for_family; vertical_order_contradicts_predicate` |
| `qwen_vl_case_021` | `semantic_and_geometry_failure` | `support_contact` | `supported by` | pillow -> floor | `promoted_into_top50` | 86 -> 9 | 0.9988 | `positive_float_gap_large; subtype_soft_support_contact` |
| `qwen_vl_case_004` | `geometry_contradiction` | `relative_vertical` | `lower than` | towel -> shower | `promoted_into_top50` | 118 -> 21 | 0.9983 | `point_subtype_delegated_to_obb_for_family; vertical_order_contradicts_predicate` |
| `qwen_vl_case_016` | `semantic_and_geometry_failure` | `relative_vertical` | `lower than` | pillow -> floor | `promoted_into_top50` | 93 -> 12 | 0.9979 | `point_subtype_delegated_to_obb_for_family; vertical_order_contradicts_predicate` |
| `qwen_vl_case_009` | `geometry_contradiction` | `support_contact` | `supported by` | box -> wardrobe | `promoted_into_top50` | 51 -> 20 | 0.9975 | `horizontal_plane_found; plane_gap_large; subtype_rigid_object_on_furniture` |
| `qwen_vl_case_022` | `semantic_and_geometry_failure` | `support_contact` | `supported by` | pillow -> floor | `promoted_into_top100` | 124 -> 67 | 0.9718 | `positive_float_gap_large; subtype_soft_support_contact` |
| `qwen_vl_case_006` | `geometry_contradiction` | `relative_vertical` | `higher than` | heater -> wall | `stayed_in_topk` | 96 -> 51 | 0.9096 | `point_subtype_delegated_to_obb_for_family; vertical_order_contradicts_predicate` |

## Family Mechanism Examples

| case | category | family | predicate | pair | transition | sem -> geom rank | p_geom_valid | reason |
| --- | --- | --- | --- | --- | --- | ---: | ---: | --- |
| `qwen_vl_case_001` | `geometry_contradiction` | `proximity` | `close by` | vase -> bread | `demoted_out_of_top50` | 22 -> 91 | 0.2691 | `far_in_normalized_xy; point_subtype_delegated_to_obb_for_family` |
| `qwen_vl_case_011` | `semantic_and_geometry_failure` | `proximity` | `close by` | socket -> pack | `demoted_out_of_top50` | 12 -> 66 | 0.03689 | `far_in_normalized_xy; point_subtype_delegated_to_obb_for_family` |
| `qwen_vl_case_014` | `semantic_and_geometry_failure` | `relative_vertical` | `higher than` | floor -> wall | `demoted_out_of_top50` | 2 -> 153 | 0.04381 | `point_subtype_delegated_to_obb_for_family; vertical_order_contradicts_predicate` |
| `qwen_vl_case_024` | `semantic_and_geometry_failure` | `relative_vertical` | `higher than` | floor -> wall | `demoted_out_of_top50` | 4 -> 132 | 0.0169 | `point_subtype_delegated_to_obb_for_family; vertical_order_contradicts_predicate` |
| `qwen_vl_case_019` | `semantic_and_geometry_failure` | `support_contact` | `supported by` | floor -> wall | `demoted_out_of_top50` | 4 -> 127 | 0.04783 | `horizontal_plane_found; plane_gap_large; subtype_rigid_object_on_furniture` |
| `qwen_vl_case_020` | `semantic_and_geometry_failure` | `support_contact` | `supported by` | box -> window | `demoted_out_of_top100` | 60 -> 142 | 0.003945 | `horizontal_plane_found; plane_gap_large; subtype_rigid_object_on_furniture` |

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

- `inspection_json`: `experiments/H001_geom_reliability/sources/qwen_vl/failure_cases/inspection.json`
- `inspection_md`: `experiments/H001_geom_reliability/sources/qwen_vl/failure_cases/inspection.md`

## Claim Boundary

qualitative reviewer-defense artifact only; not a new metric, not a visual audit, and not evidence beyond measured H001-family scope
