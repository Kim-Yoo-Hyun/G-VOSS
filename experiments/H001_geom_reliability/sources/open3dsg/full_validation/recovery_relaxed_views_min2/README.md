# Open3DSG Full-Validation Recovery Branch

Status: `open3dsg_full_validation_recovery_relaxed_views_min2_metric_and_failure_analysis_ready`

Last updated: `2026-06-25 KST`

This branch is the paper-facing primary Open3DSG full-validation result for
H001. It covers all 548 official validation contexts by using a documented
recovery policy: `OPEN3DSG_MIN_VISIBLE_OBJECTS=2` plus relaxed view regeneration
for two scans. The original 533/548 full-validation branch remains the
unmodified-source-route sensitivity check.

## Scope

- validation scans: `157`
- contexts: `548/548`
- raw rows: `26,938`
- prediction rows: `695,916`
- geometry rows: `695,916`
- H001-family geometry-checkable rows: `160,596`
- H001-family GT denominator: `3,972`

## Completed Gates

- payload/view/preprocess recovery: `payload/`, `views/`, `preprocess/`
- feature audit: `features/`, 548/548
- raw dump: `raw_dump/`, clean exit `0`, 548/548 batches
- raw-dump identity: `raw_dump_identity/`
- adapter export: `adapter/`
- geometry join: `geometry/`
- metrics/controls: `metrics/`
- low-K metric sweep: `metrics_k_sweep/`, status `ready`, K=`{5,10,20,50,100}`
- bootstrap CI: `bootstrap_ci/`
- failure-analysis rows: `failure_rows/`
- qualitative failure queue/inspection: `failure_cases/`
- Table 6/caveat report: `table_caveats/`

## Key Metrics

Low-K sweep artifact: `metrics_k_sweep/metrics.json`. K=50/100 values match
the locked `metrics/metrics.json` exactly.

| condition | R@5 | R@10 | R@20 | R@50 | R@100 | V@5 | V@10 | V@20 | V@50 | V@100 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| semantic_only | 0.0368 | 0.1002 | 0.1991 | 0.4096 | 0.5161 | 0.5131 | 0.3255 | 0.2088 | 0.1386 | 0.1242 |
| probabilistic_recalibrated | 0.0826 | 0.1581 | 0.2603 | 0.3975 | 0.5723 | 0.0628 | 0.0699 | 0.0654 | 0.0606 | 0.0811 |
| rule_verified_point_subtype | 0.0707 | 0.1314 | 0.2422 | 0.4295 | 0.5368 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| family_conditional_risk | 0.0984 | 0.1921 | 0.3291 | 0.4658 | 0.6047 | 0.0420 | 0.0482 | 0.0441 | 0.0286 | 0.0341 |

Failure-analysis summary:

- rows: `82,155`
- validation errors: `0`
- visual-audit queue rows: `8,821`
- selected qualitative cases: `36`
- selected categories: `geometry_contradiction` 13,
  `semantic_and_geometry_failure` 23
- selected families: `support_contact` 10, `proximity` 7,
  `relative_vertical` 19
- inspection summary: 25 demoted by geometry-aware reranking, 11
  promoted/retained, and 8 violated cases with `p_geom_valid > 0.9`

## Claim Boundary

Use this branch as the primary Open3DSG full-validation evidence for the
current H001 families. Always disclose the recovery policy; do not describe it
as the unmodified Open3DSG preprocess route. Treat `failure_cases/` as
deterministic qualitative failure-mechanism evidence, not as an independent
human visual audit.
