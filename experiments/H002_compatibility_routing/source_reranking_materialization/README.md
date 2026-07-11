# Source Reranking Materialization

## Role

Builds source-wide VL-SAT/Open3DSG validation rows for the final H002 reranking
experiment.

## Latest Outputs

```text
latest/model_safe_ce_view.jsonl
latest/model_safe_geometry_only_view.jsonl
latest/source_rank_view.jsonl
latest/hidden_metric_manifest.jsonl
latest/source_candidates.jsonl
latest/row_manifest.json
latest/validation_errors.jsonl
```

The five row-level JSONL files are large, deterministic runtime products and are
currently removed after compact metrics and qualitative cases are generated.
`row_manifest.json` and validation metadata are retained; rerun the materialize
service before downstream jobs that require row-level views.

## View Semantics

| View | Meaning |
| --- | --- |
| `model_safe_ce_view.jsonl` | `T_e + G_e` only; input for C_e |
| `model_safe_geometry_only_view.jsonl` | `G_e` only diagnostic view |
| `source_rank_view.jsonl` | `Z_e` source score/rank; final reranking only |
| `hidden_metric_manifest.jsonl` | GT and violation labels; metric-only |

## Paper Status

This is a reproducible paper-facing input stage, not a permanent row-level data
release.
