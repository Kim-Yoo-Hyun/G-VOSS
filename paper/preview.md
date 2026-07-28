# RelCompat3D Current Paper Preview

Last updated: 2026-07-28 KST

## Current Identity

- Title: **RelCompat3D: Re-Ranking 3D Scene Graph Relations with Geometric
  Evidence**
- Venue: AAAI-27 Main Technical Track
- Main source: `aaai/main.tex`
- Main method: source-score-excluded predicate--geometry compatibility followed
  by family-aware re-ranking
- Variants: RelCompat3D-Linear and RelCompat3D-MLP

## Current Claim

Across Open3DSG, VL-SAT, and SGFN evaluated on the same 3DSSG validation split,
both RelCompat3D variants have Recall point estimates no lower and
verifier-derived Violation point estimates no higher than Source at every
reported \(K\). This is a scoped, shared-scene reliability result rather than
a dataset-generalization or SOTA claim.

## Main Story

1. Figure 1 shows a high-ranked vertical predicate contradicted by the
   reconstructed ordered-pair geometry.
2. RelCompat3D separates predicate semantics, ordered-pair measurements, and
   source relation score.
3. Linear and nonlinear estimators learn compatibility from ground-truth
   positives and constructed counterfactuals.
4. Transformation averaging enforces the applicable endpoint/predicate
   identities.
5. Compatibility is combined with source score only during constrained
   re-ranking.
6. Recall, Violation, controls, and point/mesh audit characterize the result.

## Main Evidence

- 157 validation scans;
- 548 relation contexts;
- 3,972 exact-match ground-truth relations;
- \(K=5,10,20,50,100\);
- 1,000 paired scan-bootstrap resamples;
- three fixed predictors;
- two compatibility estimators.

At \(K=50\), the paired intervals support favorable Recall and Violation
changes for Open3DSG and SGFN. VL-SAT has lower Violation without a detectable
Recall loss. Open3DSG shows the largest changes.

## Figures and Tables

- Figure 1: desk/ceiling vertical-order demotion, rank 6 to 425.
- Figure 2: heater/trash-can proximity demotion at \(4.33\,\mathrm{m}\), rank
  19 to 178.
- Figure 3: three predictor-specific Recall--Violation trajectories.
- Table 1: Source, both variants, RankAvg, RRF, and Product (all families).
- Table 2: structural controls.
- Table 3: point- and mesh-based consistency audit.

## Supplement

The 10-page technical supplement contains complete construction and
optimization details, formal guarantees, sensitivities, controls, paired
intervals, family slices, transfer results, qualitative panels, and
reproduction checks.

## Reproducibility

The 2-page official checklist uses:

- `yes` for method outline, metrics, seeds, runs, intervals, infrastructure,
  and final settings;
- `partial` for unrestricted data availability, exhaustive development search,
  complete third-party experiment code, public release license/URL, and inline
  implementation comments;
- `NA` only for novel-dataset questions;
- blank theory subquestions after the parent answer `no`.

The conservative code/data archive excludes licensed raw data, stable source
identifiers, source-derived row bundles, and third-party checkpoints.

## Claim Limits

- one 3DSSG validation split;
- known object instances;
- reconstructed geometry required;
- no support/contact re-ranking;
- no independent validity labels;
- fixed candidate pools;
- no universal routing or fusion claim.

## Build State

The synchronized canonical files are:

- main: 9 pages;
- supplement: 10 pages;
- checklist: 2 pages.

They include the latest wording in Introduction, Discussion, and Conclusion.
The release at
`../release/relcompat3d_aaai27_openreview_20260728_214915/` contains the same
sources and PDFs.
