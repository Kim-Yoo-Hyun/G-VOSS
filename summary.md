# RelCompat3D Research Summary

Last updated: 2026-07-27 KST.

## Research Task

3D scene graph predictors can rank semantically plausible relations that are
inconsistent with the reconstructed geometry of the corresponding ordered
subject–object pair. RelCompat3D studies this mismatch for fixed predictions
rather than replacing the source relation generator.

The method separates:

- predicate semantics T;
- predicate-independent ordered-pair measurements G;
- the source relation score Z;
- learned predicate–geometry compatibility C.

Predictor identity and Z are excluded from compatibility estimation. The fitted
compatibility is averaged over applicable relation-preserving endpoint and
predicate transformations and combined with Z only during re-ranking.

## Method Scope

Two proposed estimators share the same training rows, counterfactual targets,
loss, transformations, product utility, and family-aware ranking rule:

- RelCompat3D-Linear: family-specific linear compatibility heads;
- RelCompat3D-MLP: a compact nonlinear estimator shared across families.

The evaluation families are support/contact, proximity, and vertical order. The
re-ranking scope is narrower: proximity and vertical-order candidates are
reordered within their source-family positions, while support/contact
candidates retain their source order.

## Evaluation Contract

- Predictors: VL-SAT, Open3DSG, and SGFN.
- Target: 157 3DSSG validation scans, 548 contexts, and 3,972 exact-label
  ground-truth relations.
- Metrics: exact-label Recall@K and verifier-derived Violation@K.
- K values: 5, 10, 20, 50, and 100.
- Uncertainty: uncertain verifier outputs enter the primary denominator but not
  the violation numerator; coverage and decidable-only summaries are retained
  in the compact evidence.
- Intervals: paired scan-level resampling keeps all contexts from a sampled scan
  together.

## Main K=50 Point Estimates

All values are percentages.

| Predictor | Source R/V | Linear R/V | MLP R/V |
| --- | ---: | ---: | ---: |
| VL-SAT | 92.72 / 2.68 | 92.77 / 1.97 | 92.72 / 1.89 |
| Open3DSG | 40.43 / 13.87 | 44.18 / 3.42 | 46.70 / 4.13 |
| SGFN | 74.02 / 3.85 | 74.50 / 2.63 | 74.57 / 2.58 |

Across the reported predictor–K settings, both variants have Recall point
estimates no lower and Violation point estimates no higher than the
corresponding source ranking. This is a point-estimate statement; interval
support varies by predictor and K.

## Supporting Evidence

- Wrong-predicate, wrong-pair, shuffled-geometry, fixed-predicate endpoint-swap,
  distance-only, and compatibility-only controls test the method factors.
- Rank-average and reciprocal rank fusion use the same family-aware ranking
  procedure; Product (all families) tests re-ranking support/contact as well.
- Point- and mesh-based measurements reproduce the direction of the main
  changes under an alternative geometric construct.
- Feature-removal and counterfactual-policy analyses probe partial dependence
  between the compatibility targets and the primary OBB-derived verifier.
- Matched Linear/MLP diagnostics show a small, estimator-dependent effect from
  the linked pairwise term. Transformation averaging changes aggregate metrics
  little but makes transformed compatibility and top-\(K\) membership exactly
  consistent.
- A frozen post-hoc score-mapping analysis retains the favorable
  Recall--Violation direction in all 75 Linear and 74/75 MLP conditions across
  five smooth non-identity mappings. A percentile condition produces small
  Recall losses, so the evidence supports bounded robustness rather than
  score-scale invariance.
- At \(K=50\), both learned variants Pareto-dominate a non-learned
  training-positive robust-density baseline for all three predictors.
  Evaluation-verifier Hard-tail and Hard-drop routes are retained only as
  non-deployable diagnostics.
- A matched routing control keeps support/contact positions and identities
  fixed while merging proximity and vertical order into one queue. Its mixed
  estimator- and \(K\)-dependent effects show that family slots are a
  composition-preserving constraint, not an aggregate-optimal route.
- A hash-verified construct-dependence package records which information is
  shared by target construction, the primary verifier, and the point/mesh
  audit. Point/mesh Violation is lower in 14 of 15 cells and tied once for each
  estimator, while three uncertainty policies are non-increasing in all 30
  estimator--predictor--\(K\) cells.
- Five predeclared fitting executions reproduce Linear exactly. MLP variation
  is small overall, with one VL-SAT \(K=50\) seed trading one exact-label
  relation for lower Violation; seed-uniform Pareto improvement is not
  claimed.
- A pseudonymized row-level regeneration check reproduces 291 canonical cells
  from Tables 1--3 and Figure 3 data with maximum absolute error zero.
- Candidate-pool exact-label coverage is 99.72% for VL-SAT and SGFN and 79.68%
  for Open3DSG. At \(K=50\), the active-route oracle Recall is 96.73%, 86.05%,
  and 63.72%, respectively, quantifying both remaining ranking headroom and
  missing-candidate limits without treating the oracle as model performance.
- The ReplicaSSG/FROSS result is retained only as a transfer stress test, not
  dataset-level generalization evidence.
- A bounded CPU benchmark measures re-ranking after rows and pair geometry are
  loaded; it is not end-to-end source inference latency.

## Reproducibility Boundary

The public submission tree includes the active code, protocols, fitted model
locks, compact summaries, Docker configuration, regenerated paper tables and
figure data, and candidate-pool oracle summaries. Full numerical reruns need
external source rows and public datasets. Source checkpoints, feature caches,
raw verifier outputs, meshes, and raw point/mesh audit rows are intentionally
excluded from Git. A pseudonymized derived-row bundle is generated locally,
but public redistribution is held until the dataset terms are confirmed.

The active integrity hashes are stored in
experiments/RelCompat3D_geom_reliability/active_method.json. The compact result map is
results/relcompat3d_geom_reliability/manifest.json.

## Manuscript State

The selected source is paper/aaai/main.tex. A fresh Docker build is nine
pages. Technical content ends and the references begin on page 7; references
continue on pages 8--9. The prior horizontal overflow and first-page vertical
overfull are resolved.

The latest synchronized candidate release is
release/relcompat3d_aaai27_openreview_20260728_214915/. It is regenerated from
the current manuscript, supplement, checklist, figures, method locks, source,
and compact evidence and is held as a candidate until the remaining layout and
submission-system disclosure checks are resolved.

## Claim Boundary

The evidence supports a scoped reliability layer for fixed predictions on the
shared 3DSSG validation scenes. It does not establish broad SOTA, dataset-level
generalization, calibrated physical-validity probabilities, or solved
support/contact relations.
