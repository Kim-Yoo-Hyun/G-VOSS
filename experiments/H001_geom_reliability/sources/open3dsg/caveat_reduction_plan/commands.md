# Open3DSG Caveat-Reduction Commands

This is a planning artifact. Do not run these as paper-result evidence until the relevant Docker services and output paths are confirmed.

## Regenerate This Plan

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm open3dsg_caveat_reduction_plan'
```

## R1 Exact Non-Averaged BLIP Training Retry

```bash
mkdir -p logs
ts=$(date +%Y%m%d_%H%M%S)
tmux new-session -d -s h001_open3dsg_train_full_nonavg_retry \
  "cd /home/yoohyun/research && bash -lc 'set -o pipefail; \
  env UID=$(id -u) GID=$(id -g) OPEN3DSG_TRAIN_WORKERS=0 \
  OPEN3DSG_BLIP_EMBED_CHUNK_SIZE=1 OPEN3DSG_BLIP_PROJECTOR_CHUNK_SIZE=1 \
  OPEN3DSG_MIN_GPU_FREE_MB=22000 \
  PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True,max_split_size_mb:64 \
  docker compose -f experiments/H001_geom_reliability/sources/open3dsg/compose.open3dsg.yaml \
  run --rm train_full; rc=$?; printf "%s\n" "$rc" > logs/open3dsg_train_full_nonavg_retry_${ts}.exit; exit $rc' \
  > logs/open3dsg_train_full_nonavg_retry_${ts}.log 2>&1"
```

After completion, inspect only the log tail and exit file, then refresh checkpoint selection:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm open3dsg_checkpoint_selection'
```

Important: existing H001 eval feature/raw-dump services are avg-BLIP services. Add separate non-avg services and output paths before downstream metric promotion.

## R2 H001 Covered-Context Retry Toward 388/388

```bash
mkdir -p logs
ts=$(date +%Y%m%d_%H%M%S)
tmux new-session -d -s h001_open3dsg_h001_preprocess_retry_388 \
  "cd /home/yoohyun/research && bash -lc 'set -o pipefail; \
  env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/sources/open3dsg/compose.open3dsg.yaml \
  run --rm open3dsg_base bash -lc \"python /workspace/experiments/H001_geom_reliability/scripts/patch_open3dsg_source.py \
  --repo-root /workspace --source-root /workspace/local_dataset/Open3DSG_staged/h001_runtime/source/open3dsg_source && \
  python /workspace/experiments/H001_geom_reliability/scripts/run_open3dsg_train_preprocess.py \
  --staged-root /workspace/local_dataset/Open3DSG_staged/h001_runtime \
  --open3dsg-source /workspace/local_dataset/Open3DSG_staged/h001_runtime/source/open3dsg_source \
  --work-source /workspace/local_dataset/Open3DSG_staged/h001_runtime/work/open3dsg_eval_source \
  --split validation --workers 1 --force --deep-inspect \
  --output-dir /workspace/experiments/H001_geom_reliability/sources/open3dsg/h001_preprocess_retry_388 --scan-id 0cac7532-8d6f-2d13-8cea-1e70d5ae4856 --scan-id 0cac7534-8d6f-2d13-8de7-8a915ed90050 --scan-id 0cac7582-8d6f-2d13-8d4b-e4041cb166c4 --scan-id 0cac7584-8d6f-2d13-8df8-c05e4307b418 --scan-id 10b1794e-3938-2467-89a7-ebc89e84cf88 --scan-id 422885b3-192d-25fc-84c9-9b80eea1752d --scan-id 422885c5-192d-25fc-85e6-12a3d65c8e7b --scan-id bf9a3ddf-45a5-2e80-8007-8e9e7f323e52 --scan-id c7895f63-339c-2d13-81a3-0b07b1eb23b4 --scan-id fcf66d7b-622d-291c-86b8-7db96aebcee3\"; rc=$?; printf "%s\n" "$rc" > logs/open3dsg_h001_preprocess_retry_388_${ts}.exit; exit $rc' \
  > logs/open3dsg_h001_preprocess_retry_388_${ts}.log 2>&1"
```

If new preprocess outputs appear, run bounded missing-id feature generation and audit:

```bash
mkdir -p logs
ts=$(date +%Y%m%d_%H%M%S)
tmux new-session -d -s h001_open3dsg_dump_features_h001_eval_388_retry \
  "cd /home/yoohyun/research && bash -lc 'set -o pipefail; \
  env UID=$(id -u) GID=$(id -g) \
  OPEN3DSG_CHECKPOINT=/workspace/local_dataset/Open3DSG_staged/training_repro/mlops/opensg/mlflow/363094050435167554/2a23a9af581b4666a207423aa6217853/checkpoints/epoch=13-step=13104.ckpt \
  OPEN3DSG_FEATURE_SHARD_ONLY_MISSING=1 OPEN3DSG_FEATURE_SHARD_MAX_NEW_IDS=11 \
  OPEN3DSG_BLIP_EMBED_CHUNK_SIZE=1 OPEN3DSG_BLIP_PROJECTOR_CHUNK_SIZE=1 \
  PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True,max_split_size_mb:64 \
  docker compose -f experiments/H001_geom_reliability/sources/open3dsg/compose.open3dsg.yaml \
  run --rm dump_features_h001_eval; rc=$?; printf "%s\n" "$rc" > logs/open3dsg_dump_features_h001_eval_388_retry_${ts}.exit; exit $rc' \
  > logs/open3dsg_dump_features_h001_eval_388_retry_${ts}.log 2>&1"
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/sources/open3dsg/compose.open3dsg.yaml run --rm feature_audit_h001_eval'
```

## Downstream Chain After Any Successful Retry

- `open3dsg_raw_dump_identity`
- `open3dsg_adapter_raw_dump`
- `open3dsg_geometry_join`
- `open3dsg_metric_eval`
- `bootstrap_ci`
- `table_builder`
- `open3dsg_paper_caveats`

Do not update manuscript caveats until the regenerated downstream artifacts pass.
