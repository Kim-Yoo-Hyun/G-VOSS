# Compatibility Dataset V3 Materialization Schema Audit After Docker Materialization

## Status

```text
artifact_root = artifacts/compatibility_dataset_v3_materialization_schema_audit_after_docker_materialization/
status = h002_compatibility_dataset_v3_materialization_schema_audit_after_docker_materialization_ready
selected_path = schema_audit_passed_select_grouped_split_protocol
validation_errors = 0
next_todo = compatibility_dataset_v3_grouped_split_protocol_after_materialization_schema_audit
```

## Purpose

This stage audits the Docker-materialized H002 route rows before any grouped evaluation.

Implemented files:

- `experiments/H002_compatibility_routing/scripts/audit_materialization_schema.py`
- `configs/h002/compose.yaml` service `h002-materialization-schema-audit`
- `tools/compatibility_dataset_v3_materialization_schema_audit_after_docker_materialization.py`

Executed command:

```bash
HOST_UID=$(id -u) HOST_GID=$(id -g) docker compose -f configs/h002/compose.yaml run --rm h002-materialization-schema-audit
```

## Runtime Outputs

```text
experiments/H002_compatibility_routing/schema_audit/latest/audit_manifest.json
experiments/H002_compatibility_routing/schema_audit/latest/schema_violations.jsonl
experiments/H002_compatibility_routing/schema_audit/latest/blocked_field_hits.jsonl
experiments/H002_compatibility_routing/schema_audit/latest/high_shortcut_warnings.jsonl
experiments/H002_compatibility_routing/schema_audit/latest/shortcut_risk_table.csv
experiments/H002_compatibility_routing/schema_audit/latest/split_readiness_table.csv
```

## Audit Result

| Check | Count |
| --- | ---: |
| schema errors | 0 |
| blocked `C_e` field hits in `T_e + G_e` | 0 |
| high-risk `C_e` allowed shortcut warnings | 0 |
| shortcut probes | 50 |
| split-readiness families | 4 |

## Split Readiness

| Route family | Rows | CV groups | Mixed-label groups | Split ready |
| --- | ---: | ---: | ---: | --- |
| `relative_vertical` | 1512 | 1026 | 486 | `True` |
| `size_relative` | 2400 | 1200 | 1200 | `True` |
| `relative_horizontal` | 2400 | 1200 | 1200 | `True` |
| `support_contact` | 640 | 258 | 155 | `True` |

## Boundary

- This stage is schema/leakage/split-readiness audit only.
- No grouped-holdout metric was run.
- No official validation/test was used.
- No paper-level H002 metric was produced.
- `C_e` remains restricted to `T_e + G_e`.
- `Z_e` and `Q_e` remain blocked from `C_e` unless a later protocol explicitly changes the input contract.

## Next

```text
compatibility_dataset_v3_grouped_split_protocol_after_materialization_schema_audit
```

The next stage should create a grouped split protocol over the materialized H002 candidate pool using `cv_group_id`, then validate row/id leakage and family-label balance before any learned metric run.
