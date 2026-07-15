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
- K=`{5,10,20,50,100}` are all shown and labeled. K=50 is outlined as the
  representative mid-budget operating point; K=5 and K=100 remain visible
  boundary conditions. K=1 is not a paper endpoint.
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

> The relation-algebra-constrained route improves the representative mid-budget K=50
> Recall--Violation trade-off across three predictors and shows the full
> budget-dependent trajectory without suppressing boundary conditions.

Locked visual form:

- Three source panels: VL-SAT, Open3DSG, and SGFN.
- Connect K=`{5,10,20,50,100}` for source confidence and the structured
  product; label each point by K.
- A neutral outline marks K=50; every K is labeled directly.
- Separate panel axes because source recall denominators and candidate
  distributions differ.
- Do not claim statistical Recall improvement for every source at every K;
  some low-/mid-budget Recall intervals include zero even when point estimates
  are preserved or improved.

Sources:

- `experiments/H001_geom_reliability/structured_main_v1/evaluation/summary.json`
- `paper/generated/figures/figure2_data.json`

Assets:

- `paper/generated/figures/figure2_tradeoff.svg`
- `paper/generated/figures/figure2_tradeoff.pdf`
- `paper/generated/figures/figure2_tradeoff.png`
- SVG SHA-256: `24779d23cc7403232c90d2780a89151328bbad000b8101ea7f053bf18fe267ac`
- PDF SHA-256: `8127240ec4638d22103a6d118f72f40945c08d7e3e396b33a329c35ae7a8912e`
- PNG SHA-256: `bd968dfc3bc11b185b573d88bae447a9efa59f95c1faf83050ed687decda9961`

## Figure 3: Corrections and Residual Failure

Locked claim:

> Identity-aligned geometry can demote proximity and relative-vertical
> predictions contradicted by the same-pair geometry, while the declared
> applicability boundary leaves a residual support/contact violation unchanged.

Locked cases:

| panel | case | role | relation | source -> routed rank | unrestricted rank | source / compatibility |
| --- | --- | --- | --- | ---: | ---: | ---: |
| A | `open3dsg_case_001` | proximity correction | heater `close by` trash can | 19 -> 178 | 304 | 0.853 / 0.0027 |
| B | `open3dsg_case_019` | relative-vertical correction | floor `higher than` curtain | 1 -> 430 | 431 | 0.871 / 0.000003 |
| C | `open3dsg_case_026` | residual support/contact violation | door `lying on` floor | 21 -> 21 | 10 | 0.843 / 0.998 |

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
- SVG SHA-256: `151d22fa21031f3d822f006723ab85c85e680c1024c0c63f1ede1f6487aec93d`
- PDF SHA-256: `0457f162bf3ad1b975b3891cb8e5cbe0b7896810b89b68ac508c6b76a80d370f`
- PNG SHA-256: `3fb402c4831b0ad04a2fb958a5934855f1c87d3e61e6014594e21460271c9336`

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
