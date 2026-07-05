# H002 Report 0706: C_e Improvement Path

## 목적

`p_obs/p_rel` 관련 작업은 보류하고, H002의 핵심인
`C_e = compatibility(T_e, G_e)`를 강화할 수 있는지 Docker experiment-stage에서
점검했다.

검증 순서:

```text
1. hard-negative + structured compatibility
2. route-aware C_e
3. richer G_e hard-route feasibility
4. calibrated C_e
```

Runtime artifact:

```text
experiments/H002_compatibility_routing/ce_improvement_path/latest/
```

Docker service:

```text
h002-ce-improvement-path
```

## 결과 요약

```text
status = h002_ce_improvement_path_ready
validation_errors = 0
source_rows_scored = 762888
internal_train = 4868
internal_dev = 1044
internal_heldout = 1040
best_primary_score = I4_calibrated_route_aware_source_x_Ce
calibrated_ce_candidate_pass = true
calibrated_ce_main_promotion = false
richer_ge_support_contact_promotion = false
pobs_prel_reopened = false
```

현재 결론:

```text
calibrated route-aware C_e is a promising candidate,
but it is not promoted to the main score before CI and family-wise review.
```

## Primary Route Result

Primary comparison route는 기존과 동일하게 `relative_vertical` +
`size_relative`다.

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

`I4`는 기존 `S2_current_source_x_Ce` 대비 primary route에서:

| K | Delta Recall@K | Delta Violation@K |
| ---: | ---: | ---: |
| 10 | +0.015873 | -0.008769 |
| 20 | +0.021542 | -0.010512 |
| 50 | +0.007937 | -0.014035 |

즉, calibrated route-aware `C_e`는 primary route point estimate 기준으로는 기존
`S2`보다 좋다.

## Step별 판단

| Stage | Decision | Reason |
| --- | --- | --- |
| hard-negative + structured C_e | diagnostic ablation ready | inverse-predicate hard negatives `2446`개를 추가했고 structured signed-margin feature를 사용 |
| route-aware C_e | candidate method, not auto-promoted | relation family별 model 구조는 H002의 route-aware claim과 맞지만 단독으로는 기존 S2보다 안정적으로 좋지 않음 |
| richer G_e hard route | blocked for main route | support/contact는 strict shortcut-controlled repair 후 binary row `40`, mixed class-pair `4`만 남아 metric rerun 불가 |
| calibrated C_e | promising candidate | internal dev에서 temperature `0.35`를 선택했고 primary route point estimate가 개선됨 |

## Calibration Check

Internal heldout 기준:

| Score | AUROC | Brier | NLL |
| --- | ---: | ---: | ---: |
| `current_Ce` | 0.987765 | 0.058334 | 0.214770 |
| `hardneg_structured_Ce` | 0.988668 | 0.055853 | 0.203226 |
| `route_aware_Ce` | 0.987902 | 0.056215 | 0.203538 |
| `calibrated_route_aware_Ce` | 0.987902 | 0.045925 | 0.139495 |

해석:

- hard-negative + structured C_e는 AUROC/Brier/NLL이 모두 조금 좋아진다.
- route-aware C_e만으로는 AUROC 개선이 크지 않다.
- temperature calibration은 AUROC를 바꾸지는 않지만 Brier/NLL을 크게 낮춘다.
- 따라서 calibrated route-aware C_e는 “ranking + reliability score” 관점에서 유망하다.

## Family-wise Caveat

`I4_calibrated_route_aware_source_x_Ce`는 aggregate primary route에서는 좋지만,
family/source slice를 보면 caveat가 있다.

Open3DSG `relative_vertical`:

| K | Current Recall | I4 Recall | Current Violation | I4 Violation |
| ---: | ---: | ---: | ---: | ---: |
| 10 | 0.156250 | 0.169643 | 0.013716 | 0.021397 |
| 20 | 0.410714 | 0.464286 | 0.039634 | 0.052753 |
| 50 | 0.870536 | 0.875000 | 0.160152 | 0.166914 |

VL-SAT `relative_vertical`:

| K | Current Recall | I4 Recall | Current Violation | I4 Violation |
| ---: | ---: | ---: | ---: | ---: |
| 10 | 0.700000 | 0.694872 | 0.130474 | 0.113321 |
| 20 | 0.882051 | 0.884615 | 0.159580 | 0.137500 |
| 50 | 0.992308 | 0.992308 | 0.197615 | 0.166275 |

이 말은 `I4`가 전체적으로는 좋지만, 모든 source/family cell에서 uniformly 좋은 것은
아니라는 뜻이다. 그래서 main score 승격 전에는 bootstrap CI와 family-wise decision
gate가 필요하다.

## p_obs / p_rel과의 관계

이번 단계에서는 `p_obs/p_rel`을 재개하지 않았다.

이유:

- 현재 핵심 문제는 `C_e`가 source score와 독립적으로 predicate-geometry
  compatibility를 잘 설명하는가다.
- `p_obs`는 observability/selective decision 문제이며, 현재 main comparison-route
  reranking에는 필수 구성요소가 아니다.
- `p_rel`만 단독으로 넣으면 missing/ambiguous evidence와 false relation을 분리하지
  못한다.

따라서 현재 방향은:

```text
p_obs/p_rel 보류
C_e 개선 집중
calibrated route-aware C_e를 candidate로 보관
CI/family-wise review 후 main score 승격 여부 결정
```

## 최종 판단

현재 시점의 가장 좋은 해석은 다음이다.

```text
H002의 핵심 구조는 여전히 맞다.
T_e/G_e/Z_e 분리와 C_e 기반 source reranking은 유지한다.
다만 C_e는 current global model보다 calibrated route-aware variant가 더 유망하다.
```

하지만 아직 다음 문장은 금지한다.

```text
calibrated route-aware C_e is the final main score.
```

허용되는 표현은 다음이다.

```text
calibrated route-aware C_e is a promising candidate that improves primary-route
point estimates, pending bootstrap CI and family-wise promotion review.
```

다음 실험 TODO:

```text
h002_ce_candidate_ci_family_review_before_promotion
```

## CI / Family Review Update

위 TODO를 Docker experiment-stage에서 실행했다.

Runtime artifact:

```text
experiments/H002_compatibility_routing/ce_candidate_ci_family_review/latest/
```

Docker service:

```text
h002-ce-candidate-ci-family-review
```

결과:

```text
status = h002_ce_candidate_ci_family_review_ready
validation_errors = 0
n_bootstrap = 1000
candidate_score = I4_calibrated_route_aware_source_x_Ce
baseline_score = S2_current_source_x_Ce
promote_to_main_score = false
selected_path = keep_current_main_score_report_I4_as_candidate_or_ablation
```

### K=5 결과

| Score | Recall@5 | Violation@5 |
| --- | ---: | ---: |
| `S2_current_source_x_Ce` | 0.352608 | 0.054491 |
| `I4_calibrated_route_aware_source_x_Ce` | 0.358277 | 0.047554 |

Delta:

```text
Recall@5    = +0.005669
Violation@5 = -0.006937
Recall@5 CI = [-0.006347, 0.017863]
Violation@5 CI = [-0.009130, -0.004834]
```

해석:

- K=5 point estimate에서는 I4가 S2보다 좋다.
- Violation@5 개선은 bootstrap CI에서도 안정적으로 음수다.
- 하지만 Recall@5 CI는 0을 포함하므로 Recall 개선은 아직 통계적으로 강하게
  고정됐다고 보기 어렵다.

### Primary Aggregate CI

| K | Delta Recall@K | Recall CI | Delta Violation@K | Violation CI |
| ---: | ---: | --- | ---: | --- |
| 5 | +0.005669 | [-0.006347, 0.017863] | -0.006937 | [-0.009130, -0.004834] |
| 10 | +0.015873 | [0.000971, 0.031462] | -0.008769 | [-0.010635, -0.006850] |
| 20 | +0.021542 | [0.002312, 0.042037] | -0.010512 | [-0.012193, -0.008920] |
| 50 | +0.007937 | [-0.004322, 0.021306] | -0.014035 | [-0.015485, -0.012709] |

올릴 수 있는 근거:

- aggregate primary route에서 K=5/10/20/50 모두 Recall point estimate가 증가한다.
- aggregate primary route에서 K=5/10/20/50 모두 Violation point estimate가 감소한다.
- K=10과 K=20은 Recall 개선 CI도 0 위에 있고, Violation 개선 CI도 안정적으로
  음수다.
- calibration 자체도 heldout Brier/NLL을 개선했기 때문에 reliability score 후보로는
  유망하다.

올리기 어려운 근거:

- K=5와 K=50의 Recall CI가 0을 포함한다.
- family-wise review에서 violation regression cell이 `5`개 남아 있다.
- double regression cell도 `1`개 존재한다.
- 문제 cell은 Open3DSG `relative_vertical`에 집중된다.

Family blocker:

| Source | Family | K | Delta Recall | Delta Violation | Reason |
| --- | --- | ---: | ---: | ---: | --- |
| `open3dsg_recovery_relaxed_views_min2` | `relative_vertical` | 5 | -0.004464 | +0.005478 | Recall과 Violation 모두 악화 |
| `open3dsg_recovery_relaxed_views_min2` | `relative_vertical` | 10 | +0.013393 | +0.007681 | Violation 악화 |
| `open3dsg_recovery_relaxed_views_min2` | `relative_vertical` | 20 | +0.053571 | +0.013119 | Violation 악화 |
| `open3dsg_recovery_relaxed_views_min2` | `relative_vertical` | 50 | +0.004464 | +0.006763 | Violation 악화 |
| `open3dsg_recovery_relaxed_views_min2` | `size_relative` | 5 | +0.020408 | +0.000365 | Violation 소폭 악화 |

### 최종 판단

I4를 paper의 final main score로 바로 올리기는 어렵다.

가장 방어 가능한 위치는 다음이다.

```text
I4_calibrated_route_aware_source_x_Ce
= improved C_e candidate / secondary ablation / future route-gated variant
```

현재 main score는 유지한다.

```text
main_score = S2_current_source_x_Ce
```

이유는 단순하다. I4는 aggregate에서는 더 좋지만, H002가 주장하는
relation-aware reliability framework 기준에서는 source/family cell에서 일관성이
중요하다. Open3DSG `relative_vertical`에서 Violation 악화가 남아 있으므로, 최종
main score로 올리려면 per-source/per-family mitigation이나 route-gated selection이
먼저 필요하다.

Next TODO:

```text
h002_ce_family_mitigation_or_keep_s2_boundary_update
```
