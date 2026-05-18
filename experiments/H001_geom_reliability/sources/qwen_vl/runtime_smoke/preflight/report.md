# Qwen-VL Runtime Smoke

Status: `blocked_runtime_preflight`
Created at: `2026-05-11T23:32:13.423557+00:00`

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
- memory used MB: `22449`
- utilization %: `59`

## Runtime

- model loaded: `False`
- processor class: `None`
- model class: `None`

## Blockers

- `gpu_busy_or_unavailable:memory_used_mb=22449,utilization=59`
