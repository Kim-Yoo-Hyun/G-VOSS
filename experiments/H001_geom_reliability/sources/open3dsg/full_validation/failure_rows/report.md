# Open3DSG Failure-Analysis Row Generator

Status: `failure_analysis_real_ready`
Created at: `2026-06-04T14:23:35+00:00`
Mode: `runtime_generation`

## Scope

This validates the row-generation contract against the locked Open3DSG failure-analysis schema.
Rows are generated from real Open3DSG prediction, GT, geometry, and metric artifacts.

## Summary

- rows: `81448`
- metric eligible rows: `81448`
- visual audit queue rows: `8739`

## Primary Categories

- `geometry_contradiction`: 1461
- `insufficient_geometry_evidence`: 29329
- `predicate_family_ambiguity`: 2635
- `rank_only_failure`: 615
- `semantic_and_geometry_failure`: 7278
- `semantic_false_positive`: 38105
- `true_positive_supported`: 2025

## Outputs

- `rows_jsonl`: `experiments/H001_geom_reliability/sources/open3dsg/full_validation/failure_rows/rows.jsonl`
- `summary_json`: `experiments/H001_geom_reliability/sources/open3dsg/full_validation/failure_rows/summary.json`
- `manifest_json`: `experiments/H001_geom_reliability/sources/open3dsg/full_validation/failure_rows/manifest.json`
- `report_md`: `experiments/H001_geom_reliability/sources/open3dsg/full_validation/failure_rows/report.md`

## Claim Boundary

These rows are diagnostic evidence from reproduced Open3DSG outputs. They support failure taxonomy and qualitative sampling, not a broader claim beyond the measured H001-family metric scope.
