# VL-SAT full-validation Failure-Analysis Row Generator

Status: `failure_analysis_real_ready`
Created at: `2026-06-05T01:25:21+00:00`
Mode: `runtime_generation`

## Scope

This validates the row-generation contract against the locked H001 failure-analysis schema for VL-SAT full-validation.
Rows are generated from real VL-SAT full-validation prediction, GT, geometry, and metric artifacts.

## Summary

- rows: `59841`
- metric eligible rows: `59841`
- visual audit queue rows: `2897`

## Primary Categories

- `geometry_contradiction`: 516
- `insufficient_geometry_evidence`: 19702
- `predicate_family_ambiguity`: 2781
- `rank_only_failure`: 23
- `semantic_and_geometry_failure`: 2381
- `semantic_false_positive`: 30624
- `true_positive_supported`: 3814

## Outputs

- `rows_jsonl`: `experiments/H001_geom_reliability/sources/vlsat/full_validation/failure_rows/rows.jsonl`
- `summary_json`: `experiments/H001_geom_reliability/sources/vlsat/full_validation/failure_rows/summary.json`
- `manifest_json`: `experiments/H001_geom_reliability/sources/vlsat/full_validation/failure_rows/manifest.json`
- `report_md`: `experiments/H001_geom_reliability/sources/vlsat/full_validation/failure_rows/report.md`

## Claim Boundary

These rows are diagnostic evidence from reproduced VL-SAT full-validation outputs. They support failure taxonomy and qualitative sampling, not a broader claim beyond the measured H001-family metric scope.
