# H002 Relative Horizontal Frame Route Audit

## Status

```text
status = h002_relative_horizontal_frame_route_audit_ready
validation_errors = 0
selected_path = keep_relative_horizontal_as_frame_aware_caveated_diagnostic
promote_to_main_validated_route = false
next_todo = h002_relative_horizontal_main_route_user_decision_after_audit
```

## Six-Step Result

| gate | passed | decision | reason |
| --- | --- | --- | --- |
| 1_route_redefined | True | frame_aware_directional_compatibility | left/right/front/behind are treated as one frame-aware directional route |
| 2_frame_protocol_frozen | True | dataset_world_xy_reference_frame_from_3rscan_obb_centroids | uses existing materialization policy before metric review |
| 3_residuals_defined | True | signed_dx_for_left_right_signed_dy_for_front_behind | subject-minus-object world XY residuals are explicit |
| 4_source_wide_s2_no_regression | False | fail | violation_regressions=4, recall_large_losses=3 |
| 4_controls_degrade | False | fail | control_failures=20 |
| 5_per_predicate_slices_stable | False | fail | predicate_failures=10 |
| 6_axis_controls_stable | True | pass | axis_control_failures=0 |

## Existing S2 vs Source Baseline

| source_id | K | delta_Recall@K | delta_Violation@K | recall_not_large_loss | violation_nonincrease |
| --- | --- | --- | --- | --- | --- |
| open3dsg_recovery_relaxed_views_min2 | 10 | 0.015923566878980888 | 0.44065010956902845 | True | False |
| open3dsg_recovery_relaxed_views_min2 | 20 | 0.0296423321901029 | 0.34189831748354055 | True | False |
| open3dsg_recovery_relaxed_views_min2 | 50 | 0.1146496815286624 | 0.12862130441242015 | True | False |
| vlsat_full_validation | 10 | -0.025210084033613467 | -0.011496350364963548 | False | True |
| vlsat_full_validation | 20 | -0.03142126415783708 | -0.0011861313868613 | False | True |
| vlsat_full_validation | 50 | -0.018998903909389853 | 0.012481751824817533 | False | False |

## Deterministic Frame Residual Controls

| source_id | score_id | K | Recall@K | Violation@K |
| --- | --- | --- | --- | --- |
| open3dsg_recovery_relaxed_views_min2 | D0_source_score | 10 | 0.021313081822635964 | 0.485390796201607 |
| open3dsg_recovery_relaxed_views_min2 | D0_source_score | 20 | 0.06614404703576678 | 0.48637527432333577 |
| open3dsg_recovery_relaxed_views_min2 | D0_source_score | 50 | 0.1761391474767271 | 0.49405734660525924 |
| open3dsg_recovery_relaxed_views_min2 | D1_source_x_world_xy_frame | 10 | 0.03650171484566389 | 0.0014609203798392988 |
| open3dsg_recovery_relaxed_views_min2 | D1_source_x_world_xy_frame | 20 | 0.09823615874571288 | 0.010424286759326993 |
| open3dsg_recovery_relaxed_views_min2 | D1_source_x_world_xy_frame | 50 | 0.3270455658990691 | 0.049881146932105186 |
| open3dsg_recovery_relaxed_views_min2 | D2_source_x_axis_swap | 10 | 0.05512003919647232 | 0.8038714390065741 |
| open3dsg_recovery_relaxed_views_min2 | D2_source_x_axis_swap | 20 | 0.11489465948064674 | 0.7865764447695685 |
| open3dsg_recovery_relaxed_views_min2 | D2_source_x_axis_swap | 50 | 0.26825085742283195 | 0.7563512108156292 |
| open3dsg_recovery_relaxed_views_min2 | D3_source_x_sign_flip | 10 | 0.06614404703576678 | 0.9985390796201608 |
| open3dsg_recovery_relaxed_views_min2 | D3_source_x_sign_flip | 20 | 0.1256736893679569 | 0.9896671543525969 |
| open3dsg_recovery_relaxed_views_min2 | D3_source_x_sign_flip | 50 | 0.27045565899069085 | 0.9500817114841776 |
| vlsat_full_validation | D0_source_score | 10 | 0.474241870661308 | 0.36094890510948907 |
| vlsat_full_validation | D0_source_score | 20 | 0.6956521739130435 | 0.4238138686131387 |
| vlsat_full_validation | D0_source_score | 50 | 0.9229082937522836 | 0.4607664233576642 |
| vlsat_full_validation | D1_source_x_world_xy_frame | 10 | 0.41779320423821703 | 0.10693430656934307 |
| vlsat_full_validation | D1_source_x_world_xy_frame | 20 | 0.6001096090610157 | 0.1678832116788321 |
| vlsat_full_validation | D1_source_x_world_xy_frame | 50 | 0.8085495067592254 | 0.24156934306569344 |
| vlsat_full_validation | D2_source_x_axis_swap | 10 | 0.3587869930580928 | 0.5965328467153285 |
| vlsat_full_validation | D2_source_x_axis_swap | 20 | 0.5327000365363537 | 0.6094890510948905 |
| vlsat_full_validation | D2_source_x_axis_swap | 50 | 0.77274388016076 | 0.6111678832116788 |
| vlsat_full_validation | D3_source_x_sign_flip | 10 | 0.31896236755571794 | 0.8468978102189781 |
| vlsat_full_validation | D3_source_x_sign_flip | 20 | 0.4925100474972598 | 0.7827554744525548 |
| vlsat_full_validation | D3_source_x_sign_flip | 50 | 0.7584947022287176 | 0.7068978102189781 |

## Interpretation

`relative_horizontal`은 route definition과 frame protocol 자체는 만들 수 있다. 하지만 현재 locked `S2_current_source_x_Ce` 결과 기준으로는 main validated route 승격 gate를 통과하지 못한다.

핵심 blocker:

- Open3DSG에서 `S2`가 source baseline 대비 Violation@K를 크게 악화한다.
- VL-SAT에서는 low/mid-K에서 recall loss가 있고 K=50/100에서 violation regression이 나타난다.
- per-predicate slice와 axis/sign control도 안정적인 main-route evidence를 만들기에는 부족하다.

따라서 현재 판단은:

```text
relative_horizontal = frame-aware caveated diagnostic
not main validated route yet
```
