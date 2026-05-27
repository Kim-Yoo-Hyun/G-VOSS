# Qwen-VL Runtime Smoke

Status: `tiny_inference_smoke_passed`
Created at: `2026-05-26T15:23:39.151027+00:00`

## Scope

This is a runtime smoke gate only. It is not a paper metric and does not replace the Open3DSG reproduction anchor.

## Model

- model id: `Qwen/Qwen3-VL-4B-Instruct`
- revision: `ebb281ec70b05090aa6165b016eac8ec08e71b17`
- local dir: `local_dataset/model_cache/huggingface/qwen_vl/Qwen3-VL-4B-Instruct/ebb281ec70b05090aa6165b016eac8ec08e71b17`

## Cache

- ready: `True`
- file count: `43`
- weight files: `3`
- total GB: `8.277`

## GPU

- available: `True`
- memory used MB: `5895`
- utilization %: `23`

## Runtime

- model loaded: `True`
- processor class: `Qwen3VLProcessor`
- model class: `Qwen3VLForConditionalGeneration`

## Tiny Inference

- attempted rows: `3`
- output rows: `3`
- parser status counts: `{'parsed': 3}`
