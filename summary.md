# GeoCalib / H001 Research Summary

Last updated: 2026-06-25 KST

Paper-facing name: `GeoCalib: Calibrating Geometric Consistency for Reliable 3D Scene Graph Relations`.
Use `GeoCalib` in manuscript-facing prose. Keep `H001` only for internal
experiment paths and archived hypothesis records.

## Current Status

- Current paper route: AAAI-style manuscript under `paper/aaai/`.
- Latest source-validation build: `logs/h001_aaai_pdf_build_reference_expansion_20260625_130811.log`, exit 0, output `paper/aaai/main_reference_expansion.pdf`.
- PDF status: 9 total pages, references start on page 7, reproducibility checklist page 9. The original `paper/aaai/main.pdf` is preserved.
- Main sources: VL-SAT full official validation and Open3DSG full-validation `recovery_relaxed_views_min2/`.
- Main score: `family_conditional_risk = semantic_score * p_geom_valid_family`.
- Pooled ablation: `probabilistic_recalibrated = semantic_score * p_geom_valid`.
- Geometry-only control: rank by `p_geom_valid` without semantic score.
- Main K grid: `{5, 10, 20, 50, 100}`. K=1 is sanity-check only.
- Qwen-VL is complete as a third-source / modern VLM extension, but it is not part of the main claim unless explicitly promoted.

## Claim Boundary

Allowed claim:

```text
For geometry-checkable 3D Scene Graph relation families, GeoCalib exposes and
reduces semantically plausible but geometrically inconsistent relation
predictions by applying a calibrated geometry-consistency reliability layer
while reporting recall tradeoffs.
```

Current scope:

- `support_contact`
- `proximity`
- `relative_vertical`

Not claimed:

- Broad open-vocabulary 3D Scene Graph generation improvement.
- Baseline-agnostic or SOTA 3DSSG improvement.
- Guaranteed physical correctness of every retained relation.
- Promotion of `relative_horizontal`, `relative_lateral`, or `attachment_deferred` into the main AAAI claim.

## Method

GeoCalib is a calibrated geometry-consistency evaluation and re-ranking
framework over existing relation-source outputs.

Core steps:

1. Standardize relation predictions into identity-preserving rows.
2. Join subject/object 3D geometry evidence for the same object pair.
3. Evaluate relation-family-specific geometric consistency.
4. Calibrate geometry validity as `p_geom_valid` or `p_geom_valid_family`.
5. Re-rank relation predictions with semantic confidence and calibrated geometry risk.
6. Report `R@K` and `Violation@K` together.

Main scoring conditions:

| Condition | Role |
| --- | --- |
| `semantic_only` | source ranking baseline |
| `family_conditional_risk` | GeoCalib main score |
| `probabilistic_recalibrated` | pooled calibrated-risk ablation |
| `rule_verified_point_subtype` | hard-rule diagnostic |
| `control_p_geom_valid_only` | geometry-only control |
| `control_distance_only` | distance-only control |
| `control_shuffled_geometry` | geometry distribution control |
| `control_wrong_pair_geometry` | object-pair identity control |

## Current Evidence

Full official validation scope:

| Item | Count |
| --- | ---: |
| validation scans | 157 |
| contexts | 548 |
| directed pairs | 36,808 |
| VL-SAT prediction rows | 957,008 |
| Open3DSG recovery prediction rows | 695,916 |
| GT rows | 11,254 |
| in-scope H001-family GT rows | 3,972 |

VL-SAT full-validation source result:

| Condition | R@50 | R@100 | V@50 | V@100 |
| --- | ---: | ---: | ---: | ---: |
| `semantic_only` | 0.9272 | 0.9635 | 0.0268 | 0.0476 |
| `family_conditional_risk` | 0.9288 | 0.9683 | 0.0206 | 0.0333 |
| `probabilistic_recalibrated` | 0.9305 | 0.9688 | 0.0229 | 0.0404 |
| `rule_verified_point_subtype` | 0.9257 | 0.9627 | 0.0000 | 0.0000 |

Open3DSG full-validation recovery source result:

| Condition | R@50 | R@100 | V@50 | V@100 |
| --- | ---: | ---: | ---: | ---: |
| `semantic_only` | 0.4096 | 0.5161 | 0.1386 | 0.1242 |
| `family_conditional_risk` | 0.4658 | 0.6047 | 0.0286 | 0.0341 |
| `probabilistic_recalibrated` | 0.3975 | 0.5723 | 0.0606 | 0.0811 |
| `rule_verified_point_subtype` | 0.4295 | 0.5368 | 0.0000 | 0.0000 |

Bootstrap CI summary:

- Open3DSG `family_conditional_risk` vs `semantic_only`: R@100 delta `+8.86 pp`, 95% CI `[+6.69, +10.96]`; Violation@100 delta `-9.01 pp`, 95% CI `[-9.49, -8.53]`.
- VL-SAT `family_conditional_risk` vs `semantic_only`: R@100 delta `+0.48 pp`, 95% CI `[+0.11, +0.93]`; Violation@100 delta `-1.43 pp`, 95% CI `[-1.60, -1.28]`.

Verifier evidence:

- GT positives: 3,972.
- Counterfactual negatives: 3,972.
- Positive nonviolated rate: 0.9965.
- Counterfactual nonsatisfied rate: 0.9673.
- AUROC/AUPRC: 0.9772 / 0.9729.
- Brier: 0.0543.

## Source Roles

| Source | Current role |
| --- | --- |
| VL-SAT | controlled reproduced anchor |
| Open3DSG | main open-vocabulary relation-source case study |
| Qwen-VL | appendix/extension third semantic source |
| `relative_horizontal` | stopped appendix/limitation scope-expansion evidence |
| `relative_lateral` | stopped appendix/future-work boundary evidence |
| `attachment_deferred` | preferred future family expansion, not current main claim |

Open3DSG caveats to keep visible:

- selected official non-avg checkpoint;
- filtered train/dev provenance;
- 548/548 recovery branch with `OPEN3DSG_MIN_VISIBLE_OBJECTS=2`;
- relaxed two-scan view regeneration;
- 533/548 unmodified-source sensitivity branch;
- appendix-only historical 127-scan / R2 sensitivity;
- residual calibration risk.

## Artifact And Reproducibility State

Primary current locations:

- `paper/aaai/`: active manuscript source.
- `results/h001_geom_reliability/report.md`: compact paper-facing result report.
- `results/h001_geom_reliability/manifest.lock.json`: locked current result manifest.
- `results/h001_geom_reliability/tables/`: compact table artifacts.
- `results/h001_geom_reliability/bootstrap_ci/`: compact bootstrap mirror.
- `experiments/H001_geom_reliability/sources/vlsat/full_validation/`: VL-SAT full-validation runtime results.
- `experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2/`: selected Open3DSG full-validation recovery route.
- `results/h001_geom_reliability/full_validation_transition/artifact_bundle/`: external upload payload list, checksums, and verification script.

Latest bundle verification:

- checksum generation log: `logs/h001_fullval_upload_checksums_family_main_20260625_085344.log`, exit 0.
- verification log: `logs/h001_fullval_upload_verify_family_main_20260625_085354.log`, exit 0.
- payload files: 211.
- checksum records: 211.
- row-count snapshot records: 18.

Large datasets, checkpoints, model caches, feature caches, raw dumps, and
row-level JSONL are not Git artifacts. Use `docs/reproducibility.md` before any
transfer, cleanup, or full rerun.

## Paper State

Current paper-facing files:

- `paper/README.md`: paper workspace map.
- `paper/preview.md`: current handoff snapshot.
- `paper/progress.md`: progress rationale.
- `paper/risk.md`: reviewer-risk register.
- `paper/review.md`: orthogonal persona review.
- `paper/appendix.md`: appendix/supplement plan.
- `paper/figures.md`: figure plan and source lock.
- `paper/aaai/README.md`: active venue-source runbook.

Current figures:

- Figure 1: failure mechanism and GeoCalib framework.
- Figure 2: recall-violation tradeoff.
- Figure 3: Open3DSG qualitative geometry-backed failure cases.

## Remaining TODO

Submission/package hygiene:

1. Confirm final OpenReview/AAAI portal form and exact target-year style constraints.
2. Decide artifact/code-release URL or DOI.
3. Decide supplementary/code-data upload policy.
4. Recheck partial/no reproducibility checklist answers.
5. Regenerate any flattened release package created before the low-K and family-main table/prose update.
6. Run final PDF/source sanity checks from the current checkout.

No new main-source metric experiment is required for the current GeoCalib claim.
