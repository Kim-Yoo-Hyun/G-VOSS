# RelCompat3D Experiment Guide

Last updated: 2026-07-29 KST

This document summarizes the final experiment contract. Exact executable
protocols and compact results live under
`experiments/RelCompat3D_geom_reliability/`.

## 1. Evaluation Question

RelCompat3D tests whether fixed 3D scene graph relation predictions can be
re-ranked using same-pair predicate--geometry compatibility while preserving
exact-match retrieval.

The experiment separates three quantities:

- predicate and family semantics \(T_i,a_i\);
- predicate-independent measurements \(G_i\) of the ordered subject--object
  pair;
- source relation score \(Z_i\).

Compatibility is estimated without \(Z_i\) or predictor identity. It is
combined with \(Z_i\) only during re-ranking.

## 2. Data and Split Contract

The final main evaluation uses the official 3DSSG validation split over
3RScan scenes:

- 157 evaluation scans;
- 548 relation contexts;
- 3,972 exact-match ground-truth relations;
- support/contact, proximity, and vertical-order families.

Training uses 1,061 scans. Model and family choices use the 117-scan
development split. Evaluation-split ground truth is used only for Recall and
never to construct targets, fit compatibility, or rank candidates.

Terminology:

- **validation split** refers to the dataset partition;
- **validation scenes** refers to the evaluated reconstructed scenes;
- **shared evaluation setting** means that all three predictors use the same
  split, contexts, relation scope, metrics, and \(K\) values.

## 3. Prediction Sources

| Predictor | Role | Source score |
| --- | --- | --- |
| Open3DSG | Open-vocabulary relation source | Cosine similarity between normalized text embeddings |
| VL-SAT | Closed-set relation source | Sigmoid relation score |
| SGFN | Released SceneGraphFusion benchmark model | Sigmoid relation score |

The fitted RelCompat3D parameters are applied to all three predictors without
predictor-specific refitting.

## 4. Relation Scope

- Evaluated families:
  support/contact, proximity, vertical order.
- Re-ranked families:
  proximity and vertical order.
- Preserved family:
  support/contact remains in source order.
- Excluded relations:
  candidates outside the three evaluated families.

Family-aware re-ranking preserves the source sequence of relation-family
labels. A candidate competes only with candidates in the same re-ranked
family.

## 5. Main Comparison Conditions

### Table 1

- Source;
- RelCompat3D-Linear;
- RelCompat3D-MLP;
- RankAvg;
- RRF;
- Product (all families), reported as a scope comparison because it also
  re-ranks support/contact.

Bold values are selected only among comparable methods that preserve both the
source family sequence and support/contact order.

### Table 2

The main table reports:

- both complete RelCompat3D variants;
- wrong predicate;
- wrong ordered pair;
- shuffled geometry;
- endpoint swap with fixed predicate;
- distance-only ordering;
- compatibility-only ordering.

Control rows are shown for Linear. Matched MLP controls are in the supplement.

### Table 3

The point- and mesh-based consistency audit reports \(K=50\) results for
RelCompat3D-Linear. A satisfied or violated label requires agreement between
the point-cloud and mesh-based measurements. Disagreement is uncertain.

## 6. Metrics

### Exact-match Recall@\(K\)

\[
\operatorname{Recall@K}
=
\frac{\sum_c |L_K(c)\cap Y_c|}
{\sum_c |Y_c|}.
\]

Candidate and ground-truth identities use the exact ordered triple
\((s_i,p_i,o_i)\) within a context. Family mapping is never used for label
matching.

### Verifier-derived Violation@\(K\)

\[
\operatorname{Violation@K}
=
\frac{N_v}{N_s+N_u+N_v}.
\]

The primary geometry verifier returns satisfied, uncertain, or violated.
Uncertain rows enter the denominator but not the numerator.

The supplement additionally reports measured and decidable coverage,
decidable-only Violation, uncertain-as-violated Violation, and family-specific
results.

## 7. Evaluation Grid and Statistics

- \(K\in\{5,10,20,50,100\}\);
- one fixed fit for each reported condition;
- 1,000 paired scan-level bootstrap resamples;
- all contexts from a sampled scan remain grouped;
- the same resamples are used across compared conditions.

Point-estimate claims and interval claims are kept separate. The main
all-\(K\) statement is a point-estimate statement.

## 8. Final Main Results

For every predictor and reported \(K\), both RelCompat3D variants have:

- Recall point estimates no lower than Source;
- Violation point estimates no higher than Source.

At \(K=50\), paired intervals favor both metrics for Open3DSG and SGFN. For
VL-SAT, the Recall interval contains zero while the Violation interval remains
negative. Open3DSG shows the largest changes.

The controls reveal predictor-dependent use of the source relation score.
Compatibility-only ordering remains close to RelCompat3D-Linear on Open3DSG
but loses substantial Recall on VL-SAT and SGFN.

The result is not framed as universal method dominance:

- Linear and MLP occupy different Recall--Violation operating points;
- RankAvg and RRF can obtain lower Violation at some \(K\) values while losing
  more low-\(K\) Recall;
- Product (all families) changes support/contact selections.

## 9. Additional Defenses in the Supplement

- five pre-specified monotonic source-score mappings;
- simple robust-density compatibility baseline;
- direct-verifier diagnostics separated from deployable baselines;
- matched family-routing controls;
- pairwise-loss and transformation-averaging removal;
- five-seed fitting robustness;
- exact/related/alternative feature removal;
- full Linear and MLP point/mesh audit;
- fixed-candidate Recall oracles;
- row-level regeneration of Tables 1--3 and Figure 3 data;
- ReplicaSSG/FROSS transfer stress test.

## 10. Claim Boundary

The experiments support a scoped reliability claim across three fixed
predictors evaluated on the same 3DSSG validation split. They do not establish:

- dataset-level generalization;
- independent physical-validity ground truth;
- generation of missing relations;
- support/contact correction;
- a universally optimal fusion or routing rule.

## 11. Canonical Artifacts

- Main PDF: `aaai/main_aaai27.pdf`, 9 pages.
- Supplement PDF: `aaai/supplement_aaai27.pdf`, 12 pages.
- Checklist PDF: `aaai/reproducibility_checklist_aaai27.pdf`, 2 pages.
- Current release:
  `../release/relcompat3d_aaai27_openreview_20260729_223000/`.

The canonical paths above are regenerated after every change to the main,
supplement, or checklist source.
