# RelCompat3D Supplement Guide

Last updated: 2026-07-28 KST

## 1. Purpose

The technical supplement makes the main RelCompat3D claims auditable without
repeating the main narrative. It provides:

- complete method and optimization details;
- formal implementation guarantees;
- matched diagnostics and sensitivities;
- full uncertainty and family-level analyses;
- provenance and reproduction boundaries.

Reviewers are not required to read supplementary material. Therefore the
problem, method, main metrics, primary comparisons, central controls, and
limitations remain in the main paper.

## 2. Active Source and Build

- Wrapper: `aaai/supplement.tex`
- Content: `aaai/sec/supplement.tex`
- Canonical PDF: `aaai/supplement_aaai27.pdf`
- Canonical length: 10 pages
- Canonical SHA-256:
  `85104c2c66938e4c9f011c65ddae476d5c19599ff8d77bcf7957924d2a1b32c5`

## 3. Section Structure

### 3.1 Supplementary Method and Reproducibility Details

#### Notation

One table defines candidate identities, \(T_i,G_i,Z_i,a_i\), estimator index
\(q\), compatibility, transformed compatibility, and ranking utility.

#### Model and Preprocessing Details

- Open3DSG score and coverage handling;
- SGFN extraction;
- observed source-score ranges.

#### Compatibility Estimation and Family-Aware Re-Ranking

- transformation identities;
- family-sequence preservation;
- prefix utility property;
- counterfactual-negative construction;
- information-use boundary;
- Linear and MLP parameter and optimization details.

### 3.2 Additional Experiments

#### Experimental Setup

- Docker execution and runtime;
- development diagnostics;
- row-level regeneration check.

#### Results

- component and feature removals;
- seed robustness;
- point/mesh audit;
- qualitative pair analysis;
- counterfactual-policy sensitivity;
- score mapping and simple baseline;
- fusion and routing controls;
- Open3DSG coverage;
- candidate-pool oracle;
- paired intervals;
- transfer stress test;
- family composition;
- uncertainty sensitivity.

## 4. Table Inventory

| Table | Purpose | Priority |
| --- | --- | --- |
| Notation | Prevent symbol ambiguity | Essential |
| Source-score ranges | Verify nonnegative evaluated scores | High |
| Counterfactual construction | Reproduce training targets | Essential |
| Information-use boundary | Address construct dependence | Essential |
| Component removals | Test pairwise loss and averaging | Essential |
| Transformation diagnostics | Verify exact transformation behavior | High |
| Feature removals | Test dependence on geometry primitives | Essential |
| Full point/mesh audit | Extend main Table 3 to both variants and all \(K\) | Essential |
| Score mapping | Bound product-scale sensitivity | High |
| Robust-density baseline | Compare with a simple non-learned method | Essential |
| Matched MLP controls | Complete main Table 2 | Essential |
| Routing constraint | Test the family-aware design | Essential |
| Candidate oracle | Quantify fixed-pool ceiling | High |
| Paired intervals | Support main statistical statements | Essential |
| Transfer stress test | Show non-uniform transfer | Medium |
| Family slices | Explain composition and preserved support/contact | High |
| Uncertainty sensitivity | Test denominator policy | High |

No table uses manual bold in its caption. Paired-interval cells inherit
`\small` 9-point text.

## 5. Supplementary Figure

The pair--evidence--outcome figure contains:

1. proximity demotion;
2. vertical-order promotion;
3. support/contact source-order preservation.

Its role is qualitative scope illustration. It does not replace a systematic
independent annotation audit.

## 6. Key Evidence

### Component diagnostics

Both Linear and MLP are evaluated under:

- Full;
- no pairwise loss;
- no transformation averaging.

Linked-pair ordering and transformed-score errors explain why the components
are retained even when aggregate changes can be small.

### Seed robustness

Five seeds are fixed before training. The active model is not reselected from
those results.

### Score mapping

Five pre-specified smooth monotonic transformations are evaluated. Linear
retains the source-relative conclusion in all 75 predictor--\(K\) settings and
MLP in 74 of 75. Percentile stress is reported separately and is not described
as scale invariance.

### Simple baseline

Robust density is fit from training-positive geometry without evaluation
verifier labels. Hard-tail and Hard-drop remain separate non-deployable
direct-verifier diagnostics.

### Routing

The matched joint proximity/vertical queue changes results by estimator and
\(K\). Family-aware routing is interpreted as preserving composition rather
than maximizing aggregate performance.

### Point/mesh audit

Both estimators reduce or tie agreement-based Violation in all 15
predictor--\(K\) settings. The audit excludes OBB inputs and primary verifier
labels but shares scenes and ontology.

### Candidate oracle

Candidate-pool exact-label coverage is:

- VL-SAT: 99.72%;
- Open3DSG: 79.68%;
- SGFN: 99.72%.

The oracle quantifies candidate-generation ceilings and does not represent an
attainable comparator.

## 7. Reproducibility Boundary

The code/data package includes:

- RelCompat3D source;
- Dockerfile and Compose services;
- frozen protocols and model locks;
- compact metrics and summaries;
- row exporter and reproduction code;
- schema and expected manifests;
- LaTeX sources and figures.

It excludes:

- scans, meshes, RGB-D frames, and point clouds;
- stable scan/context/instance identifiers;
- source-derived row bundles;
- source-predictor repositories and checkpoints;
- large caches and raw logs.

This conservative boundary keeps dataset and third-party licenses under their
original providers.

## 8. Writing and Formatting Contract

- Use main-paper terminology without introducing new internal names.
- Keep each paragraph focused on one reviewer question.
- Report full numeric grids in tables or machine-readable artifacts rather
  than dense prose.
- Use `validation split` for the dataset partition.
- Use `validation scenes` for the evaluated scenes.
- `validation target` may describe the complete shared evaluation setting in
  a caption, but it must not imply a second dataset.
- Use roman captions without manually bolded lead phrases.
- Use at least 9-point table text.

## 9. Claim Boundary

The supplement strengthens, but does not broaden, the main claim. It does not
establish dataset-level generalization, independent geometric-validity ground
truth, support/contact correction, full graph generation, or universal fusion
optimality.

## 10. Final Verification

After the latest source rebuild:

1. confirm all 17 tables and the supplementary figure are referenced;
2. confirm undefined citations/references and overfull boxes are zero;
3. confirm US Letter, PDF 1.5, and embedded non-Type-3 fonts;
4. update canonical hash and release manifest;
5. rebuild the supplement from the extracted code/data ZIP.
