# H002 Report 0704: Claim / Novelty / Principle Review

## 목적

현재 H002에서 주장하려는 claim, 산출물, 점수 산출 방식, 검증 과정, 결과 해석을
전체적으로 재검토했다. 결론은 다음이다.

```text
H002는 paper claim 가능성이 있다.
단, validation-level comparison-route source reranking claim으로 좁혀야 한다.
```

즉 지금 강하게 주장할 수 있는 것은 다음이다.

```text
VL-SAT / Open3DSG validation predictions 위에서
source score만 쓰는 것보다,
T_e와 G_e로 만든 compatibility C_e를 source score와 결합한 S2가
geometry-checkable comparison relation에서 Recall@K와 Violation@K tradeoff를 개선한다.
```

반대로 아직 주장하면 안 되는 것은 다음이다.

- 모든 3DSSG relation family를 해결했다.
- support/contact까지 해결했다.
- official test / SOTA / leaderboard 결과다.
- Open3DSG open-set GT evaluation이다.
- p_obs/p_rel calibrated reliability가 해결됐다.

## 현재 핵심 결과

K=20 primary comparison route 기준:

| Score | Recall@20 | Violation@20 |
| --- | ---: | ---: |
| `S0_source_score` | 0.642857 | 0.343578 |
| `A1_source_x_G_only` | 0.646259 | 0.327534 |
| `A2_source_x_TG_concat` | 0.629252 | 0.330770 |
| `S2_source_x_Ce` | 0.724490 | 0.100487 |

K=20 delta CI:

| 비교 | Metric | Delta | 95% CI |
| --- | --- | ---: | --- |
| `S2 - S0` | Recall@20 | +0.081633 | [0.048096, 0.118007] |
| `S2 - S0` | Violation@20 | -0.243091 | [-0.251882, -0.235094] |
| `S2 - A1` | Recall@20 | +0.078231 | [0.047499, 0.110305] |
| `S2 - A1` | Violation@20 | -0.227047 | [-0.234776, -0.219345] |
| `S2 - A2` | Recall@20 | +0.095238 | [0.064715, 0.131210] |
| `S2 - A2` | Violation@20 | -0.230284 | [-0.238861, -0.222207] |

해석:

- `S2`는 source-only, route-aware geometry-only, plain `T_e/G_e` concat보다 강하다.
- 특히 Violation@K 감소가 매우 안정적이다.
- Recall@K도 aggregate primary route에서는 개선되지만, family-wise Recall은 mixed이므로 uniform improvement claim은 금지한다.

## 점수 산출 방식 검토

현재 구조:

```text
T_e = predicate / relation-family semantic content
G_e = geometry evidence
Z_e = source score / rank
C_e = compatibility(T_e, G_e)
S2 = normalized_source_score(Z_e) * normalized_C_e
```

원리적으로 맞는 부분:

- `C_e` 안에 `Z_e`를 넣지 않는다.
- `Z_e`는 최종 reranking에서만 결합한다.
- hidden GT, violation label, H001 `p_geom_valid`는 model-safe input에 들어가지 않는다.
- `A1`과 `A2`를 추가해 “그냥 geometry filter 아니냐”, “그냥 concat 아니냐”를 직접 검증했다.

주의할 부분:

- `G_e`에는 predicate label이나 source score는 없지만, 현재 구현의 `common_g_features`에는 `route_family` one-hot이 들어간다.
- 따라서 `A1_source_x_G_only`는 “pure predicate-agnostic geometry-only”가 아니라 “route-aware geometry-only ablation”으로 불러야 한다.
- score normalization은 per-source / per-source-family minmax이며, validation candidate score distribution을 사용한다. label-free이긴 하지만 transductive하게 보일 수 있으므로 train-bound 또는 rank-percentile sensitivity가 필요하다.

## Novelty Threat

가장 큰 novelty threat은 RelWitness다.

RelWitness는 visual-geometric relation witness, observability, missing-relation audit를 직접 다룬다. 따라서 H002가 “relation별 geometry evidence를 만든다”만 주장하면 novelty가 약하다.

H002가 방어해야 할 차이는 다음이다.

| Threat | H002 방어 포인트 |
| --- | --- |
| RelWitness | H002는 open-vocabulary generation/pseudo-labeling이 아니라 existing relation source output의 compatibility reranking과 factor leakage control |
| VL-SAT | H002는 VL-SAT를 대체하는 predictor가 아니라 VL-SAT output 위의 reliability layer |
| Open3DSG | Open3DSG는 source이며, 정량 평가는 closed-vocabulary 3DSSG mapping |
| selective prediction / calibration | p_obs/p_rel은 framework interface이지 novelty 자체가 아님 |
| gated fusion / MoE / FiLM | route-aware factor routing 자체는 일반 개념이므로 relation-family evidence route와 controls가 핵심 |
| simple geometry reranking | A1/A2/wrong-T/shuffled-G control로 방어 |

## 원리적 문제

1. Claim scope가 좁다.
   현재 main success는 `relative_vertical`, `size_relative`에 집중되어 있다.

2. `G_e` 독립성 표현이 과장될 수 있다.
   source score와 predicate label은 빠졌지만 route-family identity는 들어간다.

3. normalization sensitivity가 필요하다.
   validation label은 쓰지 않지만 validation candidate bounds를 사용한다.

4. `p_obs/p_rel`은 아직 solved claim이 아니다.
   selective stress-test는 통과했지만 calibrated quantitative claim은 blocked다.

5. `Violation@K`는 custom metric이다.
   반드시 Recall@K와 함께 보고해야 한다.

6. support/contact는 failure taxonomy다.
   hard route의 실패를 숨기면 안 되고, 왜 richer point/mesh/contact/pose evidence가 필요한지 보여주는 사례로 써야 한다.

## 추가 보완점

다음 작업이 paper-level wording 전에 필요하다.

1. Normalization sensitivity
   - train/dev bound minmax
   - rank-percentile normalization
   - raw product 또는 log-utility score

2. No-route G-only sensitivity 또는 명시적 caveat
   - `route_family` one-hot을 제거한 G-only ablation을 추가하거나,
   - 현재 `A1`을 route-aware geometry-only ablation으로 명시한다.

3. Qualitative examples
   - `S2`가 violation을 낮추면서 GT를 유지한 case
   - `S2`가 recall을 잃은 failure case
   - `A1/A2` 대비 왜 `C_e`가 필요한지 보이는 case

4. Related-work novelty map
   - RelWitness / VL-SAT / Open3DSG / selective prediction / calibration / fusion과 직접 비교한다.

5. p_obs/p_rel boundary
   - main framework에는 포함 가능.
   - calibrated solved result로는 아직 금지.
   - real observability labels가 생기면 다시 promotion 가능.

## 결론

현재 H002는 억지로 끼워맞춘 방향은 아니다. 오히려 지금까지의 실패와 보완 과정이
다음 결론으로 수렴했다.

```text
source confidence만으로는 relation reliability를 설명하기 어렵고,
geometry evidence만으로도 충분하지 않으며,
predicate-geometry compatibility를 source score와 분리해서 계산한 뒤
다시 결합해야 한다.
```

하지만 top-tier standalone claim으로 가려면 claim을 좁게 써야 한다.

가장 안전한 현재 claim:

```text
Factor-isolated predicate-geometry compatibility improves validation-level
source reranking for geometry-checkable comparison relations, reducing
geometry violations while preserving or improving recall.
```

아직 금지해야 하는 claim:

```text
H002 solves reliable 3D Scene Graph relation reasoning for all relation families.
```

Full review artifact:

```text
artifacts/compatibility_dataset_v3_h002_experiment_stage_remaining_gap_review_after_ablation_result_review/
```

Next TODO:

```text
h002_experiment_stage_normalization_and_no_route_geometry_sensitivity_after_gap_review
```
