# RelCompat3D Appendix and Supplement Map

Last updated: 2026-07-28 KST

This document records what the final technical supplement contributes beyond
the self-contained main paper. The active source is
`aaai/sec/supplement.tex`. Historical experiments and proposed extensions are
not part of the submission appendix.

## 1. Role

The supplement supports four reviewer-facing needs:

1. define notation, preprocessing, target construction, and optimization in
   enough detail to reproduce RelCompat3D;
2. verify the exact transformation and family-preservation properties used by
   the method;
3. provide full controls, sensitivities, confidence intervals, and
   family-specific analyses that do not fit in the main paper;
4. state the boundary between compact public artifacts and licensed external
   inputs.

The supplement does not broaden the paper into a dataset-generalization, SOTA,
or independent physical-validity claim.

## 2. Final Structure

### Supplementary Method and Reproducibility Details

- notation table for \(T_i,G_i,Z_i,a_i,C_i^q,C_i^{\rm tr,q},u_i^q\);
- Open3DSG and SGFN preprocessing details;
- observed source-score ranges;
- transformation guarantees and family-sequence preservation;
- counterfactual-negative construction;
- information-use boundary;
- Linear and MLP architecture, parameter, optimizer, and row-count details.

### Additional Experiments

- implementation and development diagnostics;
- row-level regeneration check;
- component and feature removals;
- training-seed robustness;
- full point- and mesh-based audit;
- qualitative pair analysis;
- counterfactual-policy sensitivity;
- score-mapping, simple-baseline, fusion, and routing controls;
- candidate-pool Recall oracles;
- paired scan-level intervals;
- ReplicaSSG/FROSS transfer stress test;
- family composition and verifier-uncertainty sensitivity.

## 3. Final Tables

| Table role | What it establishes |
| --- | --- |
| Notation | One authoritative definition for the symbols used in main and supplement |
| Source-score ranges | The evaluated scores are nonnegative and product scoring preserves sign |
| Counterfactual construction | Family-specific positive and negative rules |
| Information-use boundary | Training construction, primary verifier, and point/mesh audit do not share labels |
| Component removals | Effect of removing pairwise loss or transformation averaging |
| Transformation diagnostics | Mean, P95, and maximum transformed-score error |
| Feature removal | Dependence on exact and related geometric primitives |
| Full point/mesh audit | Both variants over all five \(K\) values |
| Score mapping | Sensitivity to pre-specified monotonic score transformations |
| Robust-density baseline | Comparison with a simple non-learned compatibility estimator |
| Matched MLP controls | Nonlinear counterparts of the main Linear controls |
| Routing constraints | Effect of changing proximity/vertical competition |
| Candidate oracle | Fixed-pool coverage and recoverable Recall ceiling |
| Paired intervals | Scan-level uncertainty for the main changes |
| Transfer stress test | Behavior under ReplicaSSG/FROSS ontology and geometry shifts |
| Family slices | Selected top-100 composition and family-specific metrics |
| Uncertainty sensitivity | Primary and alternative verifier-denominator policies |

## 4. Supplementary Figure

The supplementary qualitative figure is a three-family
pair--evidence--outcome panel:

- proximity demotion;
- vertical-order promotion;
- support/contact source-order preservation.

It illustrates the scope of the ranking rule. It is not a systematic blinded
validity study.

## 5. Provenance and Public Boundary

The anonymous code/data archive contains Docker configuration, RelCompat3D
source, frozen protocols and model locks, compact metrics, manifests, and
paper sources. It excludes raw 3RScan/3DSSG data, scans, meshes, RGB-D frames,
third-party checkpoints, stable source identifiers, and source-derived row
bundles.

The row exporter, schema, deterministic join, and expected manifests remain
available for licensed users. This is the conservative release boundary used
by the final submission.

## 6. Claim Boundary

The appendix may support:

- robustness of the main source-relative point-estimate conclusion;
- necessity and behavior of the method components;
- reproducibility of the reported tables and figure data;
- fixed-candidate and family-routing limitations.

It must not be cited as evidence of:

- dataset-level generalization;
- independently annotated physical validity;
- universal superiority of family-aware routing;
- correction of support/contact relations;
- generation of missing relation candidates.

## 7. Current Artifact State

- Technical supplement: `aaai/supplement_aaai27.pdf`, 10 pages.
- Canonical SHA-256:
  `85104c2c66938e4c9f011c65ddae476d5c19599ff8d77bcf7957924d2a1b32c5`.
- The PDF is synchronized with the final 2026-07-28 source and release.
