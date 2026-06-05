# Open3DSG recovery full-validation Failure-Analysis Row Generator

Status: `failure_analysis_real_ready`
Created at: `2026-06-05T01:25:21+00:00`
Mode: `runtime_generation`

## Scope

This validates the row-generation contract against the locked H001 failure-analysis schema for Open3DSG recovery full-validation.
Rows are generated from real Open3DSG recovery full-validation prediction, GT, geometry, and metric artifacts.

## Summary

- rows: `82155`
- metric eligible rows: `82155`
- visual audit queue rows: `8821`

## Primary Categories

- `geometry_contradiction`: 1469
- `insufficient_geometry_evidence`: 29619
- `predicate_family_ambiguity`: 2665
- `rank_only_failure`: 615
- `semantic_and_geometry_failure`: 7352
- `semantic_false_positive`: 38390
- `true_positive_supported`: 2045

## Outputs

- `rows_jsonl`: `experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2/failure_rows/rows.jsonl`
- `summary_json`: `experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2/failure_rows/summary.json`
- `manifest_json`: `experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2/failure_rows/manifest.json`
- `report_md`: `experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2/failure_rows/report.md`

## Claim Boundary

These rows are diagnostic evidence from reproduced Open3DSG recovery full-validation outputs. They support failure taxonomy and qualitative sampling, not a broader claim beyond the measured H001-family metric scope.
