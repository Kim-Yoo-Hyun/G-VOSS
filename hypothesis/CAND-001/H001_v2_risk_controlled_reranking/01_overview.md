# H001_v2 Overview

Last updated: 2026-06-24 KST

## Status

- Stage: method-framing update.
- Branch: `hypothesis/CAND-001/H001_v2_risk_controlled_reranking/`
- Working name: `Family-Conditional Risk-Aware Soft Reranking`
- Relation to H001: same scoped reliability layer, upgraded combination rule.

## Motivation

GeoCalib currently uses a simple calibrated late-fusion rule:

```text
score(e) = semantic_score(e) * p_geom_valid(e)
```

This rule should not be framed as an arbitrary heuristic. It is the deployed
log-linear form of a risk-aware soft reranking objective:

```text
U_lambda(e) = log semantic_score(e) - lambda * R_geom(e)
R_geom(e) = -log p_geom_valid(e)
```

Equivalently:

```text
U_lambda(e) = log semantic_score(e) + lambda * log p_geom_valid(e)
score_lambda(e) = semantic_score(e) * p_geom_valid(e)^lambda
```

The current GeoCalib operating point is `lambda = 1`, which gives the existing
`semantic_score * p_geom_valid` ranking. This preserves top-K semantic utility
softly while penalizing calibrated geometric inconsistency risk.

The current H001_v2 method-development direction keeps the same soft-risk
objective but makes the geometry-risk surface relation-family conditional:

```text
p_geom_valid_family(e) = C_family(phi(g_e))
score_family(e) = semantic_score(e) * p_geom_valid_family(e)
```

This avoids forcing support/contact, proximity, and relative-vertical relations
to share one pooled geometry-validity calibration surface.

The earlier fixed-threshold H001_v2 experiment tested a hard-risk variant:

```text
maximize semantic utility subject to p_geom_valid >= 0.80
```

That variant is now diagnostic only because it confirms geometry-specific
signal but collapses VL-SAT recall.

## Core Hypothesis

For geometry-checkable 3D Scene Graph relation families, relation-source
semantic utility should be preserved in top-K ranking while calibrated
geometry-inconsistency risk is penalized continuously. A soft risk objective is
preferred over hard filtering because it can reduce violations without throwing
away useful semantic candidates.

## What Changes From H001_v1

| Item | H001_v1 | H001_v2 |
| --- | --- | --- |
| Combination | `semantic_score * p_geom_valid` | risk-aware soft reranking objective whose `lambda=1` instance is the current deployed score |
| Main object | ranking score | semantic utility minus calibrated geometry-risk penalty |
| Tuning surface | fixed multiplication | predeclared risk-penalty interpretation; family-conditional risk is frozen from train/dev calibration |
| Geometry use | continuous multiplicative weight | continuous calibrated family-conditional inconsistency-risk penalty |
| Claim | calibrated geometry-aware reranking reduces violations | calibrated family-conditional soft risk penalty preserves top-K utility while reducing geometry-inconsistent edges |

## Claim Boundary

Allowed H001_v2 method-framing claim:

> GeoCalib performs risk-aware soft reranking for geometry-checkable relation
> families: it preserves semantic source utility while penalizing calibrated
> relation-level geometric inconsistency risk. The deployed pooled
> `semantic_score * p_geom_valid` score is the `lambda=1` log-linear
> instantiation of this objective, and the H001_v2 family-conditional variant
> replaces the pooled risk surface with relation-family-specific calibrators.

Not allowed:

- broad 3DSSG generation improvement.
- source-specific post-hoc threshold tuning.
- validation/test-selected risk budgets.
- claiming the fixed-`tau*` hard-threshold variant as the main method.
- claiming the multiplication itself is the novelty independent of calibrated
  risk estimation, controls, and recall/violation evaluation.

## Why This Is Stronger Than A Better Fusion Heuristic

H001_v2 is not a learned black-box fusion model. It turns the existing
semantic+geometry combination into an explicit utility-risk objective:

```text
rank(e) by semantic utility - geometry inconsistency risk penalty
```

That makes the contribution easier to defend:

- the objective is explicit rather than described as ad hoc multiplication.
- `p_geom_valid` has a calibrated probabilistic meaning.
- top-K utility is preserved by soft penalization instead of hard removal.
- hard-threshold results are retained as diagnostic evidence showing why fixed
  eligibility constraints are too aggressive for the current main method.
- future changes to `lambda` or coverage-aware fallbacks require a new protocol
  freeze before source evaluation.
- the family-conditional risk route is now documented in
  `11_family_conditional_risk_result.md` and should not be described as a
  generic control if promoted.
