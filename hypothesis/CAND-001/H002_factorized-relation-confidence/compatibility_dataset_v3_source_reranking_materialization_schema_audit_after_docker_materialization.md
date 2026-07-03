# Source Reranking Materialization Schema Audit

## Status

```text
runtime_root = experiments/H002_compatibility_routing/source_reranking_schema_audit/latest/
artifact_root = artifacts/compatibility_dataset_v3_source_reranking_materialization_schema_audit_after_docker_materialization/
status = h002_source_reranking_materialization_schema_audit_after_docker_materialization_ready
selected_path = source_reranking_schema_audit_passed_select_metric_protocol_freeze
validation_errors = 0
next_todo = compatibility_dataset_v3_source_reranking_metric_protocol_freeze_after_schema_audit
```

## Purpose

Source-wide Docker materialization 이후, source reranking metric freeze로 넘어가기 전에
`model_safe_ce_view`, `source_rank_view`, and `hidden_metric_manifest`가 제대로 분리됐는지
감사했다.

이 단계에서도 metric을 실행하지 않았다. Official test도 사용하지 않았다.

## Result

Runtime audit:

```bash
HOST_UID=$(id -u) HOST_GID=$(id -g) docker compose -f configs/h002/compose.yaml run --rm h002-source-rerank-schema-audit
```

Key checks:

| Check | Result |
| --- | --- |
| candidate-id alignment | pass |
| `C_e` feature blocks are `T_e + G_e` only | pass |
| blocked `C_e` feature absence | pass |
| `source_rank_view` owns `Z_e` | pass |
| hidden manifest is metric-only | pass |
| geometry-only view is `G_e` only | pass |

Primary success aggregation:

| Family | Rows | Role |
| --- | ---: | --- |
| `relative_vertical` | 127148 | primary success |
| `size_relative` | 127148 | primary success |
| `relative_horizontal` | 254296 | caveated separate table |
| `proximity` | 63574 | geometry-only control |
| `support_contact` | 190722 | diagnostic excluded |

Control readiness:

- `relative_vertical`: wrong-`T` and shuffled-`G` ready.
- `size_relative`: wrong-`T` and shuffled-`G` ready.
- `relative_horizontal`: controls ready, but caveated separate table.
- `proximity`: wrong-`T` not applicable because it is a single-predicate geometry-only control.
- `support_contact`: controls ready but success aggregation excluded.

## Boundary

- Source reranking metric was not run.
- `Recall@K` and `Violation@K` were not computed.
- Official test was not used.
- `support_contact` remains diagnostic-only.
- Next stage is metric protocol freeze, not metric execution.
