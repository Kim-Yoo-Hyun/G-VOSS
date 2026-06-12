# Qwen-VL full official validation Failure-Analysis Row Generator

Status: `failure_analysis_real_ready`
Created at: `2026-06-11T18:18:05+00:00`
Mode: `runtime_generation`

## Scope

This validates the row-generation contract against the locked H001 failure-analysis schema for Qwen-VL full official validation.
Rows are generated from real Qwen-VL full official validation prediction, GT, geometry, and metric artifacts.

## Summary

- rows: `31881`
- metric eligible rows: `31881`
- visual audit queue rows: `3939`

## Primary Categories

- `geometry_contradiction`: 526
- `insufficient_geometry_evidence`: 7532
- `predicate_family_ambiguity`: 728
- `rank_only_failure`: 22
- `semantic_and_geometry_failure`: 3413
- `semantic_false_positive`: 18233
- `true_positive_supported`: 1427

## Outputs

- `rows_jsonl`: `experiments/H001_geom_reliability/sources/qwen_vl/full_validation/failure_rows/rows.jsonl`
- `summary_json`: `experiments/H001_geom_reliability/sources/qwen_vl/full_validation/failure_rows/summary.json`
- `manifest_json`: `experiments/H001_geom_reliability/sources/qwen_vl/full_validation/failure_rows/manifest.json`
- `report_md`: `experiments/H001_geom_reliability/sources/qwen_vl/full_validation/failure_rows/report.md`

## Claim Boundary

These rows are diagnostic evidence from reproduced Qwen-VL full official validation outputs. They support failure taxonomy and qualitative sampling, not a broader claim beyond the measured H001-family metric scope.
