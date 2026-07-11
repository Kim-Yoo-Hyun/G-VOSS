# H002 Proximity Geometry-Only Route Diagnostic

## Status

```text
status = h002_proximity_geometry_only_route_diagnostic_ready
validation_errors = 0
paper_draft_expansion_allowed = false
next_todo = none_frozen_geometry_only_control
```

## Decision

`proximity` / `close by`는 H002에서 `T_e x G_e` interaction 성공 사례가 아니라
geometry-only route/control로 고정한다.

핵심 해석:

- `close by`는 object-pair distance 같은 `G_e`만으로 거의 결정되는 route다.
- source score나 class-pair shortcut으로 설명되는 target이 아니다.
- shuffled/wrong-pair geometry control이 붕괴하므로 실제 object-pair geometry가 필요하다.
- 따라서 relation-aware evidence routing에서 “모든 relation에 같은 compatibility head가 필요한 것은 아니다”를 보여주는 control 역할을 한다.

## Source-Wide Validation Diagnostic

| Source | K | S0 Recall | S2 Recall | Δ Recall | S0 Violation | S2 Violation | Δ Violation | Pass |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| open3dsg_recovery_relaxed_views_min2 | 20 | 0.427778 | 0.426389 | -0.001389 | 0.191146 | 0.189816 | -0.001330 | True |
| open3dsg_recovery_relaxed_views_min2 | 50 | 0.768056 | 0.765278 | -0.002778 | 0.158627 | 0.157362 | -0.001265 | True |
| vlsat_full_validation | 20 | 0.914496 | 0.914496 | 0.000000 | 0.072810 | 0.072263 | -0.000547 | True |
| vlsat_full_validation | 50 | 0.977350 | 0.975085 | -0.002265 | 0.200228 | 0.195677 | -0.004551 | True |

요약하면 `proximity`는 source-wide route summary에서 `4/4` route cells를 통과했다. 다만 이 통과는 Recall 개선 때문이 아니라 Violation non-increase / slight reduction 때문이다. 따라서 `proximity`는 main learned compatibility route가 아니라 geometry-only control이다.

## Archived R1 Close-By Geometry Controls

| Control | AUROC | Best Accuracy | Interpretation |
| --- | ---: | ---: | --- |
| `normalized_distance_xy` | 1.000000 | 1.000000 | scale-normalized XY distance solves the route target |
| `normalized_distance_3d` | 1.000000 | 1.000000 | scale-normalized 3D distance solves the route target |
| `distance_xy` | 0.999556 | 0.992500 | raw XY distance nearly solves geometry support |
| `distance_3d` | 0.998975 | 0.987500 | raw 3D distance nearly solves geometry support |
| `source_score_rank` | 0.552103 | 0.546250 | source confidence does not explain geometry support |
| `class_pair_only` | n/a | 0.503750 | class-pair shortcut is near chance |
| `p_geom_valid_hidden_baseline` | 0.999594 | 0.991250 | hidden geometry-rule reference is strong but not model input |
| `shuffled_G` | 0.336178 | 0.500000 | shuffled geometry collapses |
| `wrong_pair_geometry` | 0.006272 | 0.500000 | wrong-pair geometry collapses |

## Main Score Mechanism: `S2_current_source_x_Ce`

`S2_current_source_x_Ce`는 source confidence를 그대로 믿지 않고, source score와 compatibility score를 분리해 계산한 뒤 마지막 reranking 단계에서 결합한다.

```text
Z_e = source confidence / rank
T_e = predicate and relation-family semantic content
G_e = predicate-independent geometry evidence
C_e = compatibility(T_e, G_e)
S2(e) = normalized_source_score(Z_e) * normalized_C_e(T_e, G_e)
```

중요한 분리 원칙:

- `C_e`를 계산할 때 `Z_e`는 넣지 않는다.
- source score/rank는 final reranking에서만 사용한다.
- `Q_e`/observability, hidden construction labels, H001 `p_geom_valid`는 main `C_e` input이 아니다.

Frozen runner 기준:

```text
C_e model = logistic
C_e train rows = 4868
C_e feature count = 498
source score normalization = per_source_minmax
C_e normalization = per_source_family_minmax
primary score id = S2_source_x_Ce
```

## `C_e` Mechanism

`C_e`는 relation candidate가 가진 predicate/object semantic content `T_e`와 predicate-independent geometry evidence `G_e`가 서로 맞는지 보는 compatibility score다.

구체적으로:

1. `T_e`는 predicate, relation family, object/predicate semantic feature를 표현한다.
2. `G_e`는 distance, vertical difference, size ratio, overlap/contact proxy 등 geometry feature를 표현한다.
3. `C_e` scorer는 internal train split에서 학습된다.
4. Official validation source rows는 evaluation-only로 사용된다.
5. `C_e`가 높으면 해당 predicate가 해당 geometry와 잘 맞는다는 뜻이고, `S2`는 이 값을 source score에 곱해 top-K ranking을 조정한다.

`proximity`에서는 이 `C_e` interaction을 main success로 주장하지 않는다. 이 route는 오히려 `G_e`만으로 충분한 route라는 점이 핵심이다.

## Claim Boundary

Allowed:

```text
proximity / close by is a geometry-only route control.
```

Blocked:

```text
close by proves predicate-geometry interaction.
close by proves calibrated p_rel/p_obs reliability.
close by alone validates the full general reliable 3D relation framework.
paper draft expansion is allowed now.
```
