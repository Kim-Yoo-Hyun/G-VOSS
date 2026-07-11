# Source Reranking Evaluation

## Role

Evaluates the paper-facing H002 reranking score:

```text
S2_source_x_Ce = normalized_source_score * C_e
```

against:

```text
S0_source_score
S1_Ce_only
C1_source_x_shuffled_Ce
C2_source_x_wrong_T_Ce
A1_source_x_G_only
A2_source_x_TG_concat
```

## Latest Outputs

```text
latest/metric_manifest.json
latest/score_manifest.json
latest/score_condition_metrics.csv
latest/absolute_primary_metrics.csv
latest/source_family_metrics.csv
latest/control_metrics.csv
latest/selected_predictions.jsonl
latest/validation_errors.jsonl
```

## Paper Status

This is the current validation-level custom-evaluation runtime output. Compact
metrics are retained; `selected_predictions.jsonl` is intentionally removed
after CI and qualitative artifacts are generated and can be regenerated. The
caption-ready table is materialized under
`../main_validation_table_refresh/latest/`.

The latest run includes ablation expansion scores:

```text
A1_source_x_G_only = normalized_source_score * G_only_score(G_e)
A2_source_x_TG_concat = normalized_source_score * C_concat(T_e,G_e)
```

Bootstrap confidence intervals for this frozen output live in:

```text
../source_reranking_ci/latest/
```
