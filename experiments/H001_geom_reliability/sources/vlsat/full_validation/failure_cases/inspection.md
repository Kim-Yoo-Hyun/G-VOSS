# VL-SAT full-validation Qualitative Failure Case Inspection

Status: `qualitative_case_inspection_ready`
Created at: `2026-06-05T01:26:15.978192+00:00`

## Scope

This report inspects the sampled VL-SAT full-validation qualitative queue generated from real prediction, GT, geometry, and metric joins.
It does not add a metric and does not perform an independent visual audit.

## Inspection Verdict

- The queue supports the H001 failure mechanism: semantically plausible relation predictions can be physically inconsistent at the relation/object-pair level.
- The failure pattern is family-structured rather than a generic score artifact.
- Geometry-aware reranking also has promotion/retention cases, so paper wording must report recall and violation jointly.
- Some violated cases still receive high calibrated probability, so rule-verified and probabilistic variants must remain separate in tables.
- No taxonomy change is made in this inspection.

## Counts

- selected cases: `36`
- demoted by geometry-aware reranking: `28`
- promoted or retained by geometry-aware reranking: `8`
- violated but p_geom_valid > 0.9: `7`
- p_geom_valid range: `1.613e-11` to `0.9988`
- semantic rank range: `23` to `160`
- geometry rank range: `44` to `400`

### By Category

- `geometry_contradiction`: 14
- `semantic_and_geometry_failure`: 22

### By Family

- `proximity`: 6
- `relative_vertical`: 20
- `support_contact`: 10

### By Reason Code

- `far_in_normalized_xy`: 6
- `furniture_support_object`: 1
- `horizontal_plane_found`: 5
- `plane_gap_large`: 5
- `point_subtype_delegated_to_obb_for_family`: 26
- `positive_float_gap_large`: 5
- `subtype_rigid_object_on_furniture`: 5
- `subtype_soft_support_contact`: 5
- `vertical_order_contradicts_predicate`: 20

## Mechanism Notes

- `semantic_plausibility_can_conflict_with_geometry`: 28 of 36 selected cases are demoted by geometry-aware reranking. Several have semantic top-50 ranks but low p_geom_valid or explicit geometry reason codes.
- `failure_is_family_structured`: proximity failures concentrate in far_in_normalized_xy; relative_vertical failures concentrate in vertical_order_contradicts_predicate; support_contact failures expose float-gap or support-plane contradictions.
- `reranking_has_recall_tradeoff_cases`: 8 selected cases are promoted or retained by geometry-aware ranking. These are useful for explaining why the paper must report recall and violation jointly.
- `calibration_is_not_equivalent_to_hard_rule_validity`: 7 selected cases are rule-violated but have p_geom_valid > 0.9. These residual cases justify reporting rule-verified, probabilistic, and family-specific variants separately.
- `qualitative_queue_is_not_a_human_audit`: The queue is deterministic diagnostic evidence from prediction/GT/geometry joins. It should guide figure selection and failure narratives, not be reported as a representative visual audit.

## Representative Demotions

| case | category | family | predicate | pair | transition | sem -> geom rank | p_geom_valid | reason |
| --- | --- | --- | --- | --- | --- | ---: | ---: | --- |
| `vlsat_case_018` | `semantic_and_geometry_failure` | `relative_vertical` | `lower than` | lamp -> toilet paper dispenser | `demoted_out_of_top100` | 92 -> 400 | 8.988e-09 | `point_subtype_delegated_to_obb_for_family; vertical_order_contradicts_predicate` |
| `vlsat_case_004` | `geometry_contradiction` | `relative_vertical` | `lower than` | box -> box | `demoted_out_of_top50` | 44 -> 338 | 3.603e-07 | `point_subtype_delegated_to_obb_for_family; vertical_order_contradicts_predicate` |
| `vlsat_case_027` | `semantic_and_geometry_failure` | `relative_vertical` | `lower than` | shelf -> trash can | `demoted_out_of_top100` | 80 -> 374 | 2.864e-08 | `point_subtype_delegated_to_obb_for_family; vertical_order_contradicts_predicate` |
| `vlsat_case_028` | `semantic_and_geometry_failure` | `relative_vertical` | `higher than` | table -> ceiling | `demoted_out_of_top100` | 91 -> 375 | 2.455e-08 | `point_subtype_delegated_to_obb_for_family; vertical_order_contradicts_predicate` |
| `vlsat_case_029` | `semantic_and_geometry_failure` | `relative_vertical` | `lower than` | light -> box | `demoted_out_of_top100` | 78 -> 361 | 1.075e-07 | `point_subtype_delegated_to_obb_for_family; vertical_order_contradicts_predicate` |
| `vlsat_case_030` | `semantic_and_geometry_failure` | `relative_vertical` | `higher than` | shoes -> ceiling | `demoted_out_of_top100` | 94 -> 367 | 2.848e-08 | `point_subtype_delegated_to_obb_for_family; vertical_order_contradicts_predicate` |
| `vlsat_case_031` | `semantic_and_geometry_failure` | `relative_vertical` | `higher than` | shoe rack -> wall | `demoted_out_of_top100` | 73 -> 328 | 5.951e-06 | `point_subtype_delegated_to_obb_for_family; vertical_order_contradicts_predicate` |
| `vlsat_case_032` | `semantic_and_geometry_failure` | `relative_vertical` | `higher than` | stand -> shelf | `demoted_out_of_top100` | 69 -> 313 | 5.666e-07 | `point_subtype_delegated_to_obb_for_family; vertical_order_contradicts_predicate` |

## Representative Promotion Or Retention Tradeoffs

| case | category | family | predicate | pair | transition | sem -> geom rank | p_geom_valid | reason |
| --- | --- | --- | --- | --- | --- | ---: | ---: | --- |
| `vlsat_case_007` | `geometry_contradiction` | `relative_vertical` | `lower than` | plant -> fireplace | `promoted_into_top100` | 160 -> 100 | 0.9988 | `point_subtype_delegated_to_obb_for_family; vertical_order_contradicts_predicate` |
| `vlsat_case_025` | `semantic_and_geometry_failure` | `support_contact` | `lying on` | plant -> floor | `promoted_into_top100` | 157 -> 98 | 0.9888 | `positive_float_gap_large; subtype_soft_support_contact` |
| `vlsat_case_020` | `semantic_and_geometry_failure` | `relative_vertical` | `lower than` | shelf -> tv stand | `promoted_into_top100` | 155 -> 100 | 0.9843 | `point_subtype_delegated_to_obb_for_family; vertical_order_contradicts_predicate` |
| `vlsat_case_012` | `geometry_contradiction` | `support_contact` | `lying on` | wall -> floor | `promoted_into_top100` | 118 -> 87 | 0.9754 | `positive_float_gap_large; subtype_soft_support_contact` |
| `vlsat_case_019` | `semantic_and_geometry_failure` | `relative_vertical` | `lower than` | blanket -> floor | `promoted_into_top50` | 67 -> 45 | 0.9957 | `point_subtype_delegated_to_obb_for_family; vertical_order_contradicts_predicate` |
| `vlsat_case_024` | `semantic_and_geometry_failure` | `support_contact` | `lying on` | toilet paper dispenser -> floor | `promoted_into_top50` | 65 -> 44 | 0.9453 | `positive_float_gap_large; subtype_soft_support_contact` |
| `vlsat_case_006` | `geometry_contradiction` | `relative_vertical` | `higher than` | lamp -> showcase | `promoted_into_top50` | 65 -> 48 | 0.7605 | `point_subtype_delegated_to_obb_for_family; vertical_order_contradicts_predicate` |
| `vlsat_case_011` | `geometry_contradiction` | `support_contact` | `supported by` | curtain -> wall | `promoted_into_top50` | 62 -> 47 | 0.9451 | `horizontal_plane_found; plane_gap_large; subtype_rigid_object_on_furniture` |

## Residual Calibration Risk Cases

| case | category | family | predicate | pair | transition | sem -> geom rank | p_geom_valid | reason |
| --- | --- | --- | --- | --- | --- | ---: | ---: | --- |
| `vlsat_case_007` | `geometry_contradiction` | `relative_vertical` | `lower than` | plant -> fireplace | `promoted_into_top100` | 160 -> 100 | 0.9988 | `point_subtype_delegated_to_obb_for_family; vertical_order_contradicts_predicate` |
| `vlsat_case_019` | `semantic_and_geometry_failure` | `relative_vertical` | `lower than` | blanket -> floor | `promoted_into_top50` | 67 -> 45 | 0.9957 | `point_subtype_delegated_to_obb_for_family; vertical_order_contradicts_predicate` |
| `vlsat_case_025` | `semantic_and_geometry_failure` | `support_contact` | `lying on` | plant -> floor | `promoted_into_top100` | 157 -> 98 | 0.9888 | `positive_float_gap_large; subtype_soft_support_contact` |
| `vlsat_case_020` | `semantic_and_geometry_failure` | `relative_vertical` | `lower than` | shelf -> tv stand | `promoted_into_top100` | 155 -> 100 | 0.9843 | `point_subtype_delegated_to_obb_for_family; vertical_order_contradicts_predicate` |
| `vlsat_case_012` | `geometry_contradiction` | `support_contact` | `lying on` | wall -> floor | `promoted_into_top100` | 118 -> 87 | 0.9754 | `positive_float_gap_large; subtype_soft_support_contact` |
| `vlsat_case_024` | `semantic_and_geometry_failure` | `support_contact` | `lying on` | toilet paper dispenser -> floor | `promoted_into_top50` | 65 -> 44 | 0.9453 | `positive_float_gap_large; subtype_soft_support_contact` |
| `vlsat_case_011` | `geometry_contradiction` | `support_contact` | `supported by` | curtain -> wall | `promoted_into_top50` | 62 -> 47 | 0.9451 | `horizontal_plane_found; plane_gap_large; subtype_rigid_object_on_furniture` |

## Family Mechanism Examples

| case | category | family | predicate | pair | transition | sem -> geom rank | p_geom_valid | reason |
| --- | --- | --- | --- | --- | --- | ---: | ---: | --- |
| `vlsat_case_015` | `semantic_and_geometry_failure` | `proximity` | `close by` | coffee table -> ceiling | `demoted_out_of_top100` | 84 -> 234 | 3.279e-05 | `far_in_normalized_xy; point_subtype_delegated_to_obb_for_family` |
| `vlsat_case_014` | `semantic_and_geometry_failure` | `proximity` | `close by` | bookshelf -> ceiling | `demoted_out_of_top50` | 46 -> 85 | 0.02351 | `far_in_normalized_xy; point_subtype_delegated_to_obb_for_family` |
| `vlsat_case_018` | `semantic_and_geometry_failure` | `relative_vertical` | `lower than` | lamp -> toilet paper dispenser | `demoted_out_of_top100` | 92 -> 400 | 8.988e-09 | `point_subtype_delegated_to_obb_for_family; vertical_order_contradicts_predicate` |
| `vlsat_case_004` | `geometry_contradiction` | `relative_vertical` | `lower than` | box -> box | `demoted_out_of_top50` | 44 -> 338 | 3.603e-07 | `point_subtype_delegated_to_obb_for_family; vertical_order_contradicts_predicate` |
| `vlsat_case_023` | `semantic_and_geometry_failure` | `support_contact` | `standing on` | vase -> pack | `demoted_out_of_top100` | 100 -> 294 | 1.362e-05 | `horizontal_plane_found; plane_gap_large; subtype_rigid_object_on_furniture` |
| `vlsat_case_022` | `semantic_and_geometry_failure` | `support_contact` | `standing on` | lamp -> shoes | `demoted_out_of_top50` | 49 -> 151 | 0.0004093 | `horizontal_plane_found; plane_gap_large; subtype_rigid_object_on_furniture` |

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

- `inspection_json`: `experiments/H001_geom_reliability/sources/vlsat/full_validation/failure_cases/inspection.json`
- `inspection_md`: `experiments/H001_geom_reliability/sources/vlsat/full_validation/failure_cases/inspection.md`

## Claim Boundary

qualitative reviewer-defense artifact only; not a new metric, not a visual audit, and not evidence beyond measured H001-family scope
