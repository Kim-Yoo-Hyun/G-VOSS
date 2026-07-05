# H002 R6 Supported-By Decomposition Smoke Plan

## Status

```text
artifact_root = artifacts/compatibility_dataset_v3_supported_by_decomposition_smoke_plan/
status = h002_compatibility_dataset_v3_supported_by_decomposition_smoke_plan_ready
validation_errors = 0
learned_smoke_executed = false
next_todo = compatibility_dataset_v3_supported_by_decomposition_smoke_runner
```

## Runner-Ready Rows

```text
rows = 320
accept_broad_support = 80
relabel_to_subtype = 80
reject_no_support = 80
abstain = 80
p_obs = observable 240 / abstain 80
p_rel_binary = accept_or_relabel 160 / reject 80
p_rel_3way = accept_broad_support 80 / relabel_to_subtype 80 / reject_no_support 80
cv_groups = 257
mixed_label_cv_groups = 39
feature_blocks = T_e + G_e_mesh_pose_contact + Q_e
```

## Planned Tasks

- `T0_decomposition_4way`: broad accept / relabel / reject / abstain.
- `T1_p_obs_binary`: observable versus abstain.
- `T2_p_rel_binary_observable`: accept-or-relabel versus reject after abstain removal.
- `T3_p_rel_3way_observable`: accept / relabel / reject among observable rows.

## Planned Comparisons

- `M1_T_class_only`
- `M2_G_geometry_only`
- `M3_Q_observability_only`
- `M4_TG_concat`
- `M5_GQ_route`
- `M6_TGQ_factorized_route`

## Required Controls

- shuffled `G_e` global
- shuffled `G_e` within class-pair
- shuffled `Q_e`
- `Q_e`-only on observable `p_rel`
- class-pair slice metrics
- hidden source/rank/`p_geom_valid` audit probes
- hidden construction-field audit probes

## Boundary

This is a plan only. It does not train a model and does not report learned
performance. Hidden construction fields, source score/rank, H001 `p_geom_valid`,
GT match fields, and audit reasons remain outside model input.
