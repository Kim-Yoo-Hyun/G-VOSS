# RelCompat3D / H001 Figure Source Lock

Last updated: 2026-07-14 KST

Status: `camera_ready_vector_three_figure_revision_passed`

This file owns the paper-facing claims, source artifacts, and non-claims for
Figures 1--3. Generated assets live under `paper/generated/figures/`; metric
and case provenance stays in `experiments/H001_geom_reliability/`.

## Global Contract

- Figures support a factor-isolated reliability layer for geometry-identifiable
  3D Scene Graph relations, not broad generation SOTA.
- Use paper-facing names only: source confidence, predicate--geometry
  compatibility, relation-algebra-constrained product, rank-average fusion,
  verifier-derived violation, and uncertain geometry.
- Report Recall and Violation together. Lower Violation and higher Recall are
  better.
- K=100 is the primary endpoint. K=`{5,10,20,50}` are all shown and labeled
  without additional protocol roles; K=1 is not a paper endpoint.
- Qwen-VL and ReplicaSSG/FROSS do not appear in the three main figures.

## Figure 1: Failure to Framework

Locked claim:

> Semantically confident relation predictions can be geometrically
> inconsistent because source confidence does not measure predicate-conditioned
> physical compatibility; RelCompat3D isolates those factors before re-ranking.

Locked visual form:

- Three left-to-right panels:
  1. the actual ordered-pair point clouds for a high-confidence relation that
     conflicts with pair distance;
  2. predicate semantics `T` and same-pair geometry `G` entering compatibility,
     while source score `Z` bypasses that module and enters only the product;
  3. the observed rank movement, identity preservation, and joint
     Recall--Violation evaluation.
- The displayed failure is the traceable Open3DSG heater--trash-can `close by`
  case used by Figure 3: source confidence `0.853`, source rank `19`,
  compatibility `0.0027`, and product rank `304`.
- `Z` is visibly excluded from `C(T,G)` and used only at final fusion.
- The identity panel states that scan, subject, object, and predicate remain
  unchanged, communicating an instance-level join rather than a category
  shortcut.
- No reviewer checklist, claim-boundary band, learned point encoder, energy
  model, evidence router, or abstention head appears.
- `relative_size` does not appear in Figure 1. It is a secondary scope
  extension whose fixed point-rule baseline matches the learned score, not core
  learned-method evidence.

Assets:

- `paper/generated/figures/figure1_framework.svg`
- `paper/generated/figures/figure1_framework.pdf`
- `paper/generated/figures/figure1_framework.png`
- `paper/scripts/render_figure3_geometry_panels.py`
- current SVG SHA-256:
  `ae144d81d343ee26d4f3677da3f3ddd34e4f2df2f4366ae123367e3b4c4ecefd`;
- current PDF SHA-256:
  `23000b2d24900c726d0f75b2703da1bfa235a012775be4412973af282610fbfc`;
- current PNG SHA-256:
  `071c2f066309a854d470c40792a160e0adf8b9ecce48a102db869494db48d4ee`.

Caption constraint: call RelCompat3D a predictor-agnostic,
relation-algebra-constrained compatibility and re-ranking framework, not a
verifier script or a universally optimal fusion formula. The caption should connect the displayed rank
change to pair-grounded compatibility without implying that one corrected case
establishes aggregate performance.

## Figure 2: Operating-Budget Trajectories

Locked claim:

> The relation-algebra-constrained product improves the aggregate K=100
> Recall--Violation point on all three predictors and shows
> predictor-dependent trade-offs at smaller budgets.

Locked visual form:

- Three source panels: VL-SAT, Open3DSG, and SGFN.
- Connect K=`{5,10,20,50,100}` for source confidence and the structured
  product; label each point by K.
- A neutral outline marks K=100; every K is labeled directly.
- Separate panel axes because source recall denominators and candidate
  distributions differ.
- Do not claim every source improves Recall at every K; VL-SAT has small
  low-K Recall decreases.

Sources:

- `experiments/H001_geom_reliability/structured_main_v1/evaluation/summary.json`
- `paper/generated/figures/figure2_data.json`

Assets:

- `paper/generated/figures/figure2_tradeoff.svg`
- `paper/generated/figures/figure2_tradeoff.pdf`
- `paper/generated/figures/figure2_tradeoff.png`
- SVG SHA-256: `c5131edf5790efaef849e4d78bd6f574a5dd48bb579834581e2a33c395e1dc42`
- PDF SHA-256: `f3e9860dab3714d6d4c8fe95a1dc891701d5ecdd68ec5053dd110c6577857f43`
- PNG SHA-256: `6c5514a3c773386253f80fac4bae2ab4360f5921e8c084dde52df33817200612`

## Figure 3: Corrections and Residual Failure

Locked claim:

> Identity-aligned geometry can demote physically inconsistent semantic
> predictions, but engineered evidence remains incomplete and can also promote
> a residual violation.

Locked cases:

| panel | case | role | relation | source rank -> product rank | source / compatibility |
| --- | --- | --- | --- | ---: | ---: |
| A | `open3dsg_case_001` | corrected proximity error | heater `close by` trash can | 19 -> 304 | 0.853 / 0.0027 |
| B | `open3dsg_case_010` | corrected support/contact error | lamp `lying on` side table | 39 -> 337 | 0.843 / 0.050 |
| C | `open3dsg_case_026` | residual top-10 failure | door `lying on` floor | 21 -> 10 | 0.843 / 0.998 |

Locked visual form:

- Three large pair-geometry point-cloud panels: two successful corrections and
  one residual failure.
- Each panel exposes subject/object, predicate, source confidence,
  compatibility, and rank movement.
- This is traceable qualitative mechanism evidence, not a representative human
  audit.

Sources and assets:

- `experiments/H001_geom_reliability/sources/open3dsg/failure_cases/inspection.json`
- `experiments/H001_geom_reliability/sources/open3dsg/failure_rows/report.md`
- `local_dataset/Open3DSG_staged/h001_full_validation_runtime/output/datasets/OpenSG_3RScan/preprocessed/`
- `paper/scripts/render_figure3_geometry_panels.py`
- `paper/generated/figures/figure3_geometry_panels.svg`
- `paper/generated/figures/figure3_geometry_panels.pdf`
- `paper/generated/figures/figure3_geometry_panels.png`
- `paper/generated/figures/figure3_geometry_cases.json`
- `paper/generated/figures/figure3_geometry_manifest.json`
- SVG SHA-256: `e1cdd18b3bf43d16e4b69cb00dadd9484d9e1bb1edf93ba06e4a3da8f59079f0`
- PDF SHA-256: `e8427310c9d37211bb0eabc28591783b77288876b02ea22b89039ce2e6144a87`
- PNG SHA-256: `652851646044607265e2aea8aad23a57dd9d51b961327a2e4f1a054c6b1e1360`

## Validation

- `paper/generated/figures/validation.json`: `passed`
- Figure 1 contains no unimplemented component or review-artifact band.
- Figure 1 was visually inspected both at native resolution and on page 2 of
  the rebuilt 8-page main PDF; panel labels, rank movement, leakage boundary,
  and metric directions remain legible at the manuscript width.
- Figure 2 metric extraction and all K labels pass source-lock validation.
- Figure 3 uses the three locked IDs and the same geometry rows as its manifest.
- SVG assets parse; vector PDF conversions are included in the current AAAI
  manuscript. PNG files are previews only.
