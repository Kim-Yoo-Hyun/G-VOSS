# Route Schema Audit

## Role

Audits early route-level materialization for schema violations, blocked field
leakage, shortcut risk, and split readiness.

## Latest Outputs

```text
latest/audit_manifest.json
latest/block_presence_table.csv
latest/blocked_field_hits.jsonl
latest/high_shortcut_warnings.jsonl
latest/shortcut_risk_table.csv
latest/split_readiness_table.csv
```

## Paper Status

Historical/internal guardrail. The paper-facing source-reranking audit is
`source_reranking_schema_audit/latest/`.
