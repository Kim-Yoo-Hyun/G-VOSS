# Full-Validation Artifact Bundle Commands

Status: `full_validation_artifact_bundle_plan_ready_no_archive_created`

These commands package the paper-facing full-validation result bundle. Run them
only when a release/upload archive is needed; the archive can be large, so use a
timestamped log and background/tmux session if packaging blocks interactive
work.

```bash
mkdir -p release logs
ts=$(date +%Y%m%d_%H%M%S)
tar --zstd -cf release/h001_full_validation_results_${ts}.tar.zst \
  local_dataset/Open3DSG_staged/training_repro/mlops/opensg/mlflow/363094050435167554/25da9c4c00214f3b880cedbb2a124177/checkpoints/epoch=13-step=13104.ckpt \
  experiments/H001_geom_reliability/full_validation_transition/scope_contract \
  experiments/H001_geom_reliability/full_validation_transition/artifact_bundle \
  experiments/H001_geom_reliability/manifest.lock.json \
  experiments/H001_geom_reliability/report.md \
  experiments/H001_geom_reliability/tables \
  experiments/H001_geom_reliability/sources/vlsat/full_validation \
  experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2 \
  experiments/H001_geom_reliability/sources/open3dsg/full_validation/table_caveats \
  experiments/H001_geom_reliability/sources/open3dsg/checkpoint_selection
sha256sum release/h001_full_validation_results_${ts}.tar.zst > release/h001_full_validation_results_${ts}.sha256
```

Verification:

```bash
sha256sum -c release/h001_full_validation_results_<timestamp>.sha256
wc -l \
  experiments/H001_geom_reliability/sources/vlsat/full_validation/adapter/predictions.jsonl \
  experiments/H001_geom_reliability/sources/vlsat/full_validation/geometry/verification.jsonl \
  experiments/H001_geom_reliability/sources/vlsat/full_validation/failure_rows/rows.jsonl \
  experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2/raw_dump/raw.jsonl \
  experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2/adapter/predictions.jsonl \
  experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2/geometry/verification.jsonl \
  experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2/failure_rows/rows.jsonl
jq -r '.status' \
  experiments/H001_geom_reliability/sources/vlsat/full_validation/metrics/metrics.json \
  experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2/metrics/metrics.json \
  experiments/H001_geom_reliability/sources/vlsat/full_validation/failure_cases/inspection.json \
  experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2/failure_cases/inspection.json
```
