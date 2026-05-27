# Qwen-VL Full-Source Input Audit

Status: `full_source_input_ready_with_missing_rows_no_inference`
Created at: `2026-05-26T15:59:37+00:00`

## Scope

- Role: third semantic source / modern VLM extension.
- No model download, model load, or Qwen inference is run by this artifact.
- Qwen remains non-metric until sharded inference, parser validation, adapter export, geometry join, metrics, bootstrap, and audit complete.

## Counts

- selected scans: `127`
- contexts: `388`
- directed pairs: `25916`
- universe query rows: `77748`
- inferable input rows: `33384`
- missing query rows: `44364`
- shards: `134`
- shard size: `250`

## Missing-Row Policy

Rows without shared object-pair view metadata or source images are retained in missing.jsonl and excluded from Qwen inference input.jsonl. Qwen metrics must report this denominator separately and must not silently inherit Open3DSG denominators after row drops.

## Outputs

- `universe_jsonl`: `experiments/H001_geom_reliability/sources/qwen_vl/full_source_input/universe.jsonl`
- `input_jsonl`: `experiments/H001_geom_reliability/sources/qwen_vl/full_source_input/input.jsonl`
- `missing_jsonl`: `experiments/H001_geom_reliability/sources/qwen_vl/full_source_input/missing.jsonl`
- `shards_jsonl`: `experiments/H001_geom_reliability/sources/qwen_vl/full_source_input/shards.jsonl`
- `manifest`: `experiments/H001_geom_reliability/sources/qwen_vl/full_source_input/manifest.json`
- `coverage`: `experiments/H001_geom_reliability/sources/qwen_vl/full_source_input/coverage.json`
- `report`: `experiments/H001_geom_reliability/sources/qwen_vl/full_source_input/report.md`

## Warnings

- `missing_rows_present:44364`
