# H002 Source Reranking Bootstrap CI

This run bootstraps over `(source_id, subgraph_id, route_family)` units for the frozen primary-family validation source-reranking result.

## Scope

- Scores: `S0_source_score`, `S1_Ce_only`, `S2_source_x_Ce`, controls, `A1_source_x_G_only`, `A2_source_x_TG_concat`
- Families: `relative_vertical`, `size_relative`
- Metrics: `Recall@K`, `Violation@K`, `S2-S0`, `S2-A1`, `S2-A2`, and control deltas
- Bootstrap samples: `1000`
- Unit count: `2192`

## Boundary

No model fitting, score normalization tuning, threshold tuning, or family selection is performed in this script.
