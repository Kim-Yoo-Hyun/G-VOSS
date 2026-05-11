# Open3DSG Checkpoint Selection Commands

Freeze or refresh the checkpoint selection template:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm open3dsg_checkpoint_selection'
```

Use this template after `train_pilot` or `train_full` creates checkpoints. The primary checkpoint must be recorded before any H001 held-out Open3DSG metric or failure inspection.
