# H002 R1 Close-By Geometry-Support Route Result Review

## Status

```text
artifact_root = artifacts/compatibility_dataset_v3_close_by_geometry_support_route_result_review/
status = h002_compatibility_dataset_v3_close_by_geometry_support_route_result_review_ready
selected_path = freeze_close_by_as_geometry_only_route_evidence_move_to_supported_by_decomposition
validation_errors = 0
next_todo = compatibility_dataset_v3_supported_by_decomposition_target_plan
```

## Decision

R1 `close by`는 `geometry-only learned/evaluated route`로 고정한다.

이 relation은 `T_e x G_e` interaction의 main evidence가 아니다. 대신 H002의
relation-aware routing claim에서 어떤 relation family는 `G_e`만으로 충분하고,
복잡한 semantic-geometry interaction을 강제하면 안 된다는 control/evidence 역할을
한다.

## Key Metrics

| Control | AUROC | Best Accuracy | Interpretation |
| --- | ---: | ---: | --- |
| `distance_xy` | 0.999556 | 0.992500 | raw XY distance nearly solves geometry support |
| `distance_3d` | 0.998975 | 0.987500 | raw 3D distance nearly solves geometry support |
| `normalized_distance_xy` | 1.000000 | 1.000000 | scale-normalized XY distance solves the route target |
| `normalized_distance_3d` | 1.000000 | 1.000000 | scale-normalized 3D distance solves the route target |
| `overlap_geometry` | 0.892500 | 0.892500 | useful but weaker geometry support cue |
| `source_score_rank` | 0.552103 | 0.546250 | source confidence does not explain geometry support |
| `class_pair_only` | n/a | 0.503750 | class-pair shortcut is near chance |
| `p_geom_valid_hidden_baseline` | 0.999594 | 0.991250 | hidden geometry-rule reference is strong but not model input |
| `shuffled_G` | 0.336178 | 0.500000 | shuffled geometry collapses |
| `wrong_pair_geometry` | 0.006272 | 0.500000 | wrong-pair geometry collapses |

## Claim Boundary

Allowed:

- `close by` is geometry-decidable under the current R1 target.
- Pair-specific distance/geometry is required because shuffled/wrong-pair controls collapse.
- R1 supports the broader claim that relation families require different evidence routes.

Blocked:

- `close by` proves predicate-geometry interaction.
- `close by` alone proves calibrated `p_rel` / `p_obs`.
- hidden `p_geom_valid` is model-safe input.
- R1 alone is paper-level held-out evidence.

## Next

```text
compatibility_dataset_v3_supported_by_decomposition_target_plan
```
