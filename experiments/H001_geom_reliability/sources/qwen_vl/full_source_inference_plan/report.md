# Qwen-VL Full-Source Inference Runner Plan

Status: `full_source_inference_runner_frozen_no_inference`
Created at: `2026-05-26T17:03:15+00:00`

## Scope

- inferable input rows: `33384`
- missing rows: `44364`
- shards: `134`
- verified unique pair crops: `11128`
- target role: `third_semantic_source_modern_vlm_extension`

## Policy

- The runner is frozen, but no Qwen model load or full-source inference is run by this plan.
- Inference must run shard-wise through Docker with timestamped logs under `logs/`.
- Resume key is `record_id`; partial shard outputs are append-resumed via `completed.jsonl`.
- Qwen outputs remain non-metric until contract validation, adapter export, geometry join, metrics, controls, bootstrap, and audit complete.
