# H002 Relative Horizontal Split Route Scorer

## Status

```text
status = h002_relative_horizontal_split_route_scorer_ready
validation_errors = 0
selected_lateral_path = include_as_caveated_lateral_main_route
selected_depth_path = classify_as_depth_reference_frame_failure_case
```

## Win / Gate Summary

| subroute | total_win_cells | metric_cells | win_fraction | max_recall_loss_abs | mean_violation_reduction_abs | selected_path |
| --- | --- | --- | --- | --- | --- | --- |
| lateral_left_right | 15 | 20 | 0.75 | 0.045242265032107376 | 0.24985111697229184 | include_as_caveated_lateral_main_route |
| depth_front_behind | 11 | 20 | 0.55 | 0.203125 | 0.3156931200168022 | classify_as_depth_reference_frame_failure_case |

## Lateral Compact Table

| source_id | K | S0_Recall@K | RH1_Recall@K | delta_Recall@K | delta_Recall_ci95 | S0_Violation@K | RH1_Violation@K | delta_Violation@K | delta_Violation_ci95 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| open3dsg_recovery_relaxed_views_min2 | 10 | 0.09090909090909091 | 0.23620823620823622 | 0.1452991452991453 | [0.1196, 0.1708] | 0.4908558888076079 | 0.010241404535479151 | -0.4806144842721287 | [-0.4954, -0.4644] |
| open3dsg_recovery_relaxed_views_min2 | 20 | 0.1658896658896659 | 0.43512043512043513 | 0.2692307692307693 | [0.2351, 0.3027] | 0.49464153732446414 | 0.02836289726533629 | -0.46627864005912784 | [-0.4786, -0.4542] |
| open3dsg_recovery_relaxed_views_min2 | 50 | 0.3978243978243978 | 0.7758352758352758 | 0.37801087801087796 | [0.3354, 0.4192] | 0.5019544992572903 | 0.13454772887186303 | -0.36740677038542724 | [-0.3821, -0.3509] |
| open3dsg_recovery_relaxed_views_min2 | 100 | 0.8146853146853147 | 0.9121989121989122 | 0.09751359751359756 | [0.0634, 0.1291] | 0.49787714543812106 | 0.3955284552845528 | -0.10234869015356823 | [-0.1104, -0.0935] |
| vlsat_full_validation | 10 | 0.6897256275539988 | 0.6444833625218914 | -0.045242265032107376 | [-0.0593, -0.0324] | 0.23777372262773722 | 0.14087591240875913 | -0.09689781021897809 | [-0.1093, -0.0841] |
| vlsat_full_validation | 20 | 0.8884997081144191 | 0.8450087565674256 | -0.04349095154699356 | [-0.0572, -0.0304] | 0.2587591240875912 | 0.15885036496350366 | -0.09990875912408756 | [-0.1106, -0.0888] |
| vlsat_full_validation | 50 | 0.9851138353765324 | 0.963806187974314 | -0.021307647402218355 | [-0.0329, -0.0116] | 0.34124770642201835 | 0.21691743119266055 | -0.1243302752293578 | [-0.1338, -0.1161] |
| vlsat_full_validation | 100 | 0.9953298307063632 | 0.99241097489784 | -0.0029188558085231353 | [-0.0087, 0.0023] | 0.46465680697762607 | 0.30976488433826316 | -0.1548919226393629 | [-0.1605, -0.1492] |

## Interpretation

`left/right` is the only relative-horizontal sub-route that can be promoted now.
It is still caveated: the claim is violation-risk reduction with bounded recall
tradeoff, not uniform Recall improvement. `front/behind` remains a
reference-frame/depth ambiguity failure case.
