# RelCompat3D Runtime Benchmark

This directory measures the CPU cost of the fixed compatibility layer and
family-aware ranking rule on the same candidate routes used by the main paper.
`protocol.json` freezes the measurement boundary; `evaluation/` contains the
Docker-generated summary and manifest.

Timing starts after verification rows and raw pair features are loaded. It
includes proximity/vertical compatibility, transformation averaging, family
queue sorting, and output assembly. Source-predictor inference, reconstruction,
geometry join, JSONL parsing, metrics, and bootstrap are excluded and must not
be attributed to the reported RelCompat3D overhead. Open3DSG timing covers its
533 nonempty public-prediction contexts; the 15 official empty contexts require
no method computation.

Run from the repository root:

```bash
env UID=$(id -u) GID=$(id -g) docker compose \
  -f configs/h001/compose.structured.yaml run --rm runtime_benchmark
```
