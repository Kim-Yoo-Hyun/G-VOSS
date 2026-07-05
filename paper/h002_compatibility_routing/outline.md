# H002 Paper Outline

## Working Title

Semantic-Geometry Compatibility Learning for Reliable 3D Scene Graph Relations

## Abstract Shape

Existing 3D Scene Graph relation sources produce confidence scores for relation
edges, but those scores conflate semantic plausibility, source ranking priors,
geometry compatibility, and evidence quality. H002 proposes a route-aware
factorized reliability framework: relation families are not forced through one
fixed semantic-geometry fusion, but are assigned evidence routes such as
geometry-only compatibility, predicate-geometry compatibility,
observability-aware abstention, or semantic/structural reasoning. The current
paper validates the central compatibility route on geometry-checkable
comparison relations. The key compatibility score
`C_e = compatibility(T_e, G_e)` is computed without source score leakage and is
combined with source confidence only for final reranking. On VL-SAT and
Open3DSG validation predictions over the official 3DSSG validation split,
compatibility-aware reranking improves the recall/violation tradeoff against
source-score ranking. The paper also reports controls, bootstrap uncertainty,
and a support/contact failure taxonomy that bounds the route-generalization
claim. We do not claim an official test benchmark, SOTA result, calibrated
p_obs/p_rel solution, or completed all-relation reliable 3D relation framework.

## Contributions

1. Relation-aware evidence-route framing that separates geometry-decidable,
   predicate-geometry, observability-heavy, and semantic/structural relation
   families instead of forcing a universal scorer.
2. Factorized relation reliability formulation for 3D Scene Graph edges:
   `T_e`, `G_e`, `Z_e`, `C_e`, `Q_e`, `p_obs`, and `p_rel`.
3. Source-agnostic predicate-geometry compatibility reranking:
   `S2(e) = normalized_source_score(Z_e) * C_e`, where `C_e` is computed from
   `T_e + G_e` before source score enters the final ranking.
4. Validation-level evidence for the comparison route across VL-SAT and
   Open3DSG predictions, with Recall@K / Violation@K, bootstrap CI,
   counterfactual controls, ablations, normalization/no-route sensitivity, and
   a support/contact failure taxonomy.

## Section Plan

Sync status:

```text
h002_route_aware_paper_section_sync_after_protocol_freeze_ready = true
```

Every section must preserve this hierarchy:

```text
framework = relation-aware evidence routing
validated mechanism = predicate-geometry compatibility route
validated relations = relative_vertical,size_relative
diagnostic/future routes = proximity, support/contact, attachment, containment, semantic/structural
blocked = all-relation solved, support/contact solved, calibrated p_obs/p_rel solved, SOTA/test claim
```

### 1. Introduction

- Problem: relation confidence is not relation reliability.
- Failure: a high source score can reflect semantic plausibility or source
  prior rather than relation-level geometry compatibility.
- Need: separate semantic content, geometry evidence, source confidence, and
  observability.
- Need: route relation families by valid evidence type instead of applying one
  fixed fusion formula.
- Claim boundary: validation-level comparison-route success; broader framework
  route map; not a new 3DSSG predictor.
- Claim hierarchy: framework claim is relation-aware evidence routing;
  validated mechanism claim is predicate-geometry compatibility for comparison
  relations; other routes are taxonomy, diagnostics, or future evidence.

### 2. Related Work

- 3D Scene Graph relation prediction and open-vocabulary relation sources.
- Geometry-aware relation reasoning and relation consistency checks.
- Calibration, selective prediction, and abstention.
- Multimodal/factorized fusion and missing-evidence handling.

### 3. Problem Definition

- Relation candidate edge `e = (subject, predicate, object)`.
- Define `T_e`, `G_e`, `Z_e`, `Q_e`.
- Define `C_e`, `p_obs`, `p_rel`, and reranking score `S2`.
- Define relation routes: comparison, geometry-only, frame-aware directional,
  support/contact, observability-heavy, and semantic/structural.
- Define Recall@K and Violation@K.

### 4. Method

- Model-safe views: `T_e + G_e` for `C_e`.
- Source-rank view: `Z_e` for final reranking only.
- Hidden metric manifest: GT and violation labels never enter model input.
- `S0_source_score` baseline.
- `S2_source_x_Ce` primary score.
- Relation route map and current route status.
- Selective decision layer: `p_obs` and `p_rel` as framework component, not
  calibrated solved result.

### 5. Experiments

- Data: official 3DSSG validation split.
- Sources: VL-SAT validation predictions and Open3DSG validation predictions.
- Main validated route: `relative_vertical` and `size_relative`.
- Baselines: source-only, geometry-only, no-route geometry-only, plain
  `T_e/G_e` concat, C_e-only, shuffled-C_e, wrong-T.
- Main metrics: Recall@K, Violation@K.
- Uncertainty: bootstrap CI.
- Failure analysis: support/contact hard route.
- Generality analysis: route map explains which relation families are current
  success, control, hard route, or future route.

### 6. Results

- Main validation reranking table.
- Route-readiness table as framework analysis, not all-route performance.
- CI table or figure.
- Controls and caveats.
- p_obs/p_rel stress-test result with calibration boundary.
- Support/contact failure taxonomy.

### 7. Limitations

- No official 3DSSG relation test GT used.
- Open3DSG is an open-vocabulary source but evaluated through closed 3DSSG
  mapping.
- `Violation@K` is a custom geometry metric.
- Support/contact is a hard-route failure taxonomy, not solved.
- Calibrated p_obs/p_rel remains blocked.
- Rank-percentile normalization loses low-K recall, so the result is not
  claimed as normalization-invariant.

### 8. Conclusion

- Relation reliability requires route-aware factorized evidence, not fixed
  fusion.
- H002 provides a source-agnostic validation-level compatibility route and a
  roadmap toward a general reliable 3D relation framework.
