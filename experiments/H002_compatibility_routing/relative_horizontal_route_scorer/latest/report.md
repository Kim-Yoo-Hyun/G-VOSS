# H002 Relative Horizontal Route-Specific Scorer

## Status

```text
status = h002_relative_horizontal_route_scorer_ready
validation_errors = 0
selected_path = allow_relative_horizontal_as_caveated_frame_aware_violation_control_route
strict_balanced_main_route_pass = false
violation_control_route_pass = true
promote_to_main_validated_route = false
```

## Gate Result

| step | gate | passed | decision | reason |
| --- | --- | --- | --- | --- |
| 1 | route_specific_scorer_defined | True | RH1_source_x_frame_score | source score multiplied by frozen world-XY frame residual compatibility |
| 2 | frame_protocol_frozen | True | dataset_world_xy_reference_frame_from_3rscan_obb_centroids | same protocol as the prior audit, no label-dependent tuning |
| 3 | axis_and_sign_controls_degrade | True | pass | control_failures=0 |
| 4 | source_wide_violation_nonincrease | True | pass | source_violation_regressions=0 |
| 4 | source_wide_recall_not_large_loss | False | fail | source_recall_loss_cells_gt_0p01=3 |
| 5 | per_predicate_violation_nonincrease | True | pass | predicate_violation_regressions=0 |
| 5 | per_predicate_recall_not_large_loss | False | fail | predicate_recall_loss_cells_gt_0p05=6 |
| 6 | strict_balanced_main_route | False | do_not_promote_as_balanced_main | requires no violation regression, no large recall loss, and control collapse |
| 6 | caveated_violation_control_route | True | allow_caveated_route | allows route only as violation-control evidence when recall tradeoff remains |

## RH1 vs Source Baseline

| source_id | K | delta_Recall@K | delta_Violation@K | recall_not_large_loss_0p01 | violation_nonincrease |
| --- | --- | --- | --- | --- | --- |
| open3dsg_recovery_relaxed_views_min2 | 10 | 0.015188633023027927 | -0.4839298758217677 | True | True |
| open3dsg_recovery_relaxed_views_min2 | 20 | 0.03209211170994611 | -0.4759509875640088 | True | True |
| open3dsg_recovery_relaxed_views_min2 | 50 | 0.15090641842234198 | -0.444176199673154 | True | True |
| vlsat_full_validation | 10 | -0.05644866642309099 | -0.254014598540146 | False | True |
| vlsat_full_validation | 20 | -0.09554256485202772 | -0.2559306569343066 | False | True |
| vlsat_full_validation | 50 | -0.11435878699305813 | -0.21919708029197077 | False | True |

## Source-Family Metrics

| source_id | score_id | K | Recall@K | Violation@K |
| --- | --- | --- | --- | --- |
| open3dsg_recovery_relaxed_views_min2 | RH0_source_score | 10 | 0.021313081822635964 | 0.485390796201607 |
| open3dsg_recovery_relaxed_views_min2 | RH0_source_score | 20 | 0.06614404703576678 | 0.48637527432333577 |
| open3dsg_recovery_relaxed_views_min2 | RH0_source_score | 50 | 0.1761391474767271 | 0.49405734660525924 |
| open3dsg_recovery_relaxed_views_min2 | RH1_source_x_frame_score | 10 | 0.03650171484566389 | 0.0014609203798392988 |
| open3dsg_recovery_relaxed_views_min2 | RH1_source_x_frame_score | 20 | 0.09823615874571288 | 0.010424286759326993 |
| open3dsg_recovery_relaxed_views_min2 | RH1_source_x_frame_score | 50 | 0.3270455658990691 | 0.049881146932105186 |
| open3dsg_recovery_relaxed_views_min2 | RH3_source_x_axis_swap_control | 10 | 0.05512003919647232 | 0.8038714390065741 |
| open3dsg_recovery_relaxed_views_min2 | RH3_source_x_axis_swap_control | 20 | 0.11489465948064674 | 0.7865764447695685 |
| open3dsg_recovery_relaxed_views_min2 | RH3_source_x_axis_swap_control | 50 | 0.26825085742283195 | 0.7563512108156292 |
| open3dsg_recovery_relaxed_views_min2 | RH4_source_x_sign_flip_control | 10 | 0.06614404703576678 | 0.9985390796201608 |
| open3dsg_recovery_relaxed_views_min2 | RH4_source_x_sign_flip_control | 20 | 0.1256736893679569 | 0.9896671543525969 |
| open3dsg_recovery_relaxed_views_min2 | RH4_source_x_sign_flip_control | 50 | 0.27045565899069085 | 0.9500817114841776 |
| vlsat_full_validation | RH0_source_score | 10 | 0.474241870661308 | 0.36094890510948907 |
| vlsat_full_validation | RH0_source_score | 20 | 0.6956521739130435 | 0.4238138686131387 |
| vlsat_full_validation | RH0_source_score | 50 | 0.9229082937522836 | 0.4607664233576642 |
| vlsat_full_validation | RH1_source_x_frame_score | 10 | 0.41779320423821703 | 0.10693430656934307 |
| vlsat_full_validation | RH1_source_x_frame_score | 20 | 0.6001096090610157 | 0.1678832116788321 |
| vlsat_full_validation | RH1_source_x_frame_score | 50 | 0.8085495067592254 | 0.24156934306569344 |
| vlsat_full_validation | RH3_source_x_axis_swap_control | 10 | 0.3587869930580928 | 0.5965328467153285 |
| vlsat_full_validation | RH3_source_x_axis_swap_control | 20 | 0.5327000365363537 | 0.6094890510948905 |
| vlsat_full_validation | RH3_source_x_axis_swap_control | 50 | 0.77274388016076 | 0.6111678832116788 |
| vlsat_full_validation | RH4_source_x_sign_flip_control | 10 | 0.31896236755571794 | 0.8468978102189781 |
| vlsat_full_validation | RH4_source_x_sign_flip_control | 20 | 0.4925100474972598 | 0.7827554744525548 |
| vlsat_full_validation | RH4_source_x_sign_flip_control | 50 | 0.7584947022287176 | 0.7068978102189781 |

## Interpretation

`RH1_source_x_frame_score`는 `relative_horizontal`을 generic `S2_current_source_x_Ce`가 아니라 별도 frame-aware directional scorer로 재실험한 결과다.

판단:

- balanced main route 기준으로는 Recall loss가 남아 있어 즉시 승격하지 않는다.
- 다만 violation-control route 기준으로는 source-wide violation non-increase와 axis/sign control collapse를 만족하면 caveated route evidence로 사용할 수 있다.
- 따라서 paper main route 포함은 사용자가 선택할 수 있지만, 가장 방어적인 표현은 `main validated compatibility route`가 아니라 `frame-aware violation-control route`다.
