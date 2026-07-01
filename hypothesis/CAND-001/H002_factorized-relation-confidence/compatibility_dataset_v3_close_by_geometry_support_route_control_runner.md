# H002 R1 Close-By Geometry-Support Route Control Runner

Date: 2026-06-30 KST

## Status

```text
artifact_root = artifacts/compatibility_dataset_v3_close_by_geometry_support_route_control_runner/
status = h002_compatibility_dataset_v3_close_by_geometry_support_route_control_runner_ready
selected_path = ran_r1_close_by_geometry_only_route_controls_no_interaction_model
validation_errors = 0
next_todo = compatibility_dataset_v3_close_by_geometry_support_route_result_review
```

## Purpose

This step runs deterministic controls for the R1 `close by` geometry-support
route. It does not train a model and does not run learned interaction smoke.

## Main Results

| Control | AUROC | Best Accuracy | Interpretation |
| --- | ---: | ---: | --- |
| `distance_xy` | 0.999556 | 0.992500 | raw XY distance nearly solves geometry support |
| `distance_3d` | 0.998975 | 0.987500 | raw 3D distance nearly solves geometry support |
| `normalized_distance_xy` | 1.000000 | 1.000000 | scale-normalized XY distance solves the route target |
| `normalized_distance_3d` | 1.000000 | 1.000000 | scale-normalized 3D distance solves the route target |
| `overlap_geometry` | 0.892500 | 0.892500 | overlap is useful but weaker than distance |
| `source_score_rank` | 0.552103 | 0.546250 | source confidence does not explain geometry support |
| `class_pair_only` | n/a | 0.503750 | class-pair shortcut is near chance |
| `p_geom_valid_hidden_baseline` | 0.999594 | 0.991250 | hidden geometry-rule reference is strong |
| `shuffled_G` | 0.336178 | 0.500000 | shuffled geometry collapses |
| `wrong_pair_geometry` | 0.006272 | 0.500000 | wrong-pair geometry collapses |

Scale control:

```text
primary raw distance AUROC = 0.999556
primary normalized distance AUROC = 1.000000
combined raw distance AUROC = 0.973713
combined normalized distance AUROC = 1.000000
```

Coverage:

```text
primary_binary = 800
raw_distance_diagnostic = 240
abstain_qe = 240
diagnostic_only = 4
q_e_complete_rows = 1284
```

## Interpretation

This confirms the route-specific interpretation:

- `close by` is a geometry-only route.
- Distance dominance is expected and useful here.
- Source score/rank does not explain the geometry-support label.
- Class-pair shortcut is near chance.
- Shuffled-G and wrong-pair geometry collapse, so the route uses pair-specific geometry.
- This is not `T_e x G_e` interaction evidence.

## Boundary

- Train-only deterministic controls.
- No validation/test used.
- No learned model trained.
- No paper-level claim from R1 alone.
- H001 artifacts were not modified.

## Next

```text
compatibility_dataset_v3_close_by_geometry_support_route_result_review
```
