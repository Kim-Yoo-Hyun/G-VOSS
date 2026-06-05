# Open3DSG Full-Validation Recovery Branch

Status: `open3dsg_full_validation_recovery_relaxed_views_min2_metric_and_failure_analysis_ready`

Last updated: `2026-06-05 KST`

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
- bootstrap CI: `bootstrap_ci/`
- failure-analysis rows: `failure_rows/`
- qualitative failure queue/inspection: `failure_cases/`
- Table 6/caveat report: `table_caveats/`

## Key Metrics

| condition | R@50 | R@100 | V@50 | V@100 |
| --- | ---: | ---: | ---: | ---: |
| semantic_only | 0.4096 | 0.5161 | 0.1386 | 0.1242 |
| probabilistic_recalibrated | 0.3975 | 0.5723 | 0.0606 | 0.0811 |
| rule_verified_point_subtype | 0.4295 | 0.5368 | 0.0000 | 0.0000 |
| control_family_specific_p_geom_valid | 0.4658 | 0.6047 | 0.0286 | 0.0341 |

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
