# Source Reranking Schema Audit

## Role

Audits source-wide reranking materialization to confirm that C_e inputs, source
score, geometry-only diagnostic view, and hidden metric labels are separated.

## Latest Outputs

```text
latest/audit_manifest.json
latest/schema_separation_audit.csv
latest/blocked_field_hits.jsonl
latest/control_readiness.csv
latest/family_success_aggregation.csv
latest/metric_freeze_precondition.csv
latest/validation_errors.jsonl
```

## Paper Status

This is a required paper-facing guardrail before using `S2_source_x_Ce`.
