# Qwen-VL Pair Crop Rendering

Status: `pair_crops_rendered_no_model_download_no_inference`
Created at: `2026-05-08T06:30:17+00:00`

## Scope

This renders tiny-pilot object-pair crops only. It does not download a model or run Qwen-VL inference.

## Counts

- input rows: `30`
- rendered crops: `30`
- updated input rows: `30`
- rows without shared view: `0`
- missing image rows: `0`

## Outputs

- `crop_root`: `local_dataset/qwen_vl_crops/tiny_pilot`
- `records_jsonl`: `experiments/H001_geom_reliability/sources/qwen_vl/crops/records.jsonl`
- `manifest`: `experiments/H001_geom_reliability/sources/qwen_vl/crops/manifest.json`
- `report`: `experiments/H001_geom_reliability/sources/qwen_vl/crops/report.md`
- `updated_input_jsonl`: `experiments/H001_geom_reliability/sources/qwen_vl/tiny_pilot/input.jsonl`

## Claim Boundary

These crops are runtime input artifacts only. They are not Qwen-VL prediction or metric evidence.
