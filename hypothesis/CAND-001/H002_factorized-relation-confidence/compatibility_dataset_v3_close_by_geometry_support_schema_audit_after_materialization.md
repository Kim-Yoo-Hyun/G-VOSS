# H002 R1 Close-By Geometry-Support Schema Audit After Materialization

Date: 2026-06-30 KST

## Status

```text
artifact_root = artifacts/compatibility_dataset_v3_close_by_geometry_support_schema_audit_after_materialization/
status = h002_compatibility_dataset_v3_close_by_geometry_support_schema_audit_after_materialization_ready
selected_path = r1_close_by_schema_pass_select_geometry_route_control_runner_plan
validation_errors = 0
passed_checks = 75
total_checks = 75
next_todo = compatibility_dataset_v3_close_by_geometry_support_route_control_runner_plan
```

## Purpose

This step audits the materialized R1 `close by` route root before any route-level
runner. The audit treats distance dominance as expected behavior for a
geometry-only route, not as a failure.

The failure conditions are:

- hidden construction field leakage into model-safe features;
- legacy `C_e_label` leakage;
- label imbalance;
- missing distance / scale / coverage controls;
- wording drift that presents `close by` as `T_e x G_e` interaction evidence.

## Result

All checks passed.

```text
checks = 75 / 75
validation_errors = 0
```

Key passed checks:

- required route files present;
- route contract and `target_axis=geometry_support` preserved;
- row count and route-row-id consistency passed;
- primary label balance passed: `400/400`;
- legacy `C_e_label` absent from `model_safe_rows.jsonl`;
- blocked hidden/construction fields absent from model-safe feature blocks;
- `c_e_interaction_label=not_applicable` for all 1,284 rows;
- distance / scale / coverage controls ready;
- wording guard passed.

## Gate Decision

Allowed next:

```text
compatibility_dataset_v3_close_by_geometry_support_route_control_runner_plan
```

Still blocked:

- learned interaction smoke for R1;
- paper-level claim from R1 alone;
- any claim that `close by` proves `T_e x G_e` interaction.

## Boundary

- Train-only audit.
- No validation/test used.
- No model run.
- No H001 artifact modified.

