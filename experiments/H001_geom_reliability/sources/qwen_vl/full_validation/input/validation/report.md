# Qwen-VL Contract Validation Report

Status: `validator_parser_skeleton_ready_no_model_runtime`
Created at: `2026-06-11T05:12:30+00:00`

## Scope

This is a contract-only validator/parser skeleton. It does not download a model and does not run Qwen-VL inference.

## Counts

- input rows: `46506`
- parsed rows: `1`
- input errors: `0`
- output errors: `0`
- warnings: `0`

## Outputs

- `parsed_jsonl`: `experiments/H001_geom_reliability/sources/qwen_vl/full_validation/input/validation/parsed.jsonl`
- `parser_contract`: `experiments/H001_geom_reliability/sources/qwen_vl/full_validation/input/validation/parser_contract.json`
- `manifest`: `experiments/H001_geom_reliability/sources/qwen_vl/full_validation/input/validation/manifest.json`
- `report`: `experiments/H001_geom_reliability/sources/qwen_vl/full_validation/input/validation/report.md`

## Next Gate

Keep using this validator before any Qwen-VL model download or inference. Runtime smoke remains optional and requires an explicit model id, fixed revision/local-dir, prompt version, and Docker command.
