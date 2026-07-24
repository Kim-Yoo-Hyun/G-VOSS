# RelCompat3D Submission Result Summary

Last updated: 2026-07-23 KST

This summary covers the active `no_family_indicator_v1` method only. Exact
all-K values, paired intervals, controls, and audits are stored in the paths
listed by `manifest.json`.

## Evaluation Contract

- Predictors: VL-SAT, Open3DSG, and SGFN.
- Shared target: 157 3DSSG validation scans, 548 relation contexts, and 3,972
  exact-label ground-truth relations in support/contact, proximity, and
  vertical-order families.
- Metrics: exact-label Recall@K and verifier-derived Violation@K for
  `K={5,10,20,50,100}`.
- Proposed variants: RelCompat3D-Linear and RelCompat3D-MLP under the same
  family-aware re-ranking rule.

## Main K=50 Operating Points

All values are percentages.

| Predictor | Source R/V | Linear R/V | MLP R/V |
| --- | ---: | ---: | ---: |
| VL-SAT | 92.72 / 2.68 | 92.77 / 1.97 | 92.72 / 1.89 |
| Open3DSG | 40.43 / 13.87 | 44.18 / 3.42 | 46.70 / 4.13 |
| SGFN | 74.02 / 3.85 | 74.50 / 2.63 | 74.57 / 2.58 |

Across every reported predictor--K setting, both variants have Recall point
estimates no lower and Violation point estimates no higher than their source
ranking. This is a point-estimate statement; the paired scan-level intervals
are reported separately in the canonical evaluation artifacts and manuscript.

## Supporting Evidence

- Wrong-predicate, wrong-pair, shuffled-geometry, fixed-predicate swap,
  distance-only, and compatibility-only controls test the method factors for
  both compatibility estimators.
- Direct Linear removals show that the linked pairwise term has a small
  aggregate effect, while transformation averaging supplies exact
  endpoint/predicate consistency even when aggregate metrics change little.
- Point- and mesh-based measurements reproduce the direction of the reported
  changes under an alternative geometric construct; they are not an
  independent physical-validity ground truth.
- The compatibility models and split firewall exclude predictor identity,
  predictor score, and final-validation rows from fitting.
- The ReplicaSSG/FROSS result is a previously observed transfer stress test and
  does not establish dataset-level generalization.

## Claim Boundary

The evidence supports a scoped re-ranking result for fixed predictions on one
shared 3DSSG target. It does not claim broad 3D scene graph SOTA,
source-independent score calibration, solved support/contact compatibility, or
independent physical-validity annotation.
