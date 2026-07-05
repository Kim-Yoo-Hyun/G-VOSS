# H002 Figure Plan

## Frozen Figure Boundary

The figures must visually separate the framework from the validated result:

- Figure 1 can show the full relation-aware evidence routing framework.
- Figure 2 should show the leakage boundary and score flow for the validated
  `C_e` route.
- Figure 3 should report the validation-level comparison-route
  Recall/Violation tradeoff.
- Figure 4 should show support/contact as a hard-route failure taxonomy, not a
  solved route.

Captions must state that `relative_vertical` and `size_relative` are the
current validated quantitative route. Other routes are framework, diagnostic,
or future evidence unless separately validated.

## Caption-Ready Claim Sync

Figure 1 caption:

```text
Relation-aware evidence routing for reliable 3D Scene Graph relations. The
framework separates predicate/object semantics T_e, predicate-independent
geometry evidence G_e, source confidence Z_e, and evidence quality Q_e. The
validated route computes C_e = compatibility(T_e, G_e) before combining it with
Z_e for final reranking. Other routes indicate geometry-only, observability,
or semantic/structural evidence requirements and are not all claimed as solved.
```

Figure 2 caption:

```text
Leakage boundary for predicate-geometry compatibility. C_e is computed from
model-safe T_e and G_e fields, while source rank Z_e enters only in the final
reranking score. Ground-truth, violation labels, and construction fields are
hidden metric-only fields.
```

Figure 3 caption:

```text
Recall@K and Violation@K tradeoff on the official 3DSSG validation split for
the validated comparison route. Results compare source-score ranking with
S2 = normalized_source_score x C_e on VL-SAT and Open3DSG validation
predictions. This is a validation-level route-specific result, not an official
test or all-relation benchmark.
```

Figure 4 caption:

```text
Support/contact failure taxonomy. These examples illustrate why contact and
pose relations require richer local geometry, mesh, and observability evidence.
They are used to bound the framework and motivate future hard-route evidence,
not to claim support/contact is solved.
```

## Figure 1: Factorized Reliability Framework

Purpose: show why source confidence is not relation reliability.

Panels:

1. relation candidate edge
2. factor split into `T_e`, `G_e`, `Z_e`, `Q_e`
3. `C_e = compatibility(T_e, G_e)` with `Z_e` excluded
4. final reranking `S2 = Z_e x C_e`
5. selective decision `p_obs -> p_rel`
6. route selector: geometry-only, predicate-geometry, observability-heavy, or
   semantic/structural route

Boundary: GT and violation labels appear only on the metric side. Caption must
state that the figure describes the route-aware framework, while the current
quantitative validation is limited to the comparison route.

## Figure 1b: Relation Route Map

Purpose: prevent the reviewer from reading H002 as a universal scalar scorer.

Content:

- comparison route: current main success
- proximity route: geometry-only control/generality
- support/contact route: hard-route failure taxonomy
- attachment/containment route: observability-heavy future route
- semantic/structural route: abstain or separate reasoning route

This can be a compact side panel in Figure 1 rather than a separate figure if
space is tight.

Caption boundary: this is a route-assignment map, not an all-relation result
summary.

## Figure 2: Leakage Boundary / Score Flow

Purpose: make the shortcut defense explicit.

Artifact sources:

```text
experiments/H002_compatibility_routing/source_reranking_materialization/latest/
experiments/H002_compatibility_routing/source_reranking_schema_audit/latest/
```

Panels:

1. `model_safe_ce_view.jsonl`: `T_e + G_e`
2. `source_rank_view.jsonl`: `Z_e`
3. `hidden_metric_manifest.jsonl`: GT/violation, metric-only
4. score output table: Recall@K / Violation@K

## Figure 3: Recall-Violation Tradeoff

Purpose: show validation-level tradeoff with CI.

Artifact source:

```text
experiments/H002_compatibility_routing/source_reranking_ci/latest/
```

Plot:

- X axis: K = 5, 10, 20, 50, 100
- curves: `S0_source_score`, `S2_source_x_Ce`
- metrics: Recall@K and Violation@K
- include bootstrap CI bands or error bars

Caption must say official 3DSSG validation split, not official test.
Caption must also say comparison-route validation result, not all-relation
benchmark.

## Figure 4: Support/Contact Failure Taxonomy

Purpose: show hard-route limitation rather than success.

Artifact source:

```text
experiments/H002_compatibility_routing/support_contact_harder_evaluation/latest/
```

Panels:

1. predicate direction / orientation failure
2. standing vs lying ambiguity
3. class-pair shortcut risk
4. contact/pose/mesh/observability insufficiency
