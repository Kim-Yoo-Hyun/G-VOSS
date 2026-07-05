# H002 R1 Close-By Geometry-Support Route Materialization After Plan

Date: 2026-06-30 KST

## Status

```text
artifact_root = artifacts/route_specific_targets/r1_proximity/
status = h002_compatibility_dataset_v3_close_by_geometry_support_route_materialization_after_plan_ready
selected_path = materialized_r1_close_by_geometry_support_route_root
validation_errors = 0
next_todo = compatibility_dataset_v3_close_by_geometry_support_schema_audit_after_materialization
```

## Purpose

This step materializes the R1 route-specific root for `close by`.

The old close-by rows are not treated as predicate-geometry interaction evidence.
They are normalized into a `geometry_support` route where `G_e` is the primary
route evidence and `C_e` interaction is explicitly not applicable.

## Output Root

```text
artifacts/route_specific_targets/r1_proximity/
```

Required files are present:

- `summary.json`
- `schema.json`
- `model_safe_rows.jsonl`
- `hidden_manifest.jsonl`
- `audit_view.jsonl`
- `control_manifest.json`
- `split_or_group_manifest.json`
- `report.md`
- `validation_errors.jsonl`

Additional diagnostics:

- `row_counts.csv`
- `label_counts.csv`

## Row Counts

| Component | Rows |
| --- | ---: |
| total | 1,284 |
| primary geometry-support binary | 800 |
| Q_e / abstain diagnostics | 240 |
| raw-distance diagnostic | 240 |
| GT/geometry conflict audit | 4 |

Primary binary labels:

```text
geometry_supported = 400
geometry_unsupported = 400
```

All geometry-support labels including diagnostics:

```text
geometry_supported = 520
geometry_unsupported = 520
abstain = 240
audit_required = 4
```

## Field Conversion

Old field:

```text
C_e_label
```

New route-specific field:

```text
geometry_support_label
geometry_support_binary
c_e_interaction_label = not_applicable
```

This preserves the H002 boundary:

- `close by` is geometry-only route evidence.
- It is not `T_e x G_e` interaction evidence.
- `T_e` and `Z_e` are retained only for annotation/source baselines.
- `Q_e` is retained for coverage/abstain diagnostics.

## Boundary

- Train-only route materialization.
- No validation/test used.
- No model run.
- No paper-level claim.
- H001 artifacts were not modified.

## Next

```text
compatibility_dataset_v3_close_by_geometry_support_schema_audit_after_materialization
```
