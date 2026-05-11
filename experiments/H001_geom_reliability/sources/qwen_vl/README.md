# Qwen-VL Semantic-Source Adapter

Status: `io_contract_frozen_model_runtime_not_started`
Created at: `2026-05-08T06:35:07+00:00`

## Role

Qwen-VL is a modern open-vocabulary VLM semantic-source extension for H001.
It is not a replacement for the Open3DSG reproduction anchor and is not an end-to-end 3DSSG training result.

## Model Ladder

- recommended small modern main: `Qwen/Qwen3-VL-4B-Instruct`
- stable small fallback: `Qwen/Qwen2.5-VL-3B-Instruct`
- lowest-cost parser smoke: `Qwen/Qwen3-VL-2B-Instruct`
- optional quality follow-ups: `Qwen/Qwen3-VL-8B-Instruct`, `Qwen/Qwen2.5-VL-7B-Instruct`

## Contract Files

- `adapter_contract.json`: model candidates, schemas, pilot plan, and claim boundary
- `input_schema.json`: frozen input JSON Schema
- `input_schema_example.json`: example input JSONL row
- `output_schema.json`: frozen output JSONL row JSON Schema
- `output_jsonl_contract.md`: human-readable output JSONL contract
- `model_candidates.json`: candidate model ladder including 2B/3B/4B options
- `prediction_schema_example.json`: example identity-preserving output row
- `prompt_templates.md`: semantic-only and diagnostic prompt templates
- `commands.qwen_vl.md`: Docker command entrypoint for this contract
- `report.md`: human-readable summary
- `validation/`: contract-only validator/parser skeleton outputs after running `qwen_vl_contract_validator`
- `tiny_pilot/`: non-held-out 30-row pilot input scope and validator outputs
- `runtime_plan/`: crop-rendering preflight and recommended model id/revision/local-dir
- `crops/`: pair-crop rendering records/manifest/report; crop images stay under ignored `local_dataset/qwen_vl_crops/`

## Next Gate

Before any model download or inference, render and validate tiny-pilot pair crops, then run the input/output JSONL validator and parser skeleton against these frozen contracts.
Docker cache/runtime smoke is a later optional gate after an explicit model choice; prefer `Qwen/Qwen3-VL-4B-Instruct` and fall back to `Qwen/Qwen2.5-VL-3B-Instruct` if Qwen3-VL runtime friction blocks progress.
