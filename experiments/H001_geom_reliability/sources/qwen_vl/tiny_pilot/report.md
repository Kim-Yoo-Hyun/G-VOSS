# Qwen-VL Tiny Pilot Scope

Status: `tiny_pilot_scope_ready_no_model_runtime`
Created at: `2026-05-08T06:30:16+00:00`

## Scope

This freezes a non-held-out tiny pilot input scope for Qwen-VL prompt/parser runtime smoke.
It does not download a Qwen model, run inference, render pair crops, or create metric evidence.

## Counts

- input rows: `30`
- scans: `12`
- subgraphs: `18`
- held-out overlaps: `0`

## Family Counts

- `proximity`: `10`
- `relative_vertical`: `10`
- `support_contact`: `10`

## Outputs

- `input_jsonl`: `experiments/H001_geom_reliability/sources/qwen_vl/tiny_pilot/input.jsonl`
- `selection_jsonl`: `experiments/H001_geom_reliability/sources/qwen_vl/tiny_pilot/selection.jsonl`
- `raw_response_template_jsonl`: `experiments/H001_geom_reliability/sources/qwen_vl/tiny_pilot/raw_response_template.jsonl`
- `scans_txt`: `experiments/H001_geom_reliability/sources/qwen_vl/tiny_pilot/scans.txt`
- `manifest`: `experiments/H001_geom_reliability/sources/qwen_vl/tiny_pilot/manifest.json`
- `report`: `experiments/H001_geom_reliability/sources/qwen_vl/tiny_pilot/report.md`

## Claim Boundary

This artifact is only a pilot scope contract. It is not Qwen-VL performance evidence and must not be used in paper metrics.
