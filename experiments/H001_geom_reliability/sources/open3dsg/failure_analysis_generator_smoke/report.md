# Open3DSG Failure-Analysis Row Generator

Status: `failure_analysis_generator_smoke_ready_no_metric_inspection`
Created at: `2026-05-09T14:26:49+00:00`
Mode: `synthetic_smoke`

## Scope

This validates the row-generation contract against the locked Open3DSG failure-analysis schema.
Rows are synthetic smoke fixtures only and must not be used as metric evidence.
The generator does not inspect Open3DSG metric failures.

## Summary

- rows: `6`
- metric eligible rows: `4`
- visual audit queue rows: `1`

## Primary Categories

- `adapter_or_identity_error`: 1
- `predicate_family_ambiguity`: 1
- `rank_only_failure`: 1
- `semantic_and_geometry_failure`: 1
- `true_positive_supported`: 1
- `unsupported_family_out_of_scope`: 1

## Outputs

- `rows_jsonl`: `experiments/H001_geom_reliability/sources/open3dsg/failure_analysis_generator_smoke/rows.jsonl`
- `summary_json`: `experiments/H001_geom_reliability/sources/open3dsg/failure_analysis_generator_smoke/summary.json`
- `manifest_json`: `experiments/H001_geom_reliability/sources/open3dsg/failure_analysis_generator_smoke/manifest.json`
- `report_md`: `experiments/H001_geom_reliability/sources/open3dsg/failure_analysis_generator_smoke/report.md`

## Claim Boundary

These rows are contract/implementation smoke evidence only until regenerated from a reproduced Open3DSG checkpoint, identity-preserving raw dump, H001 prediction JSONL, geometry join, and metric run.
