# Qwen-VL full-source Failure-Analysis Row Generator

Status: `failure_analysis_real_ready`
Created at: `2026-06-11T03:01:09+00:00`
Mode: `runtime_generation`

## Scope

This validates the row-generation contract against the locked H001 failure-analysis schema for Qwen-VL full-source.
Rows are generated from real Qwen-VL full-source prediction, GT, geometry, and metric artifacts.

## Summary

- rows: `22787`
- metric eligible rows: `22787`
- visual audit queue rows: `2843`

## Primary Categories

- `geometry_contradiction`: 353
- `insufficient_geometry_evidence`: 5322
- `predicate_family_ambiguity`: 480
- `rank_only_failure`: 20
- `semantic_and_geometry_failure`: 2490
- `semantic_false_positive`: 13212
- `true_positive_supported`: 910

## Outputs

- `rows_jsonl`: `experiments/H001_geom_reliability/sources/qwen_vl/failure_rows/rows.jsonl`
- `summary_json`: `experiments/H001_geom_reliability/sources/qwen_vl/failure_rows/summary.json`
- `manifest_json`: `experiments/H001_geom_reliability/sources/qwen_vl/failure_rows/manifest.json`
- `report_md`: `experiments/H001_geom_reliability/sources/qwen_vl/failure_rows/report.md`

## Claim Boundary

These rows are diagnostic evidence from reproduced Qwen-VL full-source outputs. They support failure taxonomy and qualitative sampling, not a broader claim beyond the measured H001-family metric scope.
