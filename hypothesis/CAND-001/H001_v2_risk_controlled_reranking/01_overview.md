# H001_v2 Overview

Last updated: 2026-06-22 KST

## Status

- Stage: hypothesis/protocol freeze.
- Branch: `hypothesis/CAND-001/H001_v2_risk_controlled_reranking/`
- Working name: `Risk-Controlled Geometry Reranking`
- Relation to H001: same scoped reliability layer, upgraded combination rule.

## Motivation

H001_v1 uses a simple calibrated late-fusion rule:

```text
score_v1(e) = semantic_score(e) * p_geom_valid(e)
```

This is interpretable and strong as a reliability baseline, but it makes a fixed
implicit assumption: semantic utility and geometry validity should always be
combined by multiplication. That assumption is not the core H001 thesis. The
core thesis is that semantic relation ranking should be constrained by
relation-level physical consistency.

H001_v2 therefore reframes the combination problem:

```text
maximize semantic recall / semantic utility
subject to a pre-specified edge-level geometry violation-risk constraint
```

## Core Hypothesis

For geometry-checkable 3D Scene Graph relation families, a predeclared
risk-controlled reranking rule can preserve the semantic-source ranking
objective while enforcing a calibration-split-derived eligibility threshold for
geometry violation risk. Top-K recall and violation are then evaluated after
semantic ranking within the fixed eligible set.

## What Changes From H001_v1

| Item | H001_v1 | H001_v2 |
| --- | --- | --- |
| Combination | `semantic_score * p_geom_valid` | semantic ranking under geometry-risk constraint |
| Main object | ranking score | feasible edge set plus semantic top-K selection |
| Tuning surface | fixed multiplication | predeclared `alpha`, `delta`, K grid, and threshold-selection rule |
| Geometry use | continuous multiplicative weight | calibrated violation-risk constraint |
| Claim | calibrated geometry-aware reranking reduces violations | risk-bounded reliability layer preserves semantic utility under a declared violation budget |

## Claim Boundary

Allowed H001_v2 claim if protocol passes:

> H001_v2 provides risk-controlled semantic reranking for geometry-checkable
> relation families: it preserves semantic ranking as the utility objective and
> uses calibrated geometry-validity risk to define a predeclared eligible set
> before selecting top-K predictions by semantic utility.

Not allowed:

- broad 3DSSG generation improvement.
- source-specific post-hoc threshold tuning.
- validation/test-selected risk budgets.
- claiming distribution-free deployment guarantees without the calibration
  exchangeability assumption and finite-sample caveats.

## Why This Is Stronger Than A Better Fusion Heuristic

H001_v2 is not a learned black-box fusion model. It is a decision rule with a
testable contract:

```text
given alpha, delta, K grid, calibration split, and candidate threshold set,
choose the least restrictive geometry-risk threshold whose calibration upper
confidence bound satisfies the edge-level violation budget, then evaluate the
fixed threshold across the K grid.
```

That makes the contribution easier to defend:

- the objective is explicit.
- the risk budget is fixed before evaluation.
- the selection rule is deterministic.
- the full-validation set is not used to pick the threshold.
- failure to satisfy the risk budget is reportable as falsification.
