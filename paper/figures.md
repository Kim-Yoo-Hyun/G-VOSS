# RelCompat3D Figure Guide

Last updated: 2026-07-28 KST

This file records the intent, fixed values, and claim boundary of every figure
in the final main paper and technical supplement.

## 1. Common Visual Contract

- Orange marks the subject instance.
- Blue marks the object instance.
- Relation text is shown in quotation marks in captions and prose.
- Main figures use the outlined-v15 PDF assets to avoid font-substitution
  warnings.
- Qualitative ranks are candidate ranks in the corresponding source context.
- A rank change illustrates re-ranking, not correction of the underlying scene
  graph generator.

Active assets:

- `reference_AAAI/figure/Figure1.pdf`;
- `reference_AAAI/figure/Figure2.pdf`;
- `reference_AAAI/figure/Figure3.pdf`;
- `aaai/supplement_figures/qualitative_geometry_panels.png`.

## 2. Figure 1: High-Scoring Geometric Failure

### Purpose

Figure 1 motivates the paper with a vertical-order candidate that is
semantically readable but inconsistent with the reconstructed ordered-pair
geometry.

### Fixed case

- Predictor: Open3DSG.
- Candidate: “desk higher than ceiling”.
- Source rank: 6.
- RelCompat3D-Linear rank: 425.
- Top-\(50\) membership: in to out.

The point-cloud view places the desk below the ceiling. The figure demonstrates
the failure mode and one qualitative outcome. It does not establish aggregate
performance.

### Final caption contract

The caption identifies the source predictor, ordered pair, contradiction,
before/after ranks, and top-\(50\) consequence. The relation phrase remains in
plain quotation marks rather than `\texttt`.

## 3. Figure 2: Compatibility and Re-Ranking Overview

### Purpose

Figure 2 explains the complete inference flow and provides a proximity
demotion example.

### Panel (a)

- Ordered pair: heater \(\rightarrow\) close by \(\rightarrow\) trash can.
- Heater instance: 14.
- Trash-can instance: 24.
- XY center distance: \(4.33\,\mathrm{m}\).

### Panel (b)

The diagram separates:

1. predicate semantics \(T\);
2. ordered-pair measurements \(G\);
3. source relation score \(Z\).

Only \(T\) and \(G\) enter predicate--geometry compatibility. \(Z\) bypasses
the estimator and is combined with compatibility in the within-family score.
Family-aware re-ranking then preserves the source family sequence.

### Fixed outcome

- Source rank: 19.
- RelCompat3D-Linear rank: 178.

The asset, caption, Method description, and Results prose agree on the distance,
variant, and ranks.

## 4. Figure 3: Recall--Violation Trajectories

### Purpose

Figure 3 visualizes the two reported metrics jointly over all five rank
cutoffs. Rightward movement increases Recall and downward movement decreases
Violation.

### Methods

- Source;
- RelCompat3D-Linear;
- RelCompat3D-MLP.

### Fixed coordinates

Each pair is \((\text{Recall},\text{Violation})\) in percent for
\(K=5,10,20,50,100\).

#### VL-SAT

| \(K\) | Source | Linear | MLP |
| ---: | --- | --- | --- |
| 5 | (41.94, 0.29) | (42.07, 0.15) | (42.09, 0.15) |
| 10 | (63.22, 0.82) | (63.39, 0.57) | (63.47, 0.51) |
| 20 | (80.74, 1.42) | (80.82, 1.14) | (80.92, 1.09) |
| 50 | (92.72, 2.68) | (92.77, 1.97) | (92.72, 1.89) |
| 100 | (96.35, 4.76) | (96.58, 2.95) | (96.50, 2.96) |

#### Open3DSG

| \(K\) | Source | Linear | MLP |
| ---: | --- | --- | --- |
| 5 | (3.42, 52.05) | (3.73, 0.94) | (3.70, 4.95) |
| 10 | (9.87, 32.89) | (11.38, 2.33) | (11.78, 4.97) |
| 20 | (19.89, 20.99) | (23.62, 3.13) | (24.67, 4.56) |
| 50 | (40.43, 13.87) | (44.18, 3.42) | (46.70, 4.13) |
| 100 | (51.11, 12.42) | (56.85, 3.24) | (59.89, 3.71) |

#### SGFN

| \(K\) | Source | Linear | MLP |
| ---: | --- | --- | --- |
| 5 | (31.17, 2.37) | (31.17, 2.37) | (31.17, 2.37) |
| 10 | (39.75, 3.49) | (39.75, 3.47) | (39.75, 3.47) |
| 20 | (49.12, 3.22) | (49.14, 2.97) | (49.19, 2.96) |
| 50 | (74.02, 3.85) | (74.50, 2.63) | (74.57, 2.58) |
| 100 | (92.35, 6.30) | (93.03, 3.50) | (92.88, 3.50) |

Axis ranges differ by predictor and the caption states this explicitly.

## 5. Supplementary Qualitative Figure

### Purpose

The three-panel figure connects pair geometry, verifier evidence, and ranking
outcome across the three evaluated families.

### Panels

| Panel | Family | Outcome |
| --- | --- | --- |
| (a) | Proximity | A geometrically inconsistent candidate is demoted |
| (b) | Vertical order | An exact-match, verifier-satisfied candidate is promoted |
| (c) | Support/contact | Source order is retained because richer contact evidence is outside the re-ranking scope |

The promotion case reports “desk close by chair” moving from rank 81 to 30 in
the same Open3DSG context as Figure 1.

## 6. Verification

Before upload:

1. include only the outlined-v15 main assets;
2. confirm Figure 1--3 and Table 1--3 occur within the seven technical pages;
3. confirm no Type 3, CID/Identity, or unembedded fonts;
4. compare Figure 3 coordinates against Table 1;
5. rebuild the canonical PDFs after any source wording change.

The final canonical build and extracted-release rebuild pass these checks.
