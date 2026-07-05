# H002 Report 0706: C_e Improvement Path

## 목적

`p_obs/p_rel`을 보류하고, H002의 핵심인 `C_e = compatibility(T_e, G_e)`를 강화할 수 있는지 실험 단계에서 점검했다.

검증 순서:

1. hard-negative + structured compatibility
2. route-aware C_e
3. richer G_e hard-route feasibility
4. calibrated C_e

## 결과 요약

```text
status = h002_ce_improvement_path_ready
validation_errors = 0
selected_path = calibrated_route_aware_candidate_requires_ci_and_family_review_before_promotion
best_primary_score = I4_calibrated_route_aware_source_x_Ce
calibrated_ce_main_promotion = false
richer_ge_support_contact_promotion = false
```

Primary comparison route, K=10/20/50:

| Score | K | Recall@K | Violation@K |
| --- | ---: | ---: | ---: |
| `S0_source_score` | 10 | 0.471655 | 0.302201 |
| `S0_source_score` | 20 | 0.642857 | 0.343578 |
| `S0_source_score` | 50 | 0.849206 | 0.425197 |
| `S2_current_source_x_Ce` | 10 | 0.513605 | 0.072342 |
| `S2_current_source_x_Ce` | 20 | 0.724490 | 0.100487 |
| `S2_current_source_x_Ce` | 50 | 0.952381 | 0.165998 |
| `I1_hardneg_structured_source_x_Ce` | 10 | 0.518141 | 0.072753 |
| `I1_hardneg_structured_source_x_Ce` | 20 | 0.734694 | 0.101221 |
| `I1_hardneg_structured_source_x_Ce` | 50 | 0.953515 | 0.166272 |
| `I2_route_aware_source_x_Ce` | 10 | 0.515873 | 0.073895 |
| `I2_route_aware_source_x_Ce` | 20 | 0.732426 | 0.103080 |
| `I2_route_aware_source_x_Ce` | 50 | 0.950113 | 0.168695 |
| `I4_calibrated_route_aware_source_x_Ce` | 10 | 0.529478 | 0.063573 |
| `I4_calibrated_route_aware_source_x_Ce` | 20 | 0.746032 | 0.089974 |
| `I4_calibrated_route_aware_source_x_Ce` | 50 | 0.960317 | 0.151963 |

## Stage Decision

| Stage | Decision | Reason |
| --- | --- | --- |
| 1_hard_negative_structured_Ce | diagnostic_ablation_ready | added 2446 inverse-predicate hard negatives and structured signed-margin features |
| 2_route_aware_Ce | candidate_method_but_not_auto_promoted | route-specific models match H002 route-aware design, but source-reranking promotion depends on Recall/Violation tradeoff |
| 3_richer_Ge_support_contact | blocked_for_main_route | support/contact capacity gate remains insufficient: binary_rows=40, mixed_class_pairs=4 |
| 4_calibrated_Ce | calibration_diagnostic_only | temperature=0.35 selected on internal_dev; does not by itself solve hard-route generalization |

## Calibration Heldout Metrics

| Score | AUROC | Brier | NLL |
| --- | ---: | ---: | ---: |
| `current_Ce` | 0.987765 | 0.058334 | 0.214770 |
| `hardneg_structured_Ce` | 0.988668 | 0.055853 | 0.203226 |
| `route_aware_Ce` | 0.987902 | 0.056215 | 0.203538 |
| `calibrated_route_aware_Ce` | 0.987902 | 0.045925 | 0.139495 |

## 해석

- hard-negative와 structured feature는 `C_e`가 단순 source score 복사가 아니라 predicate-geometry matching 문제라는 점을 더 명확히 만든다.
- route-aware C_e는 relation family마다 다른 evidence route가 필요하다는 H002 framework와 맞는다.
- support/contact richer G_e는 현재 capacity gate에서 막혀 있어 main route로 승격하지 않는다.
- calibrated C_e는 primary comparison route에서는 개선 후보로 보이지만, main score 대체 전에는 bootstrap CI와 family-wise review가 필요하다.

따라서 현재 H002의 가장 안전한 다음 방향은 calibrated route-aware `C_e`를 candidate improved score로 보관하고, CI/family-wise review 후 main score 승격 여부를 판단하는 것이다.
