# Open3DSG Prediction Adapter

Created at: `2026-05-18T08:56:40.272878+00:00`
Status: `ready`
Raw dump: `experiments/H001_geom_reliability/sources/open3dsg/raw_dump/raw.jsonl`
Smoke test: `False`

## Outputs

- predictions: `experiments/H001_geom_reliability/sources/open3dsg/adapter/predictions.jsonl`
- raw smoke: `None`
- raw schema example: `experiments/H001_geom_reliability/sources/open3dsg/adapter/raw_schema_example.json`
- manifest: `manifest.json`

## Counts

- contexts: `388`
- raw rows: `19162`
- raw rows filtered outside H001 context: `62`
- prediction rows: `496600`
- errors: `0`
- warnings: `62`

## Claim Boundary

This artifact fixes the Open3DSG-to-H001 prediction contract only. Raw rows outside the fixed H001 object context are filtered and counted before metric execution. It is not second-source metric evidence until predictions are joined with geometry and evaluated.
