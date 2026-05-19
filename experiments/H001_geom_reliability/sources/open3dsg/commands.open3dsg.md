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

H001 eval feature-cache shard command before raw dump. This filters the feature-dump dataset to ids that are missing from the existing feature run and caps this process to a bounded number of new ids:

```bash
mkdir -p logs
ts=$(date +%Y%m%d_%H%M%S)
tmux new-session -d -s h001_open3dsg_dump_features_h001_eval_shard "cd /home/yoohyun/research && bash -lc 'set -o pipefail; env UID=\$(id -u) GID=\$(id -g) OPEN3DSG_CHECKPOINT=/workspace/local_dataset/Open3DSG_staged/training_repro/mlops/opensg/mlflow/363094050435167554/2a23a9af581b4666a207423aa6217853/checkpoints/epoch=13-step=13104.ckpt OPEN3DSG_FEATURE_SHARD_ONLY_MISSING=1 OPEN3DSG_FEATURE_SHARD_MAX_NEW_IDS=5 OPEN3DSG_BLIP_EMBED_CHUNK_SIZE=1 OPEN3DSG_BLIP_PROJECTOR_CHUNK_SIZE=1 PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True,max_split_size_mb:64 docker compose -f experiments/H001_geom_reliability/sources/open3dsg/compose.open3dsg.yaml run --rm dump_features_h001_eval; rc=\$?; echo \"finished_at=\$(date -Is)\"; echo \"exit_code=\$rc\"; printf \"%s\n\" \"\$rc\" > logs/open3dsg_dump_features_h001_eval_shard_${ts}.exit; exit \$rc' > logs/open3dsg_dump_features_h001_eval_shard_${ts}.log 2>&1"
```

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) OPEN3DSG_CHECKPOINT=/workspace/local_dataset/Open3DSG_staged/training_repro/output/checkpoints/<checkpoint>.ckpt docker compose -f experiments/H001_geom_reliability/sources/open3dsg/compose.open3dsg.yaml run --rm eval_h001_gt_objects'
```

`eval_h001_gt_objects` is protected by `open3dsg_eval_preflight.py` and stops before Open3DSG execution if checkpoint/runtime/scope/import gates fail. It defaults to `OPEN3DSG_EVAL_WORKERS=0` and `OPEN3DSG_SHM_SIZE=16gb` because the feature-ready raw-dump run reached the full context load but failed during worker/shared-memory cleanup before writing `raw_dump/raw.jsonl`. Source patch schema `h001_open3dsg_source_patch_v12` also aligns avg-BLIP relationship image embeddings to the loaded BLIP model dtype and switches BLIP generation from legacy `max_length` to `max_new_tokens`.
