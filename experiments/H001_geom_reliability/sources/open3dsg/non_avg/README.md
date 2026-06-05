# Open3DSG Official Non-Avg Branch

Status: `open3dsg_non_avg_branch_ready`

This branch evaluates the official non-averaged BLIP Open3DSG checkpoint without
overwriting the current avg-BLIP paper-facing artifacts under
`sources/open3dsg/{raw_dump,adapter,geometry,metrics,...}`.

## Fixed Inputs

- selected checkpoint:
  `local_dataset/Open3DSG_staged/training_repro/mlops/opensg/mlflow/363094050435167554/25da9c4c00214f3b880cedbb2a124177/checkpoints/epoch=13-step=13104.ckpt`
- checkpoint sha256:
  `ca86d429b19e846aec2bfff014256bf36f6f90da07e566b90c461d6eca8d76bb`
- checkpoint route: `official_non_avg_blip_full`
- train-dev selection signal: `val/loss=0.5724539160728455` at step `13103`
- baseline run id: `open3dsg_nonavg_epoch13_step13104`
- feature load dir:
  `local_dataset/Open3DSG_staged/h001_runtime/output/features/clip_features_h001_eval_blip_top5_scales3`

Feature reuse note: Docker shape inspection confirmed the train official and
H001 eval relation feature tensors use BLIP sequence tensors shaped
`(*, 257, 1408)` with `torch.bfloat16`, so the existing covered H001 eval
feature cache is compatible with the non-avg projector route. The known
`validation_missing_preprocessed:11` caveat remains.

## Current Gates

- Docker compose config: passed for both Open3DSG runtime compose and H001
  experiment compose.
- `feature_audit_h001_eval_nonavg`: ran; only blocker is the known
  `validation_missing_preprocessed:11` covered-scope caveat.
- `eval_preflight_nonavg`: `ready`, blockers 0.
- raw stream: `raw_dump_stream_complete`, 19,162 rows, 377/377 completed
  batches.
- raw process exit: `137` after stream finalization; retained as source-process
  caveat, not a row-completeness blocker.
- `open3dsg_raw_dump_identity_nonavg`: `raw_dump_identity_audit_ready`.
- `open3dsg_adapter_raw_dump_nonavg`: `ready`, 496,600 prediction rows.
- `open3dsg_geometry_join_nonavg`: `ready`, 496,600 verification rows and
  114,600 geometry-checkable rows.
- `open3dsg_metric_eval_nonavg`: `ready`.
- `bootstrap_ci_nonavg`: `ready`, 1,000 bootstrap samples.
- `open3dsg_non_avg_table6_caveats`: `open3dsg_non_avg_branch_ready`.

## Branch Outputs

```text
experiments/H001_geom_reliability/sources/open3dsg/non_avg/
  eval_preflight/
  dump_features_h001_eval/
  raw_dump/
  raw_dump_identity/
  adapter/
  geometry/
  metrics/
  bootstrap_ci/
  table6_caveats/
```

Run records:

- raw dump: `raw_dump/run_20260604_182423.md`
- superseded continuation: `downstream_after_raw_20260604_183622.md`
- manual downstream completion: `downstream_manual_20260604.md`

## Metric Summary

| condition | R@50 | R@100 | V@50 | V@100 |
| --- | ---: | ---: | ---: | ---: |
| semantic_only | 0.4310 | 0.5320 | 0.1395 | 0.1256 |
| probabilistic_recalibrated | 0.3945 | 0.5639 | 0.0570 | 0.0782 |
| rule_verified_point_subtype | 0.4507 | 0.5481 | 0.0000 | 0.0000 |
| control_family_specific_p_geom_valid | 0.4750 | 0.6047 | 0.0243 | 0.0310 |

Compared with the avg-BLIP branch, non-avg improves R@100 for all listed
conditions. Semantic-only violation is slightly higher, while geometry-aware
conditions are similar or slightly better on V@100.

## Caveat Boundary

This branch is now complete enough to be reported as a separately regenerated
official non-avg Open3DSG branch. Promotion over the current avg-BLIP Open3DSG
result still requires explicit user confirmation. Filtered train/dev, covered
H001 `377/388`, exact-label denominator `2,545`,
`validation_missing_preprocessed:11`, and residual calibration-risk caveats
remain.
