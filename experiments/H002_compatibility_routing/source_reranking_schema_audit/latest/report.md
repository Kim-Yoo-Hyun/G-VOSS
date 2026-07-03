# Source Reranking Materialization Schema Audit

## Status

```text
status = h002_source_reranking_materialization_schema_audit_ready
selected_path = source_reranking_materialization_schema_audit_passed_select_metric_protocol_freeze
validation_errors = 0
next_todo = compatibility_dataset_v3_source_reranking_metric_protocol_freeze_after_schema_audit
```

## Result

The source-reranking materialization schema audit passed.

- total rows: `762888`
- source reranking metrics run: `false`
- official test usage: `false`
- model-safe C_e view: `T_e + G_e` only
- source rank view: `Z_e` reranking-only
- hidden manifest: GT/violation metric-only

The next stage is source-reranking metric protocol freeze, not metric execution.
