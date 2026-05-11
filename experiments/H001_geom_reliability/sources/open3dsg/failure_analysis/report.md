# Open3DSG Failure-Analysis Schema

Status: `failure_analysis_schema_ready_no_metric_run`
Created at: `2026-05-08T07:29:22+00:00`

## Scope

This freezes the Open3DSG failure-analysis row contract before Open3DSG metric/failure inspection.
It does not run Open3DSG, inspect predictions, compute metrics, or assign real failure labels.

## Primary Categories

- `true_positive_supported`: Prediction exactly matches a GT relation and geometry is satisfied or non-contradictory.
- `semantic_false_positive`: Prediction is not supported by GT for the directed pair and geometry does not provide an independent contradiction.
- `geometry_contradiction`: Prediction is semantically plausible or high-ranked but violates frozen H001 geometry checks.
- `semantic_and_geometry_failure`: Prediction is unsupported by GT and also geometrically contradicted.
- `plausible_unlabeled`: Prediction lacks a GT label but geometry and visual/audit evidence suggest the relation may be valid.
- `predicate_family_ambiguity`: Prediction chooses a neighboring predicate in the same family where label granularity is ambiguous.
- `object_pair_mismatch`: Prediction targets the wrong directed object pair or object identity mapping is inconsistent.
- `insufficient_geometry_evidence`: Frozen geometry verifier cannot decide because required geometry evidence is missing or too weak.
- `preprocessing_or_filtering_limitation`: Row is affected by known Open3DSG preprocessing/view/filter limitations rather than model semantics.
- `unsupported_family_out_of_scope`: Predicate family is outside H001 geometry-checkable families.
- `rank_only_failure`: Correct relation exists but is ranked below the evaluated top-k cutoff.
- `model_score_calibration_failure`: Semantic score is poorly ordered relative to geometry/GT evidence without an identity or verifier error.
- `adapter_or_identity_error`: Failure comes from raw dump conversion, id mapping, duplicate rows, or schema violation.
- `unknown_needs_audit`: Available fields are insufficient to assign a stable category.

## Assignment Priority

Categories are assigned in this fixed priority order:

`adapter_or_identity_error`, `preprocessing_or_filtering_limitation`, `unsupported_family_out_of_scope`, `true_positive_supported`, `semantic_and_geometry_failure`, `geometry_contradiction`, `predicate_family_ambiguity`, `rank_only_failure`, `semantic_false_positive`, `insufficient_geometry_evidence`, `model_score_calibration_failure`, `plausible_unlabeled`, `object_pair_mismatch`, `unknown_needs_audit`

## Outputs

- `schema_json`: `experiments/H001_geom_reliability/sources/open3dsg/failure_analysis/schema.json`
- `taxonomy_json`: `experiments/H001_geom_reliability/sources/open3dsg/failure_analysis/taxonomy.json`
- `aggregation_plan_json`: `experiments/H001_geom_reliability/sources/open3dsg/failure_analysis/aggregation_plan.json`
- `example_jsonl`: `experiments/H001_geom_reliability/sources/open3dsg/failure_analysis/example.jsonl`
- `manifest`: `experiments/H001_geom_reliability/sources/open3dsg/failure_analysis/manifest.json`
- `report`: `experiments/H001_geom_reliability/sources/open3dsg/failure_analysis/report.md`

## Claim Boundary

Failure-analysis rows are diagnostic evidence only until generated from a reproduced Open3DSG checkpoint, identity-preserving raw dump, H001 prediction JSONL, geometry join, and metric run.
