# Same-Route Fusion Comparators

This evaluation compares the projected product, rank-average, reciprocal-rank
fusion, and the frozen train-only supervision-matched nonlinear compatibility
model under the same family-slot route. All methods preserve the source family
sequence, pass support/contact through in source order, use the official 548
3DSSG validation contexts, and share scan-cluster resampling indices.

Run with:

```bash
env UID=$(id -u) GID=$(id -g) \
  docker compose -f configs/h001/compose.structured.yaml run --rm \
  routed_comparator_evaluation
```

The frozen specification is `protocol.json`; paper-facing metrics and hashes
are written under `evaluation/`.
