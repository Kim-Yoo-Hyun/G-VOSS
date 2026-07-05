# H002 Source Reranking Sensitivity

This folder stores Docker/runtime outputs for the H002 source-reranking
sensitivity run.

## Role

This is not the frozen main validation table. It checks two reviewer risks:

- whether `S2_source_x_Ce` depends on validation candidate-pool minmax
  normalization;
- whether the geometry-only ablation is explained by route-family one-hot
  features.

## Current Output

```text
latest/
```

Key files:

| File | Role |
| --- | --- |
| `summary.json` | runtime manifest, gate decision, row counts, score IDs |
| `aggregate_metrics.csv` | primary/all weighted Recall@K and Violation@K by score |
| `comparison_metrics.csv` | S2 vs sensitivity baselines |
| `source_family_metrics.csv` | source/family/K metrics |
| `score_manifest.json` | feature sets and normalization variants |
| `validation_errors.jsonl` | runtime validation errors; should be empty |

## Current Decision

```text
validation_errors = 0
source_rows_scored = 762888
no_route_g_only_sensitivity = passed
raw_source_x_Ce_direction = preserved_vs_S0_at_K_10_20_50
rankpct_normalization = violation_reduction_but_low_K_recall_loss
sensitivity_pass = false
```

Use this output as sensitivity/caveat evidence. Do not replace the main table
with it.
