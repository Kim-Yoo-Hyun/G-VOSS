# Relative Lateral Dev Failure Diagnosis Commands

Run from repository root.

```bash
docker build -t h001-geom-reliability:latest -f experiments/H001_geom_reliability/Dockerfile .
env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm \
  relative_lateral_dev_failure_diagnosis
```

This reads `relative_lateral/train_dev_policy_lock/rows.jsonl` only. It does
not change policy, read source predictions, or compute source metrics.
