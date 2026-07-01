# Compatibility Dataset V3 Sanitized View Smoke Runner

Date: 2026-06-26 KST

## Status

```text
status = h002_compatibility_dataset_v3_sanitized_view_smoke_runner_passed_controls
artifact_root = artifacts/compatibility_dataset_v3_sanitized_view_smoke_runner/
input_source = artifacts/compatibility_dataset_v3_schema_shortcut_audit/smoke_ready_view.jsonl
rows = 400
positive / negative = 200 / 200
paired_groups = 200
validation_errors = 0
epochs = 120
next = compatibility_dataset_v3_result_review_and_family_extension_decision
```

This is a train-only grouped-CV hypothesis smoke. It is not paper-level evidence.

## What Was Tested

The v3 target asks whether the same predicate-independent geometry evidence `G_e` can be interpreted
differently depending on semantic relation content `T_e`.

The target construction is:

```text
same directed object pair + same G_e + higher than = one compatibility label
same directed object pair + same G_e + lower than = opposite compatibility label
```

The primary model is:

```text
M5b_compatibility_TG_interaction
```

It uses clean `T_e + G_e` plus predicate-conditioned vertical interaction features:

```text
expected_z_sign(predicate) * center_delta_z_m
expected_z_sign(predicate) * normalized_center_delta_z
```

Wrong-T and shuffled-G controls are inference-time corruptions of the primary trained view. They are
not separately re-trained corrupted models.

## Main Metrics

| View | AUROC | Interpretation |
| --- | ---: | --- |
| `M1_source_only_Z_safe` | 0.525975 | source score/rank is near chance |
| `M2_semantic_only_T` | 0.445225 | semantic fields alone are below chance/near chance |
| `M3_semantic_source_TZ_safe` | 0.515800 | semantic + source remains near chance |
| `M4_geometry_only_G` | 0.500000 | same-G construction blocks geometry-only solution |
| `M5a_compatibility_TG_concat` | 0.446300 | plain concat does not solve the target |
| `M5b_compatibility_TG_interaction` | 1.000000 | predicate-conditioned compatibility solves the target |
| `M6_factorized_sanitized_TZGQ_interaction` | 1.000000 | factorized ablation also solves because it contains `M5b` |
| `S1_predicate_label_shortcut` | 0.446000 | predicate label alone is not enough |
| `S2_object_pair_shortcut` | 0.500000 | object-pair text alone is not enough |
| `S3_source_score_rank_shortcut` | 0.445725 | source scalar shortcut is not enough |
| `C1_wrong_T_same_G_control` | 0.000000 | swapping predicate inverts the primary signal |
| `C2_shuffled_G_global_control` | 0.477713 | globally shuffled geometry falls near chance |
| `C3_shuffled_G_within_predicate_control` | 0.515400 | within-predicate shuffled geometry stays near chance |

Paired score result:

```text
mean positive-minus-negative score = 0.812703
positive drop fraction = 1.0
```

## Gate Result

```text
data_integrity = pass
shortcut_baselines_near_chance = pass
primary_compatibility_success = pass
interaction_over_plain_concat = pass
wrong_T_same_G_degradation = pass
shuffled_G_degradation = pass
paired_score_drop = pass
overall = pass
```

## Interpretation

This is the first clean positive result for the new H002 direction. Earlier v2 failed because the
target was solvable as generic geometry perturbation detection. In v3, `G_e` alone is exactly chance
because both rows in a group share identical geometry. The signal appears only when predicate
semantics and signed vertical geometry are combined through an explicit compatibility interaction.

This supports the core H002 mechanism:

```text
semantic content and predicate-independent geometry evidence must be separated,
then recombined through a predicate-geometry compatibility function.
```

However, the result is still scoped:

- current primary family is only `relative_vertical`;
- the target uses a clean signed-vertical rule, so the result is expected to be easier than
  attachment/contact relations;
- `M6` is not independent evidence for final `p_rel` or `p_obs`, because this smoke mainly tests
  `C_e`;
- paper-level claims still require broader family review, stronger natural candidates, and Docker
  reproduction if promoted.

## Next Decision

The next step is not to immediately claim broad relation reliability. The next step is:

```text
compatibility_dataset_v3_result_review_and_family_extension_decision
```

That decision should answer:

1. whether v3 is enough as a clean mechanism proof for `C_e`;
2. whether to expand to additional relation families;
3. whether support/contact needs role/orientation or visual/mesh evidence before another smoke;
4. whether this branch should proceed toward a paper-level experiment root or remain hypothesis-stage.
