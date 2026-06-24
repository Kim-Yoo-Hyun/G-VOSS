# H001_v2 Risk-Aware Soft Reranking

Last updated: 2026-06-24 KST

Status: `method_framing_selected_no_new_metric_claim`

## Purpose

This file reframes the current GeoCalib semantic+geometry combination as a
principled risk-aware soft reranking objective. It does not change the locked
H001/GeoCalib source metrics. It explains why the deployed score is defensible
and why the fixed-`tau*` hard-threshold variant remains diagnostic.

## Objective

For a candidate relation edge `e`, let:

```text
S(e) = semantic source utility
G(e) = p_geom_valid(e)
R_geom(e) = -log G(e)
```

GeoCalib ranks edges by:

```text
U_lambda(e) = log S(e) - lambda * R_geom(e)
```

Equivalently:

```text
U_lambda(e) = log S(e) + lambda * log G(e)
score_lambda(e) = S(e) * G(e)^lambda
```

The current paper-facing GeoCalib score is the `lambda = 1` instance:

```text
score(e) = semantic_score(e) * p_geom_valid(e)
```

Thus the current method can be described as calibrated risk-aware soft
reranking, not as an arbitrary multiplication heuristic.

## Why Soft Reranking

The H001 goal is not to remove every geometrically risky edge at all costs. The
goal is:

```text
preserve top-K semantic utility while reducing calibrated geometry-inconsistency risk
```

A hard threshold such as `p_geom_valid >= 0.80` can be principled as a risk
constraint, but the executed H001_v2 diagnostic shows that it can remove too
many useful candidates. Soft reranking keeps all candidates in the ranking and
penalizes risk continuously.

## Relation To Fixed-Tau Diagnostic

The fixed-`tau*` run selected:

```text
tau* = 0.20
p_geom_valid >= 0.80
```

from held-out calibration rows only. Source metrics and tau corruption controls
showed:

- real geometry signal is present: shuffled/wrong-pair tau controls are worse
  than H001_v2 on both sources.
- the hard threshold is too aggressive for the current main method: VL-SAT
  recall collapses and H001_v2 does not dominate `probabilistic_recalibrated`.

Interpretation:

- fixed-`tau*` is useful diagnostic evidence.
- it should not replace the current GeoCalib main table.
- it motivates keeping a soft utility-risk objective as the main method
  framing.

## Guardrails

- Do not choose `lambda` from validation/test source metrics.
- The current paper does not introduce a new tuned `lambda`; it uses the
  already-reported `lambda = 1` score.
- Any future `lambda != 1`, additional family-specific penalty change, or
  coverage-aware fallback must be frozen before source evaluation.
- Missing, unsupported, and uncertain geometry must be reported as coverage and
  uncertainty states rather than hidden as successful risk reduction.

## Future Extensions

| Extension | Role |
| --- | --- |
| `family-conditional risk` | Uses relation-family-specific calibrators so support/contact, proximity, and vertical relations do not share one pooled geometry-risk surface. This is now the preferred H001_v2 direction. |
| `coverage-aware` | Keeps explicit states for covered, unsupported, missing, and uncertain geometry so recall loss is attributable. |
| `risk-aware soft lambda` | Allows a predeclared `lambda` or calibration-derived penalty strength if a future protocol needs a different recall-violation operating point. |

Current decision:

- Use this objective to strengthen the GeoCalib method explanation.
- Keep the locked H001/GeoCalib metrics unchanged.
- Keep fixed-`tau*` H001_v2 as diagnostic evidence only.
- Treat `family_specific_p_geom_valid` as `family_conditional_risk` for H001_v2
  method development rather than as a generic control condition.
- Keep pooled `lambda=1` as the current H001 main score unless the paper is
  explicitly revised to promote family-conditional risk.
