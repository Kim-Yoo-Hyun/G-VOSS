# H001_v2 Risk-Control Protocol

Last updated: 2026-06-24 KST

## Protocol Version

```text
h001_v2_risk_controlled_reranking_protocol_v0
```

This is the diagnostic fixed-threshold protocol. It records the hard-risk
variant that was executed after the 2026-06-22 schema probe: edge-level
threshold selection from held-out calibration score rows, followed by
fixed-threshold top-K source evaluation.

It is no longer the preferred H001_v2 main-method framing. The selected method
framing is risk-aware soft reranking, where the current GeoCalib
`semantic_score * p_geom_valid` score is interpreted as the `lambda=1`
log-linear utility-risk objective. The current H001_v2 development direction is
the family-conditional calibrated-risk variant documented in
`11_family_conditional_risk_result.md`. See
`09_risk_aware_soft_reranking.md` for the shared objective framing.

## Fixed Inputs

Relation families:

```text
support_contact
proximity
relative_vertical
```

K grid:

```text
K = {5, 10, 20, 50, 100}
```

Primary risk budget:

```text
alpha = 0.05
delta = 0.05
```

Diagnostic secondary budget:

```text
alpha = 0.10
delta = 0.05
```

`alpha=0.05` is the primary H001_v2 operating point because it corresponds to a
clear top-K geometric-violation budget rather than a tuned performance target.
`alpha=0.10` is diagnostic only and must not replace the primary result after
looking at full-validation metrics.

## Edge Risk

For every geometry-checkable prediction edge `e`:

```text
r(e) = 1 - p_geom_valid(e)
```

where `p_geom_valid(e)` is the frozen H001 calibrated geometry-validity
probability from the existing H001 geometry join.

Rows without deployable `p_geom_valid` are not assigned a risk-controlled score.
They remain outside the H001_v2 primary selection set and must be counted under
coverage.

## Selection Rule

For a candidate threshold `tau`:

```text
A_tau = {e | r(e) <= tau}
TopK_tau(g) = top-K edges in subgraph g from A_tau, sorted by semantic_score
```

This hard-threshold diagnostic does not multiply semantic score by geometry
score. Geometry determines which edges are eligible under the risk budget.
Semantic score remains the utility ranking inside the feasible set.

If fewer than K eligible in-scope predictions exist in a subgraph, select the
available eligible predictions and report selected-count / coverage.

## Candidate Threshold Set

The threshold set is fixed before source evaluation:

```text
tau_grid = {0.00, 0.01, 0.02, ..., 0.99, 1.00}
```

Equivalent `p_geom_valid` thresholds are:

```text
p_geom_valid >= 1 - tau
```

No threshold may be inserted after seeing validation/test source metrics.

## Primary Calibration Set

Primary threshold selection uses:

```text
archive/hypothesis_records/hypothesis/CAND-001/H001_geometry-grounded-verification/artifacts/calibration/p_geom_valid_smoke/scores.jsonl
```

with:

```text
role == "dev"
```

Rationale:

- `p_geom_valid_smoke/scores.jsonl` contains the deployable H001
  `p_geom_valid` score and `label.geom_valid` target.
- `role == "train"` rows were used to fit the geometry-validity model and must
  not select `tau*`.
- `train_dev_calib/table.jsonl` is provenance input but lacks deployable
  `p_geom_valid` and source semantic ranks.

## Calibration Quantity

For each candidate `tau` on held-out calibration score rows:

```text
n(tau) = calibration rows with r(e) <= tau
v(tau) = eligible calibration rows with label.geom_valid == 0
V(tau) = v(tau) / n(tau)
```

The calibration risk statistic is:

```text
L(tau) = U(tau)
```

where `U(tau)` is a one-sided finite-sample upper confidence bound for the
eligible-set binomial violation rate.

The current artifacts do not contain source semantic ranking distributions for
the calibration split. Therefore top-K `Violation@K` is evaluated only after
`tau*` is fixed; it is not used to choose `tau*`.

## Upper Bound Rule

Use a one-sided Clopper-Pearson upper bound:

```text
U(tau) = CP_upper(v(tau), n(tau), delta)
```

Primary feasibility condition:

```text
U(tau) <= alpha
```

The exact implementation can use a standard beta quantile implementation. If
the local dependency stack lacks a beta quantile, the implementation must record
the fallback bound and validate that it is conservative before any metric claim.

## Threshold Choice

Select:

```text
tau* = max { tau in tau_grid | U(tau) <= alpha }
```

This chooses the least restrictive threshold that satisfies the risk budget and
therefore maximizes semantic candidate retention under the fixed constraint.

If no `tau` satisfies the condition:

```text
status = risk_budget_infeasible
```

Then H001_v2 must report infeasibility rather than loosening `alpha`, changing
the grid, or switching to source-specific thresholds.

## Primary Policy

Primary H001_v2 policy:

```text
pooled_tau_single_threshold
```

Meaning:

- one shared `tau*`;
- pooled across the three H001 relation families;
- pooled across calibration rows;
- not source-specific.

Rationale:

- avoids source-specific post-hoc tuning.
- keeps H001_v2 as a general reliability layer.
- makes source transfer measurable.

## Diagnostic Policies

Allowed diagnostic policies:

| Policy | Purpose | Main-claim status |
| --- | --- | --- |
| `family_tau_bonferroni` | Test whether family-specific hard-threshold risk control is needed. | appendix/diagnostic |
| `source_tau_bonferroni` | Test source calibration mismatch. | diagnostic only |
| `alpha_0_10_pooled` | Sensitivity to a looser violation budget. | diagnostic only |

Diagnostic policies cannot replace the primary policy unless a new protocol
freeze is created before source evaluation.

## Baselines

Required comparisons:

- `semantic_only`
- `probabilistic_recalibrated` = `semantic_score * p_geom_valid`
- `rule_verified_point_subtype`
- `control_family_specific_p_geom_valid`
- `control_p_geom_valid_only`
- `control_shuffled_geometry`
- `control_wrong_pair_geometry`
- `h001_v2_risk_controlled_pooled_tau`

## Claim Conditions

The fixed-threshold diagnostic can be claimed as an improvement over the current
GeoCalib main method only if:

- `tau*` is selected using the frozen calibration protocol only.
- full-validation source metrics use the fixed `tau*`.
- the calibration policy satisfies or transparently fails the predeclared
  edge-level violation budget check.
- recall retention is reported, not hidden.
- source coverage and selected-count reductions are reported.
- top-K source `Violation@K` is reported as fixed-threshold evaluation, not as
  a calibration guarantee.
- controls show that shuffled/wrong-pair geometry cannot reproduce the result.

The executed `tau*=0.20` result does not satisfy this promotion condition
because it has geometry-specific controls but causes VL-SAT recall collapse and
does not dominate `probabilistic_recalibrated`. It should remain diagnostic
evidence.
