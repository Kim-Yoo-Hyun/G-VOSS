# Open3DSG Docker Reproduction Commands

Run from the repository root.

Build the reproduction image:

```bash
sg docker -c 'docker compose -f experiments/H001_geom_reliability/sources/open3dsg/compose.open3dsg.yaml build'
```

Environment import/GPU check:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/sources/open3dsg/compose.open3dsg.yaml run --rm env_check'
```

Model/cache preflight:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/sources/open3dsg/compose.open3dsg.yaml run --rm cache_preflight'
```

Do not run `dump_features_3rscan`, `train_pilot`, or `train_full` until `local_dataset/Open3DSG_staged/training_repro/` has full official train payload, train views, and an explicit preprocessed-ready runtime train split.
The compose commands enforce this with `open3dsg_training_preflight.py`.
`dump_features_3rscan` currently defaults to lazy dataset loading, pre-forward skip-existing resume, no-grad feature dumping, deterministic no-shuffle feature iteration, explicit `--epochs 1`, `workers=0`, and `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True` because full preload, worker shm, repeated forward on already-dumped rows, and gradient graph paths are not viable in the current Docker runtime.

Stage `training_repro` metadata and scan symlinks from the top-level H001 compose file:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm open3dsg_train_root'
```

Train view/preprocess staging:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/sources/open3dsg/compose.open3dsg.yaml run --rm train_views_audit'
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/sources/open3dsg/compose.open3dsg.yaml run --rm train_views_smoke'
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/sources/open3dsg/compose.open3dsg.yaml run --rm train_preprocess_smoke'
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/sources/open3dsg/compose.open3dsg.yaml run --rm train_views_full'
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/sources/open3dsg/compose.open3dsg.yaml run --rm train_preprocess_full'
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/sources/open3dsg/compose.open3dsg.yaml run --rm train_preprocess_filter'
```

Validation view/preprocess staging:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/sources/open3dsg/compose.open3dsg.yaml run --rm validation_views_audit'
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/sources/open3dsg/compose.open3dsg.yaml run --rm validation_views_full'
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/sources/open3dsg/compose.open3dsg.yaml run --rm validation_preprocess_audit'
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/sources/open3dsg/compose.open3dsg.yaml run --rm validation_preprocess_full'
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/sources/open3dsg/compose.open3dsg.yaml run --rm validation_preprocess_filter'
```

Feature dump audit after `dump_features_3rscan` completes:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/sources/open3dsg/compose.open3dsg.yaml run --rm feature_audit'
```

Reduced/pilot-only feature dump route for checkpoint smoke when the official BLIP TopK5/scales3 route is too slow. This is not paper-result evidence:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/sources/open3dsg/compose.open3dsg.yaml run --rm dump_features_3rscan_pilot'
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/sources/open3dsg/compose.open3dsg.yaml run --rm feature_audit_pilot'
```

Pilot command after official feature dump pass:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/sources/open3dsg/compose.open3dsg.yaml run --rm train_pilot'
```

Reduced checkpoint-smoke command after reduced/pilot feature dump pass. This is not paper-result evidence:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/sources/open3dsg/compose.open3dsg.yaml run --rm train_pilot_reduced'
```

Full training command after pilot checkpoint:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/sources/open3dsg/compose.open3dsg.yaml run --rm train_full'
```

H001 eval command after checkpoint:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) OPEN3DSG_CHECKPOINT=/workspace/local_dataset/Open3DSG_staged/training_repro/output/checkpoints/<checkpoint>.ckpt docker compose -f experiments/H001_geom_reliability/sources/open3dsg/compose.open3dsg.yaml run --rm eval_preflight'
```

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) OPEN3DSG_CHECKPOINT=/workspace/local_dataset/Open3DSG_staged/training_repro/output/checkpoints/<checkpoint>.ckpt docker compose -f experiments/H001_geom_reliability/sources/open3dsg/compose.open3dsg.yaml run --rm eval_h001_gt_objects'
```

`eval_h001_gt_objects` is protected by `open3dsg_eval_preflight.py` and stops before Open3DSG execution if checkpoint/runtime/scope/import gates fail.
