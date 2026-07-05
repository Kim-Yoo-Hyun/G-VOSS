# Compatibility Dataset V3 Route Materialization Protocol Implementation After Docker Preflight

## Status

```text
artifact_root = artifacts/compatibility_dataset_v3_route_materialization_protocol_implementation_after_docker_preflight/
status = h002_compatibility_dataset_v3_route_materialization_protocol_implementation_after_docker_preflight_ready
selected_path = docker_materialized_promoted_routes_select_materialization_schema_shortcut_audit
validation_errors = 0
next_todo = compatibility_dataset_v3_materialization_schema_audit_after_docker_materialization
```

## Purpose

This stage implements and runs Docker route materialization for the promoted H002 candidate routes.

Implemented files:

- `experiments/H002_compatibility_routing/scripts/materialize_routes.py`
- `configs/h002/compose.yaml` service `h002-materialize-routes`
- `tools/compatibility_dataset_v3_route_materialization_protocol_implementation_after_docker_preflight.py`

Executed command:

```bash
HOST_UID=$(id -u) HOST_GID=$(id -g) docker compose -f configs/h002/compose.yaml run --rm h002-materialize-routes
```

## Runtime Outputs

```text
experiments/H002_compatibility_routing/materialization/latest/route_rows.jsonl
experiments/H002_compatibility_routing/materialization/latest/model_safe_view.jsonl
experiments/H002_compatibility_routing/materialization/latest/hidden_manifest.jsonl
experiments/H002_compatibility_routing/materialization/latest/row_manifest.json
experiments/H002_compatibility_routing/materialization/latest/validation_errors.jsonl
```

## Counts

| Route family | Rows | Label 0 | Label 1 |
| --- | ---: | ---: | ---: |
| `relative_vertical` | 1512 | 756 | 756 |
| `size_relative` | 2400 | 1200 | 1200 |
| `relative_horizontal` | 2400 | 1200 | 1200 |
| `support_contact` | 640 | 320 | 320 |

Total rows:

```text
route_rows = 6952
model_safe_view = 6952
hidden_manifest = 6952
validation_errors = 0
```

## Predicates

| Route family | Predicates |
| --- | --- |
| `relative_vertical` | `higher than`, `lower than` |
| `size_relative` | `bigger than`, `smaller than` |
| `relative_horizontal` | `left`, `right`, `front`, `behind` |
| `support_contact` | `standing on`, `lying on` |

## Feature Boundary

The materialized model-safe view normalizes factor blocks as:

```text
T_e = semantic content
G_e = geometry-only evidence
Q_e = observability / evidence quality
Z_e = source confidence
```

For the next `C_e` compatibility audit, the allowed input contract is:

```text
C_e allowed blocks = T_e + G_e
C_e blocked blocks = Z_e + Q_e + extra_safe_blocks
```

`Q_e` and `Z_e` remain stored for later `p_obs` / `p_rel` protocol decisions, but they are not allowed to leak into the next compatibility-head audit.

## Boundary

- Route materialization was run inside Docker.
- No grouped-holdout metric was run.
- No official validation/test was used.
- No paper-level H002 metric was produced.
- H001 artifacts remained read-only references.
- `protocol_split` remains `unassigned_pre_grouped_holdout`.

## Next

```text
compatibility_dataset_v3_materialization_schema_audit_after_docker_materialization
```

The next stage must audit the materialized `model_safe_view` for blocked-field leakage, schema consistency, family/predicate shortcut risk, and split-readiness before any grouped metric or learned evaluation.
