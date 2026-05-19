# Open3DSG Failure-Analysis Row Generator

Status: `failure_analysis_real_ready`
Created at: `2026-05-18T09:16:48+00:00`
Mode: `runtime_generation`

## Scope

This validates the row-generation contract against the locked Open3DSG failure-analysis schema.
Rows are generated from real Open3DSG prediction, GT, geometry, and metric artifacts.

## Summary

- rows: `57736`
- metric eligible rows: `57736`
- visual audit queue rows: `6162`

## Primary Categories

- `geometry_contradiction`: 979
- `insufficient_geometry_evidence`: 20828
- `predicate_family_ambiguity`: 1727
- `rank_only_failure`: 433
- `semantic_and_geometry_failure`: 5183
- `semantic_false_positive`: 27326
- `true_positive_supported`: 1260

## Outputs

- `rows_jsonl`: `experiments/H001_geom_reliability/sources/open3dsg/failure_rows/rows.jsonl`
- `summary_json`: `experiments/H001_geom_reliability/sources/open3dsg/failure_rows/summary.json`
- `manifest_json`: `experiments/H001_geom_reliability/sources/open3dsg/failure_rows/manifest.json`
- `report_md`: `experiments/H001_geom_reliability/sources/open3dsg/failure_rows/report.md`

## Claim Boundary

These rows are diagnostic evidence from reproduced Open3DSG outputs. They support failure taxonomy and qualitative sampling, not a broader claim beyond the measured H001-family metric scope.
