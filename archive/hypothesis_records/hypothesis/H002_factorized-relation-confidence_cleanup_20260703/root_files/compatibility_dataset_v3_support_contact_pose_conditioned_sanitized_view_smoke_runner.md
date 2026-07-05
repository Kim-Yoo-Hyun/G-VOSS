# Compatibility Dataset V3 Support/Contact Pose-Conditioned Sanitized View Smoke Runner

## Status

```text
status = h002_compatibility_dataset_v3_support_contact_pose_conditioned_sanitized_view_smoke_runner_passed_controls
artifact_root = artifacts/compatibility_dataset_v3_support_contact_pose_conditioned_sanitized_view_smoke_runner/
rows = 400
positive / negative = 200 / 200
paired_groups = 200
validation_errors = 0
overall = support_contact_pose_conditioned_smoke_passed_controls
next_todo = compatibility_dataset_v3_support_contact_pose_conditioned_result_review
```

This is a train-only grouped-CV hypothesis smoke. It is not paper-level evidence and does not use
validation or test rows.

## Input

```text
plan = artifacts/compatibility_dataset_v3_support_contact_pose_conditioned_sanitized_view_smoke_plan/
model_input = artifacts/compatibility_dataset_v3_support_contact_pose_conditioned_schema_shortcut_audit/smoke_ready_view.jsonl
```

The runner reads only `feature_blocks` from `smoke_ready_view.jsonl`. Raw candidate rows, hidden
manifests, row ids, anchor ids, scan ids, visible pairs, queue kinds, source predicates, hidden pose
state, and geometry hashes are not model features.

## Metrics

| Model | AUROC | AUPRC | Accuracy | Balanced Acc. |
| --- | ---: | ---: | ---: | ---: |
| `M1_source_only_Z_safe` | 0.500 | 0.506 | 0.500 | 0.500 |
| `M2_semantic_only_T` | 0.382 | 0.428 | 0.410 | 0.410 |
| `M3_semantic_source_TZ_safe` | 0.382 | 0.428 | 0.410 | 0.410 |
| `M4_geometry_only_G` | 0.500 | 0.506 | 0.500 | 0.500 |
| `M5a_compatibility_TG_concat` | 0.382 | 0.428 | 0.410 | 0.410 |
| `M5b_compatibility_TG_pose_interaction` | 1.000 | 1.000 | 1.000 | 1.000 |
| `M6_factorized_sanitized_TZGQ_pose_interaction` | 1.000 | 1.000 | 1.000 | 1.000 |
| `S1_predicate_label_shortcut` | 0.382 | 0.428 | 0.410 | 0.410 |
| `S2_object_pair_shortcut` | 0.500 | 0.506 | 0.500 | 0.500 |
| `S3_quality_shortcut` | 0.500 | 0.506 | 0.500 | 0.500 |
| `C1_wrong_T_same_G_control` | 0.000 | 0.308 | 0.000 | 0.000 |
| `C2_shuffled_G_global_control` | 0.525 | 0.535 | 0.510 | 0.510 |
| `C3_shuffled_G_within_predicate_control` | 0.568 | 0.565 | 0.560 | 0.560 |

## Gates

```text
data_integrity = pass
shortcut_baselines_near_chance = pass
primary_compatibility_success = pass
interaction_over_plain_concat = pass
wrong_T_same_G_degradation = pass
shuffled_G_degradation = pass
paired_score_margin = pass
overall_pass = true
```

Key gate values:

```text
best_noncompat_AUROC = 0.500
M5b_AUROC = 1.000
M5b_gain_over_best_noncompat = 0.500
M5a_AUROC = 0.382
wrong_T_AUROC = 0.000
best_shuffled_G_AUROC = 0.568
paired_mean_positive_minus_negative = 0.915326
paired_positive_margin_fraction = 1.000
```

## Interpretation

This smoke gives the first clean support/contact evidence for the current H002 direction:

```text
same G_e + different T_e -> different compatibility decision
```

The result is strong because source-only, semantic-only, geometry-only, object-pair-only, and
quality-only baselines stay near chance, while the predicate-conditioned pose interaction model
passes. The wrong-T control inverts the decision, and shuffled-G controls return near chance,
supporting that the model is using aligned predicate-geometry compatibility rather than metadata or
single-factor shortcuts.

`M6` matches `M5b`, but it is an ablation here. This stage primarily tests `C_e`, not final
`p_rel/p_obs` reliability.

The ECE values in the current helper are diagnostic only and not used as gates; calibration should
be revisited in the result review if this branch is promoted.

## Boundary

```text
split = train_internal_grouped_by_cv_group_id
validation_usage = false
test_usage = false
paper_evidence_allowed = false
h001_artifacts_modified = false
```

Next:

```text
compatibility_dataset_v3_support_contact_pose_conditioned_result_review
```
