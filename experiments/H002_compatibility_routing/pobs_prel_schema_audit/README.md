# p_obs / p_rel Schema Audit

## Role

This folder owns leakage and schema checks for the H002 p_obs / p_rel
materialization.

The audit verifies:

- `model_safe_qe_view.jsonl` exposes only `Q_e`.
- `model_safe_prel_view.jsonl` keeps `T_e`, `G_e`, `Q_e`, and `Z_e` separate.
- hidden selective labels are not present in model-safe views.
- candidate ids align across all p_obs / p_rel materialized files.

## Current Output

```text
latest/summary.json
latest/schema_separation_audit.csv
latest/label_balance.csv
latest/blocked_field_hits.jsonl
latest/validation_errors.jsonl
```

## Boundary

A passing schema audit only means the materialized files are safe to evaluate.
It does not by itself validate the scientific claim.
