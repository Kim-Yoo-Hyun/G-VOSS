# Route Materialization

## Role

Early internal route-level materialization for H002 candidate rows. This created
model-safe and hidden views before the official-validation and source-reranking
paths were finalized.

## Latest Outputs

```text
latest/route_rows.jsonl
latest/model_safe_view.jsonl
latest/hidden_manifest.jsonl
latest/row_manifest.json
latest/validation_errors.jsonl
```

## Paper Status

Historical/internal support artifact. The current paper-facing materialization is
`source_reranking_materialization/latest/`.
