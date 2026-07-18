# Superseded Recovered-Route Runtime Diagnostic

This prepublication diagnostic used the recovered Open3DSG coverage path and
is not a paper result. The active benchmark is
`experiments/H001_geom_reliability/runtime_v1/`, which uses the same public
candidate route as the main paper.

This directory measures the CPU cost of the fixed compatibility layer and
family-aware ranking rule. `protocol.json` freezes the measurement boundary;
`evaluation/` contains the Docker-generated summary and manifest.

Timing starts after verification rows and raw pair features are loaded. It
includes proximity/vertical compatibility, transformation averaging, family
queue sorting, and output assembly. Source-predictor inference, reconstruction,
geometry join, JSONL parsing, metrics, and bootstrap are intentionally excluded
and must not be attributed to the reported RelCompat3D overhead.

Run from the repository root:

```bash
env UID=$(id -u) GID=$(id -g) docker compose \
  -f configs/h001/compose.structured.yaml run --rm runtime_benchmark
```
