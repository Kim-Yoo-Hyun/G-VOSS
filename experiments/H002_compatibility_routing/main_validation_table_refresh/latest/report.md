# H002 Main Validation Table Refresh After Lateral Lock

## Status

```text
status = h002_main_validation_table_refresh_after_lateral_lock_ready
validation_errors = 0
main_rows = 13
appendix_rows = 13
selected_path = main_appendix_table_refreshed_after_lateral_lock
next_todo = none_scoped_h002_outputs_ready
```

## Table Placement

| route | relations | placement | status | reason |
| --- | --- | --- | --- | --- |
| predicate_geometry_comparison | higher/lower, bigger/smaller | main_table | main_validated | validated S2 source x C_e route with bootstrap CI and controls |
| caveated_lateral_compatibility | left/right | main_table_caveated_rows | caveated_main_validated | 15/20 win cells, no Violation regression, no recall-loss cell above 0.05, controls pass |
| frame_depth_ambiguity | front/behind | appendix_failure_analysis | failure_case | Violation improves, but Recall loss is too large; reference-frame/depth ambiguity remains |
| geometry_only_control | close by | appendix_or_analysis_control | control_route | geometry-only route is sufficient; not a T_e x G_e interaction success |
| hard_contact_pose | standing on, lying on, supported by | appendix_failure_taxonomy | diagnostic_failure | capacity and shortcut-controlled labels block support/contact solved claim |
| full_relative_horizontal | left/right/front/behind | not_single_main_route | blocked_as_whole | left/right and front/behind have different route behavior |

## Main Table Preview

| route | relations | source_scope | K | Delta_Recall@K | Delta_Recall_CI95 | Delta_Violation@K | Delta_Violation_CI95 | paper_role |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| predicate_geometry_comparison | higher/lower + bigger/smaller | VL-SAT + Open3DSG validation | 5 | 0.007937 | [-0.006049, 0.022589] | -0.240690 | [-0.254359, -0.227705] | main_validated_compatibility_route |
| predicate_geometry_comparison | higher/lower + bigger/smaller | VL-SAT + Open3DSG validation | 20 | 0.081633 | [0.048096, 0.118007] | -0.243091 | [-0.251882, -0.235094] | main_validated_compatibility_route |
| predicate_geometry_comparison | higher/lower + bigger/smaller | VL-SAT + Open3DSG validation | 50 | 0.103175 | [0.068924, 0.140698] | -0.259199 | [-0.266175, -0.252394] | main_validated_compatibility_route |
| predicate_geometry_comparison | higher/lower + bigger/smaller | VL-SAT + Open3DSG validation | 100 | 0.004535 | [0.000000, 0.011393] | -0.142873 | [-0.146752, -0.139429] | main_validated_compatibility_route |
| caveated_lateral_compatibility | left/right | open3dsg_recovery_relaxed_views_min2 | 20 | 0.269231 | [0.2351, 0.3027] | -0.466279 | [-0.4786, -0.4542] | caveated_main_lateral_route |
| caveated_lateral_compatibility | left/right | open3dsg_recovery_relaxed_views_min2 | 50 | 0.378011 | [0.3354, 0.4192] | -0.367407 | [-0.3821, -0.3509] | caveated_main_lateral_route |
| caveated_lateral_compatibility | left/right | open3dsg_recovery_relaxed_views_min2 | 100 | 0.097514 | [0.0634, 0.1291] | -0.102349 | [-0.1104, -0.0935] | caveated_main_lateral_route |
| caveated_lateral_compatibility | left/right | vlsat_full_validation | 20 | -0.043491 | [-0.0572, -0.0304] | -0.099909 | [-0.1106, -0.0888] | caveated_main_lateral_route |
| caveated_lateral_compatibility | left/right | vlsat_full_validation | 50 | -0.021308 | [-0.0329, -0.0116] | -0.124330 | [-0.1338, -0.1161] | caveated_main_lateral_route |
| caveated_lateral_compatibility | left/right | vlsat_full_validation | 100 | -0.002919 | [-0.0087, 0.0023] | -0.154892 | [-0.1605, -0.1492] | caveated_main_lateral_route |

## Appendix / Analysis Rows

| route | relations | source_scope | K | Delta_Recall@K | Delta_Violation@K | paper_role | interpretation |
| --- | --- | --- | --- | --- | --- | --- | --- |
| frame_depth_ambiguity | front/behind | open3dsg_recovery_relaxed_views_min2 | 10 | -0.002653 | -0.475128 | failure_case_appendix | Violation decreases, but Recall loss is too large for main success. |
| frame_depth_ambiguity | front/behind | open3dsg_recovery_relaxed_views_min2 | 20 | -0.060345 | -0.457409 | failure_case_appendix | Violation decreases, but Recall loss is too large for main success. |
| frame_depth_ambiguity | front/behind | open3dsg_recovery_relaxed_views_min2 | 50 | -0.170424 | -0.359159 | failure_case_appendix | Violation decreases, but Recall loss is too large for main success. |
| frame_depth_ambiguity | front/behind | open3dsg_recovery_relaxed_views_min2 | 100 | -0.137268 | -0.107204 | failure_case_appendix | Violation decreases, but Recall loss is too large for main success. |
| frame_depth_ambiguity | front/behind | vlsat_full_validation | 10 | -0.177246 | -0.280657 | failure_case_appendix | Violation decreases, but Recall loss is too large for main success. |
| frame_depth_ambiguity | front/behind | vlsat_full_validation | 20 | -0.203125 | -0.273084 | failure_case_appendix | Violation decreases, but Recall loss is too large for main success. |
| frame_depth_ambiguity | front/behind | vlsat_full_validation | 50 | -0.127441 | -0.237028 | failure_case_appendix | Violation decreases, but Recall loss is too large for main success. |
| frame_depth_ambiguity | front/behind | vlsat_full_validation | 100 | -0.066895 | -0.188074 | failure_case_appendix | Violation decreases, but Recall loss is too large for main success. |
| geometry_only_control | close by | open3dsg_recovery_relaxed_views_min2 | 20 | -0.001389 | -0.001330 | geometry_only_route_control | Proximity is geometry-decidable and supports relation-aware routing, not T_e x G_e interaction. |
| geometry_only_control | close by | open3dsg_recovery_relaxed_views_min2 | 50 | -0.002778 | -0.001265 | geometry_only_route_control | Proximity is geometry-decidable and supports relation-aware routing, not T_e x G_e interaction. |
| geometry_only_control | close by | vlsat_full_validation | 20 | 0.000000 | -0.000547 | geometry_only_route_control | Proximity is geometry-decidable and supports relation-aware routing, not T_e x G_e interaction. |
| geometry_only_control | close by | vlsat_full_validation | 50 | -0.002265 | -0.004551 | geometry_only_route_control | Proximity is geometry-decidable and supports relation-aware routing, not T_e x G_e interaction. |

## Interpretation

`left/right` is now included as a caveated lateral main validated route.
`front/behind` remains a reference-frame/depth ambiguity failure case. Full
`relative_horizontal` is not a single solved route. Paper draft files were not
edited by this table refresh.
