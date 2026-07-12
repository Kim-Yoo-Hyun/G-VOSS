# GeoCalib / H001 Figure Source Lock

Last updated: 2026-07-12 KST

Status: `camera_ready_three_figure_revision_passed`

This file owns the paper-facing claims, source artifacts, and non-claims for
Figures 1--3. Generated assets live under `paper/generated/figures/`; metric
and case provenance stays in `experiments/H001_geom_reliability/`.

## Global Contract

- Figures support a factor-isolated reliability layer for geometry-identifiable
  3D Scene Graph relations, not broad generation SOTA.
- Use paper-facing names only: source confidence, predicate--geometry
  compatibility, family-calibrated product, rank-average fusion, physical
  violation, and uncertain geometry.
- Report Recall and Violation together. Lower Violation and higher Recall are
  better.
- K=100 is the primary endpoint, K=50 the canonical secondary endpoint,
  and K=10 the top-ranked operational setting. K=5/20 provide trajectory
  continuity; K=1 is not a paper endpoint.
- Qwen-VL and ReplicaSSG/FROSS do not appear in the three main figures.

## Figure 1: Failure to Framework

Locked claim:

> Semantically confident relation predictions can be geometrically
> inconsistent because source confidence does not measure predicate-conditioned
> physical compatibility; GeoCalib isolates those factors before re-ranking.

Locked visual form:

- Four stages: observed inconsistent relation, isolated `T/G/Z` evidence,
  compatibility plus falsification/identity controls, and fusion plus joint
  evaluation.
- The displayed failure is the traceable Open3DSG heater--trash-can `close by`
  case used by Figure 3.
- `Z` is visibly excluded from `C(T,G)` and used only at final fusion.
- No reviewer checklist, claim-boundary band, learned point encoder, energy
  model, evidence router, or abstention head appears.

Assets:

- `paper/generated/figures/figure1_framework.svg`
- `paper/generated/figures/figure1_framework.png`
- `paper/scripts/generate_draft_figures.py`

Caption constraint: call GeoCalib a calibrated, factor-isolated
geometry-consistency evaluation and re-ranking framework, not a verifier
script or a new fusion formula.

## Figure 2: Operating-Budget Trajectories

Locked claim:

> The calibrated product preserves or improves the Recall--Violation tradeoff
> across smaller budgets, while the two-instantiation SGFN gate is specific to
> the primary K=100 endpoint.

Locked visual form:

- Three source panels: VL-SAT, Open3DSG, and SGFN.
- Connect K=`{5,10,20,50,100}` for source confidence and the calibrated
  product; label each point by K.
- Orange ring: primary K=100 endpoint. K=50 is secondary and K=10 is
  operational.
- Separate panel axes because source recall denominators and candidate
  distributions differ.
- Do not claim every source improves Recall at every K; VL-SAT has small
  low-K Recall decreases.

Sources:

- `experiments/H001_geom_reliability/sources/vlsat/full_validation/metrics_k_sweep/metrics.json`
- `experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2/metrics_k_sweep/metrics.json`
- `experiments/H001_geom_reliability/sources/sgfn/confirmatory_metrics_v3/metrics.json`
- `paper/generated/figures/figure2_data.json`

Assets:

- `paper/generated/figures/figure2_tradeoff.svg`
- `paper/generated/figures/figure2_tradeoff.png`

## Figure 3: Corrections and Residual Failure

Locked claim:

> Identity-aligned geometry can demote physically inconsistent semantic
> predictions, but engineered evidence remains incomplete and can also promote
> a residual violation.

Locked cases:

| panel | case | role | relation | source rank -> product rank | source / compatibility |
| --- | --- | --- | --- | ---: | ---: |
| A | `open3dsg_case_001` | corrected proximity error | heater `close by` trash can | 19 -> 294 | 0.853 / 0.013 |
| B | `open3dsg_case_010` | corrected support/contact error | lamp `lying on` side table | 39 -> 310 | 0.843 / 0.078 |
| C | `open3dsg_case_026` | residual top-10 failure | door `lying on` floor | 21 -> 10 | 0.843 / approximately 1.0 |

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
- `paper/generated/figures/figure3_geometry_panels.png`
- `paper/generated/figures/figure3_geometry_cases.json`
- `paper/generated/figures/figure3_geometry_manifest.json`

## Validation

- `paper/generated/figures/validation.json`: `passed`
- Figure 1 contains no unimplemented component or review-artifact band.
- Figure 2 metric extraction and all K labels pass source-lock validation.
- Figure 3 uses the three locked IDs and the same geometry rows as its manifest.
- PNG/SVG assets parse and are included in the current AAAI PDF.
