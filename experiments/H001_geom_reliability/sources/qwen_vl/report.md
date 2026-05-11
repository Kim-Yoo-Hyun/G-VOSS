# Qwen-VL Adapter Contract Report

Status: `io_contract_frozen_model_runtime_not_started`
Created at: `2026-05-08T06:35:07+00:00`

## Decision

Use Qwen-VL as an optional modern semantic-source extension after recording the Open3DSG reproduction anchor.
Start with small models: `Qwen3-VL-4B-Instruct` as the recommended modern target, `Qwen2.5-VL-3B-Instruct` as stable fallback, and `Qwen3-VL-2B-Instruct` for lowest-cost parser smoke.

## Claim Boundary

- allowed: modern VLM semantic-source reliability with H001 geometry reranking
- not allowed: end-to-end 3DSSG generation claim
- not allowed: replacement of Open3DSG reproduction evidence

## Acceptance Gates

- frozen `input_schema.json` and `output_schema.json` before model downloads or inference
- contract-only validator/parser skeleton before model downloads or inference
- non-held-out tiny pilot scope before model downloads or inference
- fixed model id and revision/local-dir before held-out metrics
- frozen prompt templates and parser
- identity-preserving prediction JSONL
- semantic-only prompt must not receive verifier labels or geometry scores
- Docker-generated outputs only for paper-result promotion
