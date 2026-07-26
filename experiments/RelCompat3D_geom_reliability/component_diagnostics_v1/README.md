# Component Diagnostics

This frozen post-hoc analysis compares the promoted Linear and MLP estimators
with matched removal of the linked pairwise loss or inference-time
transformation averaging. It reports held-out linked-pair margins,
transformation-error distributions, transformed-view top-K membership
consistency, and all-K aggregate point estimates.

The protocol was fixed before the run. The analysis does not replace or
reselect the active method. Row-level inputs remain under the ignored
`local_dataset/` runtime root; compact outputs are stored in `evaluation/`.

```bash
env UID=$(id -u) GID=$(id -g) docker compose \
  -f configs/relcompat3d/compose.structured.yaml run --rm \
  relcompat3d_component_diagnostics
```
