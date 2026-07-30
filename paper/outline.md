# RelCompat3D Paper Outline and Submission Snapshot

Last updated: 2026-07-29 KST

This document combines the manuscript outline with the current handoff
snapshot. Mutable task status belongs in the root `TODO.md`.

## 1. Paper Identity

- Title: **RelCompat3D: Re-Ranking 3D Scene Graph Relations with Geometric
  Evidence**
- Venue: AAAI-27 Main Technical Track
- Main source: `aaai/main.tex`
- Variants: RelCompat3D-Linear and RelCompat3D-MLP
- Task: post-hoc predicate--geometry compatibility estimation and
  family-aware re-ranking of fixed relation predictions

## 2. Core Question and Message

A high relation score does not necessarily measure whether the corresponding
ordered subject--object pair satisfies the predicate geometrically.
RelCompat3D estimates that compatibility from predicate semantics and
predicate-independent ordered-pair measurements, without the source score or
predictor identity. It combines compatibility with the source score only
during family-aware re-ranking.

The memorable message is that predicate--geometry compatibility can serve as a
predictor-agnostic reliability signal, while its interaction with source
relation scores remains predictor dependent.

## 3. Contributions

1. Define and measure the mismatch between source relation scores and
   ordered-pair geometric compatibility using exact-match Recall@\(K\) and
   verifier-derived Violation@\(K\).
2. Estimate source-score-excluded predicate--geometry compatibility and enforce
   exact consistency under applicable endpoint/predicate transformations.
3. Introduce family-aware re-ranking and characterize its predictor- and
   relation-family-dependent behavior across three fixed predictors.

Cross-predictor results, controls, and audits are evidence for these
contributions rather than additional contributions.

## 4. Main Manuscript

### Abstract

States the geometric mismatch, the post-hoc framework, estimator and
transformation design, ranking scope, three-predictor evaluation,
source-relative point-estimate result, controls, alternative audit, and scoped
predictor-agnostic conclusion.

### Introduction

Moves from downstream need to the observed failure, explains why semantic
similarity does not explicitly estimate ordered-pair compatibility, separates
\(T,G,Z\), introduces the estimators and constrained ranking, summarizes the
cross-predictor result, and ends with three contributions.

### Related Work

1. 3D Scene Graph Prediction
2. Geometry-aware Relation Evidence
3. Reliability Evaluation and Calibration

Each subsection distinguishes RelCompat3D from relation generation,
geometric-evidence methods, or probabilistic calibration.

### Method

1. Problem Formulation
2. Compatibility Estimation
3. Family-Aware Re-Ranking

Figure 2 follows the same input, compatibility, score-combination, and ranking
order.

### Experiments

- official 3DSSG validation split;
- 157 scans, 548 contexts, and 3,972 exact-match relations;
- Open3DSG, VL-SAT, and SGFN;
- \(K\in\{5,10,20,50,100\}\);
- exact-match Recall@\(K\) and verifier-derived Violation@\(K\);
- 1,000 paired scan-level bootstrap resamples.

Results use Table 1 and Figure 3 for the main trajectories, Table 2 for
counterfactual and structural controls, and Table 3 for the alternative
point/mesh audit. The text emphasizes that compatibility-only behavior differs
across predictors.

### Discussion and Limitations

Explains why compatibility can complement semantic or task-specific source
scores, then limits the evidence to one validation split, known instances,
reconstructed geometry, unchanged support/contact order, and an alternative
rather than independent audit.

### Conclusion

Restates the scoped source-relative result and the predictor-dependent role of
source relation scores. It closes on predicate--geometry compatibility as a
predictor-agnostic reliability signal.

## 5. Figures and Tables

| Item | Role |
| --- | --- |
| Figure 1 | Vertical-order failure and demotion |
| Figure 2 | Compatibility and family-aware re-ranking flow with proximity demotion |
| Figure 3 | Predictor-specific Recall--Violation trajectories |
| Table 1 | Main comparisons over all five \(K\) values |
| Table 2 | Ablations and counterfactual controls |
| Table 3 | Point/mesh alternative consistency audit |

All items are referenced in the main text. Detailed visual values and caption
contracts are in `figures.md`.

## 6. Current Evidence Snapshot

- At every reported predictor--\(K\) setting, both variants have Recall point
  estimates no lower and Violation point estimates no higher than Source.
- At \(K=50\), paired intervals are favorable for Recall and Violation on
  Open3DSG and SGFN. VL-SAT lowers Violation without a detectable Recall loss.
- Compatibility-only ordering stays close to the full Linear estimator on
  Open3DSG but loses substantial Recall on VL-SAT and SGFN.
- The point/mesh audit supports the direction of the Violation changes under
  alternative geometric measurements.
- Supplementary controls bound score scaling, routing, component, seed,
  candidate-pool, and construct-dependence risks.

This is a shared-scene reliability result, not a dataset-generalization or SOTA
claim.

## 7. Supplement and Reproducibility Contract

The supplement owns complete target rules, proofs, optimization details,
sensitivities, matched controls, intervals, family slices, oracles, transfer
stress tests, and the row-level regeneration check. The checklist records only
the official status answers. Detailed answer rationales and the public release
boundary are in `reproducibility.md`.

## 8. Build and Upload Boundary

The only official main entry point is `aaai/main.tex`; legacy teaser wrappers
are not part of the submission. Canonical PDFs are:

- `aaai/main_aaai27.pdf`;
- `aaai/supplement_aaai27.pdf`;
- `aaai/reproducibility_checklist_aaai27.pdf`.

Current page counts and hashes are recorded after each clean build in
`paper/README.md` and `reproducibility.md`. The code/data archive excludes
licensed raw data, stable source identifiers, source-derived row bundles, and
third-party checkpoints.
