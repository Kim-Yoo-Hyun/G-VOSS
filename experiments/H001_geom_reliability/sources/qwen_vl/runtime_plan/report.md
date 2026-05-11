# Qwen-VL Runtime Plan

Status: `runtime_plan_ready_no_model_download_no_inference`
Created at: `2026-05-08T06:30:19+00:00`

## Scope

This is a planning/preflight artifact only. It does not render crops, download a model, or run Qwen-VL inference.

## Crop Preflight

- input rows: `30`
- pair crops existing: `30`
- pair crops missing: `0`
- context frames existing: `30`
- object2image metadata existing: `30`

## Recommended Model Lock

- model id: `Qwen/Qwen3-VL-4B-Instruct`
- revision: `ebb281ec70b05090aa6165b016eac8ec08e71b17`
- local dir: `local_dataset/model_cache/huggingface/qwen_vl/Qwen3-VL-4B-Instruct/ebb281ec70b05090aa6165b016eac8ec08e71b17`

## Claim Boundary

No Qwen-VL runtime evidence exists yet. This only fixes the next runtime gate and recommended model lock.
