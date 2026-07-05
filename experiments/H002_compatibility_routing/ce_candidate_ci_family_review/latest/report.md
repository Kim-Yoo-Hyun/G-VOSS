# H002 C_e Candidate CI / Family Review

## 목적

`I4_calibrated_route_aware_source_x_Ce`를 current `S2_current_source_x_Ce` 대신 main score로 올릴 수 있는지 확인했다.

## 결론

```text
status = h002_ce_candidate_ci_family_review_ready
validation_errors = 0
candidate_score = I4_calibrated_route_aware_source_x_Ce
baseline_score = S2_current_source_x_Ce
promote_to_main_score = false
selected_path = keep_current_main_score_report_I4_as_candidate_or_ablation
```

## Primary Delta

| K | Delta Recall@K | Recall CI | Delta Violation@K | Violation CI |
| ---: | ---: | --- | ---: | --- |
| 5 | 0.005669 | [-0.006347, 0.017863] | -0.006937 | [-0.009130, -0.004834] |
| 10 | 0.015873 | [0.000971, 0.031462] | -0.008769 | [-0.010635, -0.006850] |
| 20 | 0.021542 | [0.002312, 0.042037] | -0.010512 | [-0.012193, -0.008920] |
| 50 | 0.007937 | [-0.004322, 0.021306] | -0.014035 | [-0.015485, -0.012709] |
| 100 | 0.000000 | [0.000000, 0.000000] | -0.000912 | [-0.001233, -0.000633] |

## K=5 Point Result

| Score | Recall@5 | Violation@5 |
| --- | ---: | ---: |
| `S2_current_source_x_Ce` | 0.352608 | 0.054491 |
| `I4_calibrated_route_aware_source_x_Ce` | 0.358277 | 0.047554 |

## Family Blockers

| Source | Family | K | Delta Recall | Delta Violation | Reason |
| --- | --- | ---: | ---: | ---: | --- |
| `open3dsg_recovery_relaxed_views_min2` | `relative_vertical` | 5 | -0.004464 | 0.005478 | recall and violation both worsen |
| `open3dsg_recovery_relaxed_views_min2` | `relative_vertical` | 10 | 0.013393 | 0.007681 | violation worsens |
| `open3dsg_recovery_relaxed_views_min2` | `relative_vertical` | 20 | 0.053571 | 0.013119 | violation worsens |
| `open3dsg_recovery_relaxed_views_min2` | `relative_vertical` | 50 | 0.004464 | 0.006763 | violation worsens |
| `open3dsg_recovery_relaxed_views_min2` | `size_relative` | 5 | 0.020408 | 0.000365 | violation worsens |

## Promotion Gates

| Gate | Passed | Reason |
| --- | --- | --- |
| `primary_point_K5` | True | delta_recall=0.005669, delta_violation=-0.006937 |
| `primary_ci_K5` | False | recall_CI=[-0.006347,0.017863], violation_CI=[-0.009130,-0.004834] |
| `primary_point_K10` | True | delta_recall=0.015873, delta_violation=-0.008769 |
| `primary_ci_K10` | True | recall_CI=[0.000971,0.031462], violation_CI=[-0.010635,-0.006850] |
| `primary_point_K20` | True | delta_recall=0.021542, delta_violation=-0.010512 |
| `primary_ci_K20` | True | recall_CI=[0.002312,0.042037], violation_CI=[-0.012193,-0.008920] |
| `primary_point_K50` | True | delta_recall=0.007937, delta_violation=-0.014035 |
| `primary_ci_K50` | False | recall_CI=[-0.004322,0.021306], violation_CI=[-0.015485,-0.012709] |
| `family_no_violation_regression_K5_50` | False | violation_regression_cells=5 |
| `family_no_double_regression_K5_50` | False | double_regression_cells=1 |
| `main_score_promotion` | False | candidate has positive aggregate signal, but family-wise violation regressions block replacing the current main score |

## 해석

- 올릴 수 있는 근거: aggregate primary route에서 K=5/10/20/50 모두 Recall이 증가하고 Violation이 감소한다.
- 올리기 어려운 근거: family-wise로 보면 Open3DSG relative_vertical 등에서 Violation이 악화되는 cell이 남아 있다.
- 따라서 `I4`는 improved candidate / ablation으로는 강하지만, current main score를 대체하려면 family-wise mitigation 또는 per-route gating이 먼저 필요하다.
