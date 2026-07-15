# Supervision-Matched Nonlinear Comparison

This experiment fits two 69-parameter source-excluded nonlinear compatibility
models on the same train-only constructed target used by RelCompat3D. The same
models are applied unchanged to VL-SAT, Open3DSG, and SGFN. Existing
SGFN-specific exact-label rescorer results are retained as a separate,
stronger-supervision comparator.

Run:

```bash
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.structured.yaml run --rm supervision_matched_nonlinear
```
