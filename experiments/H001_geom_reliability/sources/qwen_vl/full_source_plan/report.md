# Qwen-VL Full-Source Promotion Plan

Status: `full_source_promotion_plan_frozen_no_metric_run`
Created at: `2026-05-26T15:33:49.774731+00:00`

## Role

Qwen-VL is frozen as a third semantic source / modern VLM extension. It is not a replacement for VL-SAT or Open3DSG.

## Current Evidence

- cache status: `model_cache_ready`
- tiny runtime smoke: `tiny_inference_smoke_passed`
- runtime contract validation: `validator_parser_skeleton_ready_no_model_runtime`
- tiny attempted/output rows: `3` / `3`

## Frozen Metric Scope

- selected scans: `127`
- contexts: `388`
- directed pairs: `25916`
- max all-pairs x family query rows: `77748`
- in-scope GT denominator: `2545`
- target family counts: `{'proximity': 1128, 'relative_vertical': 218, 'support_contact': 1199}`

## Promotion Rule

Qwen can be added as paper evidence only after full-source input audit, shard inference, parser validation, prediction export, geometry join, metrics, controls, bootstrap CI, and qualitative audit complete in Docker.

Tiny smoke results remain non-metric evidence.
