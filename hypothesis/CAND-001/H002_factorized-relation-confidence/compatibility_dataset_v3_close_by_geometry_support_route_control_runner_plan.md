# H002 R1 Close-By Geometry-Support Route Control Runner Plan

Date: 2026-06-30 KST

## Status

```text
artifact_root = artifacts/compatibility_dataset_v3_close_by_geometry_support_route_control_runner_plan/
status = h002_compatibility_dataset_v3_close_by_geometry_support_route_control_runner_plan_ready
selected_path = plan_r1_close_by_geometry_only_route_controls_no_interaction_runner
validation_errors = 0
planned_controls = 12
next_todo = compatibility_dataset_v3_close_by_geometry_support_route_control_runner
```

## Purpose

This step plans the deterministic control runner for the R1 `close by`
geometry-support route. It does not run metrics and does not train a model.

The runner is constrained to report `close by` as a geometry-only
learned/evaluated route. Distance dominance is expected for this route and must
not be promoted to `T_e x G_e` interaction evidence.

## Planned Controls

| Control | Source | Role |
| --- | --- | --- |
| `distance_xy` | `G_e_route.distance_xy` | raw XY distance baseline |
| `distance_3d` | `G_e_route.distance_3d` | raw 3D distance baseline |
| `normalized_distance_xy` | `G_e_route.normalized_distance_xy` | primary scale-normalized route evidence |
| `normalized_distance_3d` | `G_e_route.normalized_distance_3d` | 3D scale-normalized diagnostic |
| `overlap_geometry` | `projected_iou_xy`, overlap ratios | secondary geometry diagnostic |
| `scale_control` | raw vs normalized distance, extent proxies | separates distance from object-scale effects |
| `coverage_control` | `Q_e_observability`, subsets | keeps abstain/audit rows out of binary metric |
| `source_score_rank` | `Z_e_source_baseline` | source/rank baseline only |
| `class_pair_only` | hidden class pair | audit-only shortcut probe |
| `p_geom_valid_hidden_baseline` | hidden `p_geom_valid` | reference diagnostic only |
| `shuffled_G` | permuted `G_e_route` | pair-specific geometry control |
| `wrong_pair_geometry` | different-pair `G_e_route` | object-pair alignment control |

## Metrics To Run Next

- AUROC over `geometry_support_binary` on primary rows;
- best-threshold accuracy;
- F1 at best threshold;
- coverage counts for all rows;
- control drop for shuffled-G and wrong-pair geometry;
- wording gate: output must say geometry-only route, not interaction evidence.

## Boundary

- Train-only plan.
- No validation/test used.
- No metric runner yet.
- No model run.
- No H001 artifact modified.
- Learned interaction smoke remains blocked for R1.
- Paper-level claim remains blocked from this plan alone.

## Next

```text
compatibility_dataset_v3_close_by_geometry_support_route_control_runner
```
