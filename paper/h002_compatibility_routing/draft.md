# H002 Draft Skeleton

## Title

Semantic-Geometry Compatibility Learning for Reliable 3D Scene Graph Relations

## Abstract

3D Scene Graph relation sources assign confidence scores to predicted relation
edges, but a single confidence score does not reveal whether an edge is reliable.
A relation can score highly because it is semantically plausible, because the
source model has a class prior, or because the local 3D geometry actually
supports the predicate. We propose a route-aware factorized relation reliability
framework that separates predicate semantic content, predicate-independent
geometry evidence, source confidence, and observability. Rather than forcing all
relation families through one fixed semantic-geometry fusion, the framework treats
relations as requiring different evidence routes: geometry-only compatibility,
predicate-geometry compatibility, observability-aware abstention, or
semantic/structural reasoning. The current paper validates the central
predicate-geometry compatibility route for geometry-checkable comparison
relations. Our key score computes compatibility before combining it with source
confidence for final reranking. On VL-SAT and Open3DSG validation predictions
over the official 3DSSG validation split, this compatibility-aware reranking
improves the Recall@K and Violation@K tradeoff compared with source-score
ranking. We further report counterfactual controls, bootstrap confidence
intervals, and a support/contact failure taxonomy that bounds where the current
evidence is sufficient. The result is a scoped validation-level
comparison-route claim, not an official test benchmark or a completed
all-relation reliability result.

## Section-Ready Claim Sync

Use these paragraphs as the synchronized paper wording. They follow the frozen
route-aware hierarchy and should replace looser internal phrasing when the
manuscript moves from notes to prose.

### Introduction Thesis

Existing 3D Scene Graph relation sources produce ranked relation candidates,
but their confidence scores do not identify why an edge should be trusted. A
high score can reflect a source prior over object classes, a semantically
plausible predicate, or genuine geometric support in the scene. Treating these
signals as one scalar relation reliability score is therefore under-specified:
some relation families are geometry-decidable, some require compatibility
between predicate semantics and geometry, some require an observability-aware
abstention decision, and some are primarily semantic or structural. We frame
reliable 3D relation estimation as relation-aware evidence routing.

### Method Thesis

For a candidate edge, the method separates predicate/object semantic content
`T_e`, predicate-independent geometry evidence `G_e`, source confidence `Z_e`,
and evidence quality `Q_e`. The compatibility score `C_e` is computed from
`T_e` and `G_e` before source confidence is used, so the compatibility module
cannot simply copy source rank or source confidence. Final validation-level
reranking uses `S2(e) = normalized_source_score(Z_e) * C_e`. This makes the
validated mechanism a predicate-geometry compatibility route inside a broader
relation-aware evidence routing framework.

### Experiment Thesis

The main quantitative result evaluates the validated comparison route on the
official 3DSSG validation split using VL-SAT and Open3DSG validation
predictions. The primary comparison is between source-score ranking and
compatibility-aware reranking over `relative_vertical` and `size_relative`
relations. Recall@K measures retained GT relation coverage, while Violation@K
measures geometry-inconsistent ranked predictions. This experiment validates
the predicate-geometry compatibility route; it is not an official test,
leaderboard, SOTA, or all-relation reliability benchmark.

### Boundary Thesis

The route-aware framework is broader than the current quantitative result. The
comparison route is validated; proximity is treated as a geometry-only control;
support/contact is a hard-route failure taxonomy; observability-heavy relations
such as attachment and containment require visual/mesh evidence and `Q_e`; and
semantic/structural relations require separate evidence routes. We therefore
claim a relation-aware framework with a validated predicate-geometry
compatibility route, not a completed general reliable 3D relation framework.

## Introduction Notes

The paper should open from the reliability mismatch:

```text
source confidence != geometry compatibility != relation reliability
```

The design argument should be:

1. Source confidence `Z_e` is useful but can copy source priors.
2. Geometry evidence `G_e` must be predicate-independent to avoid encoding the
   predicate answer directly.
3. Compatibility `C_e = compatibility(T_e, G_e)` is needed because the same
   geometry can support one predicate and contradict another.
4. Observability `Q_e` is needed because some edges should be abstained rather
   than forced into accept/reject.
5. A reliable 3D relation framework must be route-aware: proximity,
   comparison, support/contact, attachment/containment, and structural
   relations do not use the same valid evidence.

Use this claim hierarchy consistently:

```text
framework claim = relation-aware evidence routing is needed
validated mechanism claim = T_e x G_e compatibility route improves source reranking
route taxonomy claim = different families require different evidence routes
boundary claim = H002 does not solve all 3DSSG relation families
```

## Method Notes

Use this formula as the central method:

```text
S2(e) = normalized_source_score(Z_e) * C_e
```

State clearly:

- `C_e` is fit from `T_e + G_e`.
- `Z_e` is not an input to `C_e`.
- GT and violation labels are hidden metric-only fields.
- `p_obs/p_rel` are included as selective-decision framework components, but
  calibrated quantitative claims are blocked by the current calibration audit.
- no-route geometry-only and raw-product sensitivity support the scoped S2
  result, but rank-percentile normalization prevents normalization-invariant
  wording.

## Result Notes

Main result should use the validation table:

```text
K = {5, 10, 20, 50, 100}
S0 = source score
S2 = source score x C_e
metrics = Recall@K, Violation@K
```

The strongest result pattern is that `S2` consistently reduces Violation@K and
improves Recall@K at K = 10, 20, and 50 with bootstrap support. K = 5 and K =
100 need more careful wording for recall because the CI includes or touches
zero.

The main success route is currently limited to geometry-checkable comparison
relations (`relative_vertical`, `size_relative`). Support/contact is a hard
route failure taxonomy, while proximity, frame-aware directional, attachment,
containment, and semantic/structural relations are route-map evidence or future
work unless additional route-specific experiments pass.

`I4_calibrated_route_aware_source_x_Ce` can be mentioned as a candidate
improvement-path ablation, but the main result should keep
`S2_current_source_x_Ce` because family-wise regressions remain unresolved.

## Limitations Notes

Do not overclaim:

- no official test benchmark
- no SOTA claim
- no solved support/contact claim
- no calibrated p_obs/p_rel solved claim
- no completed all-relation reliable 3D relation framework claim
- validation-level result only
