# Open3DSG Metric Scope Commands

Freeze or refresh the predicate-family mapping and denominator policy:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm open3dsg_metric_scope'
```

Run this before real Open3DSG metric execution. Metric code must not change predicate-family mapping or denominator caveats after prediction/failure inspection.
