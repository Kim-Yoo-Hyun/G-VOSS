# Source Reranking CI

## Role

This folder owns bootstrap confidence intervals for the frozen H002
source-reranking validation result.

It is generated from:

```text
source_reranking_evaluation/latest/selected_predictions.jsonl
source_reranking_materialization/latest/hidden_metric_manifest.jsonl
```

and does not fit, tune, threshold, or change any H002 score.

Those two row-level inputs are regenerable and are not retained in the compact
workspace. The CI tables below are the retained outputs.

## Latest Outputs

```text
latest/main_reranking_ci.csv
latest/main_reranking_delta_ci.csv
latest/familywise_reranking_ci.csv
latest/familywise_reranking_delta_ci.csv
latest/point_validation.csv
latest/report.md
latest/summary.json
latest/validation_errors.jsonl
```

## Current Status

```text
status = h002_source_reranking_bootstrap_ci_ready
n_bootstrap = 1000
bootstrap_unit = source_id/subgraph_id/route_family
unit_count = 2192
point_metric_mismatch_count = 0
validation_errors = 0
score_ids = S0_source_score,S1_Ce_only,S2_source_x_Ce,C1_source_x_shuffled_Ce,C2_source_x_wrong_T_Ce,A1_source_x_G_only,A2_source_x_TG_concat
delta_baselines = S0_source_score,A1_source_x_G_only,A2_source_x_TG_concat,C1_source_x_shuffled_Ce,C2_source_x_wrong_T_Ce,S1_Ce_only
familywise_unit_scopes = 4
```

## Boundary

This is a validation-level uncertainty analysis for `S0_source_score`,
`S2_source_x_Ce`, the `A1/A2` ablations, and controls. It is not an
official-test benchmark and does not create a SOTA or leaderboard claim.
