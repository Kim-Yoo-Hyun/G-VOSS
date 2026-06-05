# Open3DSG Prediction Adapter

Created at: `2026-06-04T18:18:01.884060+00:00`
Status: `ready`
Raw dump: `experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2/raw_dump/raw.jsonl`
Smoke test: `False`

## Outputs

- predictions: `experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2/adapter/predictions.jsonl`
- raw smoke: `None`
- raw schema example: `experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2/adapter/raw_schema_example.json`
- manifest: `manifest.json`

## Counts

- contexts: `548`
- raw rows: `26938`
- raw rows filtered outside H001 context: `172`
- prediction rows: `695916`
- errors: `0`
- warnings: `172`

## Claim Boundary

This artifact fixes the Open3DSG-to-H001 prediction contract only. Raw rows outside the fixed H001 object context are filtered and counted before metric execution. It is not second-source metric evidence until predictions are joined with geometry and evaluated.
