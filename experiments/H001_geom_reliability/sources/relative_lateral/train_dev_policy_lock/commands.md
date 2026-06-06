# Relative Lateral Train/Dev Policy Lock Commands

Run from repository root.

```bash
docker build -t h001-geom-reliability:latest -f experiments/H001_geom_reliability/Dockerfile .
env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm \
  relative_lateral_train_dev_policy_lock
```

This uses train/dev GT positives and left/right label-flip counterfactuals only.
It does not read VL-SAT/Open3DSG predictions and does not update the paper
claim.
