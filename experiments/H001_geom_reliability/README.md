# H001 Geometry Reliability Experiment

Last updated: 2026-06-25 KST

This is the Docker-based experiment root for GeoCalib/H001. Paper-facing
summaries are promoted to `results/h001_geom_reliability/`; row-level runtime
artifacts remain under this experiment tree or in an external release bundle.

Paper-facing name: `GeoCalib: Calibrating Geometric Consistency for Reliable 3D Scene Graph Relations`.
`H001` remains the internal experiment identifier.

## Current Route

- Main sources: VL-SAT full official validation and Open3DSG full-validation `recovery_relaxed_views_min2/`.
- Main relation families: `support_contact`, `proximity`, `relative_vertical`.
- Main score: `family_conditional_risk = semantic_score * p_geom_valid_family`.
- Pooled ablation: `probabilistic_recalibrated = semantic_score * p_geom_valid`.
- Geometry-only control: `control_p_geom_valid_only`, ranking by `p_geom_valid` without semantic score.
- K grid: `{5, 10, 20, 50, 100}`. K=1 is sanity-check only.
- Current paper build: `logs/h001_aaai_pdf_build_family_main_20260625_084157.log`, exit 0.

## Source Roles

| Source | Role | Primary path |
| --- | --- | --- |
| VL-SAT | controlled reproduced anchor | `sources/vlsat/full_validation/` |
| Open3DSG | main open-vocabulary relation-source case study | `sources/open3dsg/full_validation/recovery_relaxed_views_min2/` |
| Qwen-VL | appendix/extension third semantic source | `sources/qwen_vl/` |
| Open3DSG 533/548 branch | unmodified-source sensitivity | `sources/open3dsg/full_validation/` |
| historical 127-scan branches | appendix/sensitivity/provenance only | older source subfolders and `archive/` |

## Current Full-Validation Counts

| Item | Count |
| --- | ---: |
| validation scans | 157 |
| contexts | 548 |
| directed pairs | 36,808 |
| VL-SAT prediction rows | 957,008 |
| Open3DSG recovery prediction rows | 695,916 |
| GT rows | 11,254 |
| in-scope H001-family GT rows | 3,972 |

## Main Metrics

VL-SAT full-validation:

| Condition | R@50 | R@100 | V@50 | V@100 |
| --- | ---: | ---: | ---: | ---: |
| `semantic_only` | 0.9272 | 0.9635 | 0.0268 | 0.0476 |
| `family_conditional_risk` | 0.9288 | 0.9683 | 0.0206 | 0.0333 |
| `probabilistic_recalibrated` | 0.9305 | 0.9688 | 0.0229 | 0.0404 |
| `rule_verified_point_subtype` | 0.9257 | 0.9627 | 0.0000 | 0.0000 |

Open3DSG full-validation recovery:

| Condition | R@50 | R@100 | V@50 | V@100 |
| --- | ---: | ---: | ---: | ---: |
| `semantic_only` | 0.4096 | 0.5161 | 0.1386 | 0.1242 |
| `family_conditional_risk` | 0.4658 | 0.6047 | 0.0286 | 0.0341 |
| `probabilistic_recalibrated` | 0.3975 | 0.5723 | 0.0606 | 0.0811 |
| `rule_verified_point_subtype` | 0.4295 | 0.5368 | 0.0000 | 0.0000 |

The raw metric JSON may still contain legacy condition keys such as
`control_family_specific_p_geom_valid`; paper-facing tables and prose should
refer to that operating point as `family_conditional_risk`.

## Canonical Artifacts

Paper-facing compact outputs:

- `results/h001_geom_reliability/report.md`
- `results/h001_geom_reliability/manifest.lock.json`
- `results/h001_geom_reliability/tables/`
- `results/h001_geom_reliability/bootstrap_ci/summary.md`
- `results/h001_geom_reliability/figures/figure_specs.md`
- `results/h001_geom_reliability/full_validation_transition/artifact_bundle/`

Primary source artifacts:

- `sources/vlsat/full_validation/metrics/metrics.json`
- `sources/vlsat/full_validation/metrics_k_sweep/metrics.json`
- `sources/vlsat/full_validation/bootstrap_ci/summary.md`
- `sources/vlsat/full_validation/gt_eval/metrics.json`
- `sources/open3dsg/full_validation/recovery_relaxed_views_min2/metrics/metrics.json`
- `sources/open3dsg/full_validation/recovery_relaxed_views_min2/metrics_k_sweep/metrics.json`
- `sources/open3dsg/full_validation/recovery_relaxed_views_min2/bootstrap_ci/summary.md`
- `sources/open3dsg/full_validation/recovery_relaxed_views_min2/table_caveats/report.md`

## Runbook

Use `experiments/H001_geom_reliability/commands.md` for exact commands.

Common Docker checks from the repo root:

```bash
docker compose -f configs/h001/compose.yaml config --quiet
docker compose -f configs/h001/compose.yaml run --rm table_builder
docker compose -f configs/h001/compose.yaml run --rm bootstrap_ci
```

Artifact bundle verification:

```bash
bash results/h001_geom_reliability/full_validation_transition/artifact_bundle/verify_upload_bundle.sh
```

Latest verified bundle logs:

- `logs/h001_fullval_upload_checksums_family_main_20260625_085344.log`, exit 0.
- `logs/h001_fullval_upload_verify_family_main_20260625_085354.log`, exit 0.

## Claim Boundary

Allowed:

- scoped relation reliability for geometry-checkable families;
- calibrated geometry-consistency evaluation and re-ranking;
- explicit recall/violation tradeoff reporting;
- Open3DSG as source-output reliability evidence with recovery-policy caveats.

Blocked:

- broad open-vocabulary 3DSSG SOTA claim;
- treating Open3DSG recovery as an unmodified official benchmark result;
- promoting Qwen-VL or relation-family expansions into the main claim without explicit decision and matching evidence gates.

## Archived Or Optional Material

Historical 127-scan outputs, non-avg branch details, failed/intermediate runs,
relative-horizontal/lateral experiments, and attachment-deferred experiments
are provenance, appendix, or future-work material. Keep their detailed logs in
their owning subfolders or `archive/`; do not copy them into current main
tables unless the claim boundary is intentionally changed.
