# Open3DSG Metric/Join Contract Commands

Run from the repository root.

## Contract / Blocked-Input Preflight

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm open3dsg_metric_join_contract'
```

## Real Runtime Inputs Required Later

- `experiments/H001_geom_reliability/sources/open3dsg/adapter/predictions.jsonl`
- `hypothesis/CAND-001/H001_geometry-grounded-verification/artifacts/evaluation/vlsat_closed_set/hardened/ground_truth.jsonl`
- `experiments/H001_geom_reliability/sources/open3dsg/geometry/verification.jsonl`

Do not promote this contract output to paper-result evidence.
