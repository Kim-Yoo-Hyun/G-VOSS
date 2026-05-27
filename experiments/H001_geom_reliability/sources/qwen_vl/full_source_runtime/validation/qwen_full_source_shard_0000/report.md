# Qwen-VL Contract Validation Report

Status: `validator_parser_skeleton_ready_no_model_runtime`
Created at: `2026-05-26T17:22:25+00:00`

## Scope

This is a contract-only validator/parser skeleton. It does not download a model and does not run Qwen-VL inference.

## Counts

- input rows: `33384`
- parsed rows: `250`
- input errors: `0`
- output errors: `0`
- warnings: `0`

## Outputs

- `parsed_jsonl`: `experiments/H001_geom_reliability/sources/qwen_vl/full_source_runtime/validation/qwen_full_source_shard_0000/parsed.jsonl`
- `parser_contract`: `experiments/H001_geom_reliability/sources/qwen_vl/full_source_runtime/validation/qwen_full_source_shard_0000/parser_contract.json`
- `manifest`: `experiments/H001_geom_reliability/sources/qwen_vl/full_source_runtime/validation/qwen_full_source_shard_0000/manifest.json`
- `report`: `experiments/H001_geom_reliability/sources/qwen_vl/full_source_runtime/validation/qwen_full_source_shard_0000/report.md`

## Next Gate

Keep using this validator before any Qwen-VL model download or inference. Runtime smoke remains optional and requires an explicit model id, fixed revision/local-dir, prompt version, and Docker command.
