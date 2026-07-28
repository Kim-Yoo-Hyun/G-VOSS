# RelCompat3D Paper Outline

Last updated: 2026-07-28 KST

## 1. Paper Identity

- Title: **RelCompat3D: Re-Ranking 3D Scene Graph Relations with Geometric
  Evidence**
- Venue: AAAI-27 Main Technical Track
- Main source: `aaai/main.tex`
- Method variants: RelCompat3D-Linear and RelCompat3D-MLP
- Task: post-hoc predicate--geometry compatibility estimation and
  family-aware re-ranking of fixed relation predictions

## 2. Core Story

1. A high relation score does not necessarily measure whether the corresponding
   ordered pair satisfies the predicate geometrically.
2. RelCompat3D estimates compatibility from predicate semantics and same-pair
   geometry without using source score or predictor identity.
3. Transformation averaging gives equal compatibility to equivalent
   endpoint/predicate representations.
4. Compatibility and source score are combined only during family-aware
   re-ranking.
5. Exact-match Recall and verifier-derived Violation jointly measure retrieval
   and geometric reliability.

## 3. Contributions

1. Define and measure the mismatch between relation score and instance-level
   geometric compatibility.
2. Learn source-score-excluded compatibility with ordered-pair identity and
   relation-preserving transformations.
3. Introduce family-aware re-ranking and characterize it across three fixed
   predictors.

The contributions are method and evaluation contributions. Cross-predictor
results, controls, and audits are evidence rather than extra contributions.

## 4. Main Manuscript

### Abstract

Problem, post-hoc method, training and transformation design, ranking scope,
three-predictor evaluation, point-estimate result, controls, alternative audit,
and scoped conclusion.

### Introduction

- downstream need for geometrically supported relations;
- motivating vertical-order failure in Figure 1;
- distinction between geometry-aware generation and explicit same-pair
  compatibility;
- \(T,G,Z\) separation;
- two estimators, counterfactual training, transformations;
- family-aware ranking and support/contact preservation;
- evaluation on the official 3DSSG validation split;
- three concise contributions.

Selected wording:

- use `official 3DSSG validation split` for the partition;
- use `shared 3DSSG validation scenes` for the evaluated scenes.

### Related Work

1. 3D Scene Graph Prediction
2. Geometry-aware Relation Evidence
3. Reliability Evaluation and Calibration

Each subsection ends by locating RelCompat3D relative to generation,
geometric evidence, or probabilistic reliability.

### Method

1. Problem Formulation
2. Compatibility Estimation
3. Family-Aware Re-Ranking

Figure 2 follows the same order.

### Experiments

#### Experimental Setup

- official 3DSSG validation split;
- 157 scans, 548 contexts, 3,972 relations;
- Open3DSG, VL-SAT, SGFN;
- exact-match Recall@\(K\);
- verifier-derived Violation@\(K\);
- \(K\in\{5,10,20,50,100\}\);
- 1,000 paired scan bootstrap resamples.

#### Recall--Violation Results

- Table 1 and Figure 3;
- all-\(K\) source-relative point-estimate claim;
- \(K=50\) paired interval claim;
- fusion and scope trade-offs;
- score-mapping, simple-baseline, and routing summary;
- three qualitative rank changes.

#### Ablations and Controls

- Table 2;
- dependence on predicate, correct pair, geometry, transformation, and source
  score.

#### Point- and Mesh-Based Consistency Audit

- Table 3;
- OBB-free alternative measurement;
- not independent ground truth.

### Discussion and Limitations

- same 3DSSG validation split, not dataset-level generalization;
- known instances and reconstructed geometry;
- support/contact remains in source order;
- alternative audit uses the same scenes and ontology;
- broader claims require independent labels, richer contact/pose evidence,
  and additional datasets.

### Conclusion

Return to the motivating failure and summarize the scoped result over the
shared 3DSSG validation scenes. No citation is needed because 3DSSG has already
been defined and cited earlier.

## 5. Main Figures and Tables

| Item | Role |
| --- | --- |
| Figure 1 | Vertical-order failure and demotion |
| Figure 2 | Compatibility and re-ranking flow plus proximity demotion |
| Figure 3 | Recall--Violation trajectories |
| Table 1 | Main comparisons over all five \(K\) values |
| Table 2 | Ablations and counterfactual controls |
| Table 3 | Point/mesh alternative audit |

All six items are referenced in the main text and occur within the seven
technical pages in the last clean build.

## 6. Supplement Contract

The supplement owns complete rules, proofs, optimization, sensitivities,
matched controls, intervals, family slices, oracles, transfer stress test, and
reproducibility details. Critical method definitions and main evidence remain
in the main paper.

## 7. Current Build Boundary

The synchronized final build is 9/10/2 pages for main, supplement, and
checklist. Main technical content and all main figures/tables remain within
pages 1--7. The current release is
`../release/relcompat3d_aaai27_openreview_20260728_214915/`.
