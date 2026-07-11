# H002 Qualitative Evidence Package

## Purpose

This package supports the scoped H002 paper claim with row-pattern examples and locked route summaries. It does not change the score, route scope, or paper claim.

## Candidate-Level Cases

| case_id | evidence_level | source_id | route_family | subroute | predicate_label | score_id | rank | K | gt_exact_match | violation_status | interpretation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| comparison_source_violation_filtered_by_scomp | selected_prediction_row | open3dsg_recovery_relaxed_views_min2 | size_relative |  | bigger than | S0_source_score | 1 | 100 | False | violated | A source-selected comparison candidate is GT-negative and geometry-violated; it drops out of the S_comp top-20 set. |
| comparison_gt_match_promoted_by_scomp | selected_prediction_row | open3dsg_recovery_relaxed_views_min2 | relative_vertical |  | higher than | S2_source_x_Ce | 3 | 100 | True | satisfied | A comparison candidate selected by S_comp is GT-positive and geometry-satisfied but absent from the source-score top-20 set. |
| comparison_scomp_satisfied_selection | selected_prediction_row | vlsat_full_validation | relative_vertical |  | higher than | S2_source_x_Ce | 1 | 100 | True | satisfied | S_comp selects a geometry-satisfied comparison candidate, illustrating the Recall-Violation tradeoff target. |
| support_contact_diagnostic_only_row | selected_prediction_row_boundary | open3dsg_recovery_relaxed_views_min2 | support_contact |  | standing on | S0_source_score | 1 | 100 | True | diagnostic_only | Support/contact rows are present in the source pool, but the current violation target is diagnostic-only and not promoted. |
| left_right_source_violation_filtered_by_frame_route | selected_prediction_row | vlsat_full_validation | relative_horizontal | lateral_left_right | right | RH0_source_score | 1 |  | False | violated | A source-ranked left/right candidate is geometry-violated and is filtered out by the frame-aware lateral route. |
| left_right_gt_match_promoted_by_frame_route | selected_prediction_row | open3dsg_recovery_relaxed_views_min2 | relative_horizontal | lateral_left_right | left | RH1_source_x_frame_score | 1 |  | True | satisfied | The caveated left/right route promotes a GT-positive and geometry-satisfied candidate. |
| front_behind_depth_ambiguity_row | selected_prediction_row_boundary | open3dsg_recovery_relaxed_views_min2 | relative_horizontal | depth_front_behind | behind | RH1_source_x_frame_score | 1 |  | False | satisfied | A front/behind row can be geometry-satisfied by the frame score but still GT-negative, motivating the depth/reference-frame failure boundary. |

## Route-Level Patterns

| case_id | evidence_level | route | relations | source_scope | K | delta_recall | delta_violation | interpretation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| metric_predicate_geometry_comparison_K10_VL-SAT + Open3DSG validation | route_metric_summary | predicate_geometry_comparison | higher/lower + bigger/smaller | VL-SAT + Open3DSG validation | 10 | 0.041950 | -0.229859 | official validation only; source/family caveats remain separate |
| metric_predicate_geometry_comparison_K20_VL-SAT + Open3DSG validation | route_metric_summary | predicate_geometry_comparison | higher/lower + bigger/smaller | VL-SAT + Open3DSG validation | 20 | 0.081633 | -0.243091 | official validation only; source/family caveats remain separate |
| metric_predicate_geometry_comparison_K50_VL-SAT + Open3DSG validation | route_metric_summary | predicate_geometry_comparison | higher/lower + bigger/smaller | VL-SAT + Open3DSG validation | 50 | 0.103175 | -0.259199 | official validation only; source/family caveats remain separate |
| metric_caveated_lateral_compatibility_K10_open3dsg_recovery_relaxed_views_min2 | route_metric_summary | caveated_lateral_compatibility | left/right | open3dsg_recovery_relaxed_views_min2 | 10 | 0.145299 | -0.480614 | violation-risk reduction with bounded recall tradeoff; not a full relative-horizontal solved claim |
| metric_caveated_lateral_compatibility_K20_open3dsg_recovery_relaxed_views_min2 | route_metric_summary | caveated_lateral_compatibility | left/right | open3dsg_recovery_relaxed_views_min2 | 20 | 0.269231 | -0.466279 | violation-risk reduction with bounded recall tradeoff; not a full relative-horizontal solved claim |
| metric_caveated_lateral_compatibility_K50_open3dsg_recovery_relaxed_views_min2 | route_metric_summary | caveated_lateral_compatibility | left/right | open3dsg_recovery_relaxed_views_min2 | 50 | 0.378011 | -0.367407 | violation-risk reduction with bounded recall tradeoff; not a full relative-horizontal solved claim |
| metric_caveated_lateral_compatibility_K10_vlsat_full_validation | route_metric_summary | caveated_lateral_compatibility | left/right | vlsat_full_validation | 10 | -0.045242 | -0.096898 | violation-risk reduction with bounded recall tradeoff; not a full relative-horizontal solved claim |
| metric_caveated_lateral_compatibility_K20_vlsat_full_validation | route_metric_summary | caveated_lateral_compatibility | left/right | vlsat_full_validation | 20 | -0.043491 | -0.099909 | violation-risk reduction with bounded recall tradeoff; not a full relative-horizontal solved claim |
| metric_caveated_lateral_compatibility_K50_vlsat_full_validation | route_metric_summary | caveated_lateral_compatibility | left/right | vlsat_full_validation | 50 | -0.021308 | -0.124330 | violation-risk reduction with bounded recall tradeoff; not a full relative-horizontal solved claim |
| appendix_frame_depth_ambiguity_K20_open3dsg_recovery_relaxed_views_min2 | appendix_metric_summary | frame_depth_ambiguity | front/behind | open3dsg_recovery_relaxed_views_min2 | 20 | -0.060345 | -0.457409 | Violation decreases, but Recall loss is too large for main success. |
| appendix_frame_depth_ambiguity_K50_open3dsg_recovery_relaxed_views_min2 | appendix_metric_summary | frame_depth_ambiguity | front/behind | open3dsg_recovery_relaxed_views_min2 | 50 | -0.170424 | -0.359159 | Violation decreases, but Recall loss is too large for main success. |
| appendix_frame_depth_ambiguity_K20_vlsat_full_validation | appendix_metric_summary | frame_depth_ambiguity | front/behind | vlsat_full_validation | 20 | -0.203125 | -0.273084 | Violation decreases, but Recall loss is too large for main success. |
| appendix_frame_depth_ambiguity_K50_vlsat_full_validation | appendix_metric_summary | frame_depth_ambiguity | front/behind | vlsat_full_validation | 50 | -0.127441 | -0.237028 | Violation decreases, but Recall loss is too large for main success. |
| appendix_geometry_only_control_K20_open3dsg_recovery_relaxed_views_min2 | appendix_metric_summary | geometry_only_control | close by | open3dsg_recovery_relaxed_views_min2 | 20 | -0.001389 | -0.001330 | Proximity is geometry-decidable and supports relation-aware routing, not T_e x G_e interaction. |
| appendix_geometry_only_control_K50_open3dsg_recovery_relaxed_views_min2 | appendix_metric_summary | geometry_only_control | close by | open3dsg_recovery_relaxed_views_min2 | 50 | -0.002778 | -0.001265 | Proximity is geometry-decidable and supports relation-aware routing, not T_e x G_e interaction. |
| appendix_geometry_only_control_K20_vlsat_full_validation | appendix_metric_summary | geometry_only_control | close by | vlsat_full_validation | 20 | 0.000000 | -0.000547 | Proximity is geometry-decidable and supports relation-aware routing, not T_e x G_e interaction. |
| appendix_geometry_only_control_K50_vlsat_full_validation | appendix_metric_summary | geometry_only_control | close by | vlsat_full_validation | 50 | -0.002265 | -0.004551 | Proximity is geometry-decidable and supports relation-aware routing, not T_e x G_e interaction. |
| proximity_control_normalized_distance_xy | geometry_only_control_summary | geometry_only_control | close by |  |  |  |  | scale-normalized XY distance solves the route target |
| proximity_control_normalized_distance_3d | geometry_only_control_summary | geometry_only_control | close by |  |  |  |  | scale-normalized 3D distance solves the route target |
| proximity_control_distance_xy | geometry_only_control_summary | geometry_only_control | close by |  |  |  |  | raw XY distance nearly solves geometry support |

## Boundary

- This is not a new benchmark result.
- It does not promote support/contact, p_obs/p_rel, learned G_e, H003, or all-relation reliability.
- It should be used as appendix/qualitative support for the existing scoped validation claim.
