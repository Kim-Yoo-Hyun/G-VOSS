# RelCompat3D Research Summary

Last updated: 2026-07-22 KST.

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
- The ReplicaSSG/FROSS result is retained only as a transfer stress test, not
  dataset-level generalization evidence.
- A bounded CPU benchmark measures re-ranking after rows and pair geometry are
  loaded; it is not end-to-end source inference latency.

## Reproducibility Boundary

The public submission tree includes the active code, protocols, fitted model
locks, compact summaries, and Docker configuration. Full numerical reruns need
external source rows and public datasets. Source checkpoints, feature caches,
row-level predictions, verifier outputs, meshes, and raw point/mesh audit rows
are intentionally excluded from Git.

The active integrity hashes are stored in
experiments/RelCompat3D_geom_reliability/active_method.json. The compact result map is
results/relcompat3d_geom_reliability/manifest.json.

## Manuscript State

The selected artifact is paper/aaai/main_teaser_aaai27.pdf. The stored PDF is
nine pages, but a fresh build from the current consolidated source is ten pages
and retains one 4.43 pt overfull box. Page compression and the final anonymous
release regeneration remain pending.

The last verified release baseline is
release/relcompat3d_aaai27_openreview_20260720_084307/. It passed archive integrity,
inner checksums, anonymous path checks, JSON/compose validation, and extracted
source builds before the later manuscript consolidation.

## Claim Boundary

The evidence supports a scoped reliability layer for fixed predictions on one
shared 3DSSG target. It does not establish broad SOTA, dataset-level
generalization, calibrated physical-validity probabilities, or solved
support/contact relations.
