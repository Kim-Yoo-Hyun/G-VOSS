# H002 Docker Commands

Run from the repository root.

## Internal Compatibility

```bash
docker compose -f configs/h002/compose.yaml run --rm h002-protocol-check
docker compose -f configs/h002/compose.yaml run --rm h002-materialize-routes
docker compose -f configs/h002/compose.yaml run --rm h002-materialization-schema-audit
docker compose -f configs/h002/compose.yaml run --rm h002-grouped-split
docker compose -f configs/h002/compose.yaml run --rm h002-grouped-eval
```

## Source Reranking

```bash
docker compose -f configs/h002/compose.yaml run --rm h002-source-rerank-materialize
docker compose -f configs/h002/compose.yaml run --rm h002-source-rerank-schema-audit
docker compose -f configs/h002/compose.yaml run --rm h002-source-rerank-metric-runner
docker compose -f configs/h002/compose.yaml run --rm h002-source-rerank-bootstrap-ci
docker compose -f configs/h002/compose.yaml run --rm h002-source-rerank-sensitivity
```

## Lateral Route

```bash
docker compose -f configs/h002/compose.yaml run --rm h002-relative-horizontal-frame-audit
docker compose -f configs/h002/compose.yaml run --rm h002-relative-horizontal-route-scorer
docker compose -f configs/h002/compose.yaml run --rm h002-relative-horizontal-split-route-scorer
```

## Tables And Figures

```bash
docker compose -f configs/h002/compose.yaml run --rm h002-main-validation-table-refresh
docker compose -f configs/h002/compose.yaml run --rm h002-qualitative-evidence-package
docker compose -f configs/h002/compose.yaml run --rm h002-paper-strengthening-assets
```

The qualitative service requires regenerated
`source_reranking_evaluation/latest/selected_predictions.jsonl` and
`relative_horizontal_split_route_scorer/latest/selected_predictions.jsonl`.
These large files are removed after compact qualitative assets are produced.

## Validation

```bash
docker compose -f configs/h002/compose.yaml config --services
python -m compileall -q experiments/H002_compatibility_routing/scripts
```
