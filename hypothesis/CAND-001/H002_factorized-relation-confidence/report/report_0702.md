# H002 Report 0702: Official Metric Result Review and Paper-Level Experiment Gate

## 1. 현재 위치

H002는 현재 `Semantic-Geometry Compatibility Learning for Reliable 3D Scene Graph Relations`
방향으로 진행 중이다. 핵심은 relation source score를 그대로 신뢰하지 않고,
relation reliability를 구성하는 요소를 다음처럼 분리하는 것이다.

```text
T_e = semantic content
Z_e = source confidence
G_e = predicate-independent geometry evidence
C_e = compatibility(T_e, G_e)
Q_e = evidence quality / observability
p_obs = P(evidence is sufficient to decide)
p_rel = P(relation is reliable | evidence is observable)
```

이번 단계에서는 `p_rel` 또는 `p_obs`까지 가지 않고, 먼저 `C_e =
compatibility(T_e, G_e)`가 official validation candidate pool에서도 의미 있는지를 검증했다.

## 2. 방금 진행한 내용

직전 단계에서 frozen protocol을 따르는 Docker official metric runner를 실행했다.

```bash
HOST_UID=$(id -u) HOST_GID=$(id -g) docker compose -f configs/h002/compose.yaml run --rm h002-official-metric-runner
```

생성 위치:

```text
experiments/H002_compatibility_routing/official_evaluation/latest/
artifacts/compatibility_dataset_v3_official_metric_runner_after_protocol_freeze/
```

검증된 조건:

- official validation rows는 eval-only로 사용했다.
- official test는 사용하지 않았다.
- trainable view는 internal train split에서 fit했다.
- main `C_e`에는 `T_e`와 `G_e`만 사용했다.
- `Z_e`, `Q_e`, H001 `p_geom_valid`, hidden construction fields는 main `C_e`에서 제외했다.
- validation errors는 `0`이다.

## 3. Official Metric 결과

Primary metric은 frozen protocol에서 정한 `macro_family_AUROC`다.
Overall AUROC는 `relative_horizontal` row 수가 전체를 지배할 수 있으므로 secondary로만 본다.

| View | Macro-family AUROC | Weighted-family AUROC | Overall AUROC |
| --- | ---: | ---: | ---: |
| `M1_T_semantic_only` | 0.417633 | 0.455374 | 0.404333 |
| `M2_G_geometry_only` | 0.500000 | 0.500000 | 0.528329 |
| `M3_T_plus_G_concat` | 0.416923 | 0.454625 | 0.406137 |
| `M4_TxG_compatibility` | 0.835547 | 0.720781 | 0.724835 |

Family-level M4:

| Family | Rows | M4 AUROC | Balanced accuracy | 판단 |
| --- | ---: | ---: | ---: | --- |
| `relative_vertical` | 780 | 0.991321 | 0.957692 | main evidence 후보 |
| `size_relative` | 340 | 0.999585 | 0.988235 | main evidence 후보 |
| `relative_horizontal` | 18764 | 0.719568 | 0.701522 | caveat付き 후보 |
| `support_contact` | 3178 | 0.631712 | 0.566394 | diagnostic/challenging |

## 4. Control 결과

Macro-family 기준 control 결과는 다음과 같다.

| Comparison | Delta AUROC | 해석 |
| --- | ---: | --- |
| `M4_vs_M1` | 0.417913 | semantic-only보다 강함 |
| `M4_vs_M2` | 0.335547 | geometry-only보다 강함 |
| `M4_vs_M3` | 0.418624 | 단순 concat보다 강함 |
| `M4_vs_wrong_T_within_route` | 0.671120 | predicate가 틀리면 크게 무너짐 |
| `M4_vs_wrong_T_across_route` | 0.270464 | route 밖 wrong predicate에서도 저하 |
| `M4_vs_shuffled_G_global` | 0.341733 | geometry를 섞으면 저하 |
| `M4_vs_shuffled_G_within_family` | 0.318753 | family 내부 geometry shuffle도 저하 |
| `M4_vs_subject_object_swap` | 0.717045 | directed pair control 저하 |
| `M4_vs_sign_flip` | 0.717045 | signed geometry control 저하 |
| `M4_vs_horizontal_frame_swap` | 0.038149 | macro 기준 margin 약함 |

중요한 해석:

- `M4_TxG_compatibility`가 semantic-only, geometry-only, 단순 concat을 모두 이긴다.
- wrong-`T`와 shuffled-`G` control이 무너진다.
- 이는 모델이 단순히 predicate/class prior나 geometry alone만 보는 것이 아니라,
  `T_e`와 `G_e`의 matching을 보고 있다는 근거다.
- 다만 `horizontal_frame_swap`은 macro delta가 약하다. 이는 non-horizontal family에는
  frame-swap이 사실상 적용되지 않기 때문이므로, `relative_horizontal`은 family-specific
  frame-control caveat와 함께 다뤄야 한다.

## 5. Paper-Level Experiment Gate에서 확인한 내용

이번 gate의 목적은 “지금 결과를 paper-level experiment로 실행해도 되는 상태였는가?”와
“실행된 결과를 paper-facing evidence로 올릴 수 있는가?”를 분리해 판단하는 것이다.

| Gate | 결과 | 판단 |
| --- | --- | --- |
| Docker 재현 가능성 | pass | `h002-official-metric-runner`가 exit 0으로 실행됨 |
| Official validation policy | pass | validation은 eval-only, official test 미사용 |
| Feature boundary | pass | main `C_e`는 `T_e + G_e`만 사용 |
| Hidden/source leakage | pass | `Z_e`, `Q_e`, H001 `p_geom_valid`, hidden fields 제외 |
| Primary metric | pass | M4 macro-family AUROC가 모든 baseline보다 높음 |
| Counterfactual controls | pass | wrong-`T`, shuffled-`G`, swap, sign flip에서 성능 저하 |
| Family-wise reporting | pass | family별 metric이 분리되어 있음 |
| `relative_horizontal` | caveat | frame-control wording 필요 |
| `support_contact` | caveat | solved claim 금지, diagnostic only |
| Paper promotion | conditional pass | claim-boundary lock 이후 승격 여부 결정 |

결론:

```text
paper_level_experiment_execution_gate = passed_with_caveats
paper_result_promotion = not_yet
next_action = claim_boundary_lock
```

즉, paper-level experiment를 실행해도 되는 상태였고 실제로 실행도 완료했다.
하지만 결과를 최종 paper table로 올리려면 claim boundary를 먼저 잠가야 한다.

## 6. Family별 Claim Boundary

현재 결과 기준으로 가장 안전한 family별 위치는 다음이다.

| Family | Claim boundary |
| --- | --- |
| `relative_vertical` | main evidence 가능. Axis-order relation에서 predicate-conditioned geometry compatibility가 강하게 작동한다. |
| `size_relative` | main evidence 가능. Size-comparison relation에서 `T_e x G_e` compatibility가 명확하다. |
| `relative_horizontal` | supporting/main 후보 가능. 단, frame-control caveat를 명시해야 한다. |
| `support_contact` | diagnostic/challenging only. Contact/pose evidence가 아직 부족하며 solved claim 금지. |

## 7. 아직 막아야 하는 Claim

아래 claim은 현재 결과만으로는 쓰면 안 된다.

- 모든 3DSSG relation type에서 일반화된다.
- `support_contact`가 해결됐다.
- `relative_horizontal`이 frame-invariant하게 완전히 해결됐다.
- `p_rel` / `p_obs` reliability까지 검증됐다.
- VL-SAT/Open3DSG source reranking의 recall/violation tradeoff까지 개선했다.
- official test 결과다.

## 8. 다음 단계

다음 TODO는 다음이다.

```text
compatibility_dataset_v3_official_metric_claim_boundary_lock_after_result_review
```

여기서 해야 할 일:

- paper-facing main table에 어떤 family를 넣을지 확정한다.
- `relative_vertical`, `size_relative`를 main evidence로 둘지 확정한다.
- `relative_horizontal`을 main/supporting 중 어디에 둘지 frame-control caveat와 함께 결정한다.
- `support_contact`를 diagnostic/failure taxonomy로 고정한다.
- paper wording에서 금지 claim과 허용 claim을 분리한다.
- paper-level result promotion 여부를 결정한다.
