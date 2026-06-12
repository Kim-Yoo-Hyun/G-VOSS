# Qwen-VL Full-Source Input Audit

Status: `full_source_input_ready_with_missing_rows_no_inference`
Created at: `2026-06-11T05:12:11+00:00`

## Scope

- Role: third semantic source / modern VLM extension.
- No model download, model load, or Qwen inference is run by this artifact.
- Qwen remains non-metric until sharded inference, parser validation, adapter export, geometry join, metrics, bootstrap, and audit complete.

## Counts

- selected scans: `157`
- contexts: `548`
- directed pairs: `36808`
- universe query rows: `110424`
- inferable input rows: `46506`
- missing query rows: `63918`
- shards: `187`
- shard size: `250`

## Missing-Row Policy

Rows without shared object-pair view metadata or source images are retained in missing.jsonl and excluded from Qwen inference input.jsonl. Qwen metrics must report this denominator separately and must not silently inherit Open3DSG denominators after row drops.

## Outputs

- `universe_jsonl`: `experiments/H001_geom_reliability/sources/qwen_vl/full_validation/input/universe.jsonl`
- `input_jsonl`: `experiments/H001_geom_reliability/sources/qwen_vl/full_validation/input/input.jsonl`
- `missing_jsonl`: `experiments/H001_geom_reliability/sources/qwen_vl/full_validation/input/missing.jsonl`
- `shards_jsonl`: `experiments/H001_geom_reliability/sources/qwen_vl/full_validation/input/shards.jsonl`
- `manifest`: `experiments/H001_geom_reliability/sources/qwen_vl/full_validation/input/manifest.json`
- `coverage`: `experiments/H001_geom_reliability/sources/qwen_vl/full_validation/input/coverage.json`
- `report`: `experiments/H001_geom_reliability/sources/qwen_vl/full_validation/input/report.md`

## Warnings

- `missing_rows_present:63918`
