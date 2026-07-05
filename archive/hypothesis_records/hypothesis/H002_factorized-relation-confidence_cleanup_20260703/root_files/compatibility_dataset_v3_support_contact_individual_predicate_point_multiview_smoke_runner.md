# H002 Support/Contact Individual Predicate Point/Multiview Smoke Runner

## Status

```text
artifact_root = artifacts/compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_smoke_runner/
status = h002_compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_smoke_runner_diagnostic_only_failed_controls
rows = 640
positive / negative = 320 / 320
predicate_counts = lying on 320 / standing on 320
cv_groups = 258
mixed_label_cv_groups = 155
validation_errors = 0
primary_model = M8_TG_point_contact_interaction
next_todo = compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_failure_analysis
```

## Main Metrics

| Model | AUROC | Role |
| --- | ---: | --- |
| `M1_semantic_only_T` | 0.442480 | semantic/content shortcut baseline |
| `M2_obb_geometry_only` | 0.464077 | old OBB-only geometry baseline |
| `M3_point_pose_only` | 0.494673 | point pose ablation |
| `M4_contact_patch_only` | 0.465952 | point contact ablation |
| `M5_point_contact_geometry` | 0.470249 | new geometry-only baseline |
| `M6_TG_obb_concat` | 0.430010 | old OBB T+G baseline |
| `M7_TG_point_contact_concat` | 0.434658 | plain point/contact fusion |
| `M8_TG_point_contact_interaction` | 0.699375 | primary predicate-geometry compatibility smoke |
| `M9_TGQ_factorized_observability` | 0.694619 | Q_e diagnostic extension |

Shortcut and control probes:

| Probe | AUROC | Interpretation |
| --- | ---: | --- |
| `S1_predicate_label_shortcut` | 0.422490 | no predicate-only shortcut |
| `S2_class_pair_shortcut` | 0.472783 | no class-pair shortcut |
| `S3_quality_only_shortcut` | 0.481484 | Q_e alone does not define target |
| `C1_wrong_T_same_G` | 0.273125 | wrong predicate strongly degrades/inverts |
| `C2_shuffled_G_global` | 0.506240 | shuffled geometry near chance |
| `C3_shuffled_G_within_predicate` | 0.463857 | within-predicate shuffled geometry near chance |
| `C4_shuffled_Q` | 0.699297 | Q_e alignment has negligible effect over M8 |

## Gate Result

The smoke is diagnostic-only because the frozen primary signal gate required
`M8 AUROC >= 0.70`, while the observed value is `0.699375`.

Other promotion-relevant gates passed:

- `M8` strongly beats semantic-only, OBB-only, point-only, contact-only, and point+contact geometry-only baselines.
- `M8` beats old OBB T+G (`M6`) by `0.269365` AUROC.
- `M8` beats plain point/contact concat (`M7`) by `0.264717` AUROC.
- geometry-only dominance is not observed: `M8 - M5 = 0.229126`.
- wrong-T and shuffled-G controls degrade as expected.
- `Q_e` does not rescue a weak `C_e` target; `M9` is slightly below `M8`.

Predicate slices:

```text
lying on:
  M8 AUROC = 0.692578
  M9 AUROC = 0.687305

standing on:
  M8 AUROC = 0.707930
  M9 AUROC = 0.704922
```

## Interpretation

This result is not a clean pass, but it is much stronger than the previous
OBB-only support/contact individual-predicate smoke. The useful signal is not
raw geometry-only evidence; it appears when predicate content modulates
point-derived pose/contact geometry.

The blocker is now narrow: the aggregate primary AUROC misses the fixed `0.70`
gate by `0.000625`, and the weaker slice is `lying on`. The next step should
therefore analyze which `lying on` cases are failing, whether failures come from
pose ambiguity, point crop quality, class-pair distribution, thresholding, or
feature design, and whether this branch should be treated as near-threshold
diagnostic evidence or repaired with a better feature/target design.

## Boundary

- train-only grouped-CV hypothesis smoke
- no validation/test usage
- no paper-level evidence
- no H001 artifact modification
- multiview is used as audit/`Q_e` metadata, not as learned visual input

## Outputs

```text
summary.json
metrics.json
metrics_by_predicate.json
gate_results.json
group_contrast_margins.json
predictions.jsonl
error_cases_m8.jsonl
validation_errors.jsonl
report.md
```
