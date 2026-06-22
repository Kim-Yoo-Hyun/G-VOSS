# H001_v2 Evaluation Plan

Last updated: 2026-06-22 KST

## Evaluation Goal

The evaluation asks whether a predeclared risk-controlled semantic reranker
improves H001_v1's reliability tradeoff without relying on post-hoc fusion
tuning.

Primary comparison:

```text
H001_v1 probabilistic_recalibrated: semantic_score * p_geom_valid
H001_v2 risk_controlled_pooled_tau: semantic ranking under calibrated violation-risk constraint
```

## Primary Metrics

Use the same K grid as current low-K policy:

```text
K = {5, 10, 20, 50, 100}
```

Metrics:

- `R@K`
- `Violation@K`
- selected prediction count at K
- geometry coverage at K
- recall retention versus `semantic_only`
- violation reduction versus `semantic_only`
- violation reduction versus `probabilistic_recalibrated`
- risk budget pass/fail

## Primary Sources

If implementation is approved, evaluate on:

- VL-SAT full official validation.
- Open3DSG full-validation `recovery_relaxed_views_min2/`.

Do not choose `tau*` using either source evaluation result.

## Required Tables

Table A: calibration threshold selection.

| Field | Meaning |
| --- | --- |
| `alpha` | predeclared violation budget |
| `delta` | upper-bound confidence parameter |
| `tau*` | selected risk threshold |
| `U(tau*)` | held-out calibration upper bound |
| `V(tau*)` | held-out calibration empirical violation |
| `selected_count` | held-out calibration eligible rows |

Table B: source metrics.

| Condition | R@5 | R@10 | R@20 | R@50 | R@100 | V@5 | V@10 | V@20 | V@50 | V@100 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `semantic_only` | | | | | | | | | | |
| `probabilistic_recalibrated` | | | | | | | | | | |
| `rule_verified_point_subtype` | | | | | | | | | | |
| `h001_v2_risk_controlled_pooled_tau` | | | | | | | | | | |

Table C: coverage and selected-count.

This table is mandatory because risk control may reduce the number of eligible
top-K predictions.

## Controls

H001_v2 must keep existing H001 controls:

- `control_p_geom_valid_only`
- `control_distance_only`
- `control_shuffled_geometry`
- `control_wrong_pair_geometry`

Additional H001_v2-specific controls:

- apply `tau*` to shuffled geometry risk.
- apply `tau*` to wrong-pair geometry risk.
- report whether risk budget still appears satisfied under corrupted geometry.

Expected behavior:

```text
wrong-pair/shuffled geometry should degrade the selected set or fail the same reliability pattern
```

If corrupted geometry preserves the same gains, H001_v2 is not demonstrating
object-pair-specific geometry risk control.

## Bootstrap / Uncertainty

Use the existing deterministic subgraph bootstrap style after H001_v2 source
metrics are generated:

- resample subgraphs.
- keep the selected `tau*` fixed.
- report CI for `Delta R@K` and `Delta Violation@K`.

Do not reselect `tau*` inside bootstrap samples for the primary result.

## Pass Criteria

H001_v2 is worth promoting beyond hypothesis-stage if:

- the primary pooled `tau*` is feasible under edge-level `alpha=0.05`.
- source evaluation shows lower `Violation@K` than `probabilistic_recalibrated`
  at K=10/20/50/100 on at least one main source without collapse in recall.
- Open3DSG and VL-SAT trends are directionally consistent or the source-specific
  difference is explained by coverage/source-score calibration.
- wrong-pair/shuffled geometry controls do not reproduce the same trend.
- coverage loss is explicit and acceptable.

Falsification:

- no threshold satisfies `alpha=0.05`.
- risk-controlled reranking becomes equivalent to hard rule filtering with no
  meaningful recall retention.
- `semantic_score * p_geom_valid` dominates H001_v2 on both recall and
  violation.
- corrupted geometry controls preserve the improvement.
- source evaluation requires changing `alpha`, `tau_grid`, or threshold policy.
