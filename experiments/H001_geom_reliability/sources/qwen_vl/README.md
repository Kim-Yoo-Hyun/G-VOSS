# Qwen-VL Semantic-Source Adapter

Status: `model_cache_ready_runtime_preflight_blocked_gpu_busy`
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

- `Dockerfile.qwen`: Docker runtime image for Qwen-VL cache/runtime smoke
- `compose.qwen.yaml`: Docker services for model download, cache verify, runtime preflight, and tiny inference smoke
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
- `model_cache/`: timestamped long-running model-cache job records
- `runtime_smoke/`: cache/preflight/tiny-inference smoke outputs after the relevant Docker services run

## Current Runtime State

- model-cache job: completed, exit code `0`
- log: `logs/qwen_vl_model_download_20260512_082830.log`
- exit file: `logs/qwen_vl_model_download_20260512_082830.exit`
- model id: `Qwen/Qwen3-VL-4B-Instruct`
- revision: `ebb281ec70b05090aa6165b016eac8ec08e71b17`
- local dir: `local_dataset/model_cache/huggingface/qwen_vl/Qwen3-VL-4B-Instruct/ebb281ec70b05090aa6165b016eac8ec08e71b17`
- cache verification: `model_cache_ready`, 43 files, 8.277 GB, 3 weight/index files
- runtime preflight: `blocked_runtime_preflight` because the GPU is still busy with Open3DSG feature dump

## Next Gate

After GPU availability, rerun `qwen_vl_runtime_preflight`, then run
`qwen_vl_tiny_inference_smoke` on 1-3 crops. These outputs are runtime smoke
evidence only, not paper metric evidence, and they do not replace the Open3DSG
reproduction anchor.
