# Open3DSG H001 Eval Feature Dump Shard Mode

Status: ready_to_launch
Created at: 2026-05-18 10:00 KST

## Purpose

Replace blind full-loader resumes with a reproducible remaining-id shard
mode. This mode changes only feature-cache generation. It does not reduce
the final H001 eval metric scope.

## Source Patch

Schema: `h001_open3dsg_source_patch_v10`

Key behavior:

- `OPEN3DSG_FEATURE_SHARD_ONLY_MISSING=1` filters the feature-dump dataset
  to ids that do not already have all three feature roles.
- `OPEN3DSG_FEATURE_SHARD_MAX_NEW_IDS=<N>` limits the current run to at
  most `N` selected missing ids.
- Missing preprocessed contexts are skipped during shard selection.
- Test-mode feature dumping skips the eval-only relation mapper allocation.
- Lazy dataset loading is enabled for H001 eval feature dumping.

## Current Input State

```text
feature_run_dir=local_dataset/Open3DSG_staged/h001_runtime/output/features/clip_features_h001_eval_blip_top5_scales3
complete_ids=195/377
next_first_missing_loadable_id=10b17940-3938-2467-8a7a-958300ba83d3-1
```

## Launch Template

```bash
mkdir -p logs
ts=$(date +%Y%m%d_%H%M%S)
tmux new-session -d -s h001_open3dsg_dump_features_h001_eval_shard "cd /home/yoohyun/research && bash -lc 'set -o pipefail; env UID=\$(id -u) GID=\$(id -g) OPEN3DSG_CHECKPOINT=/workspace/local_dataset/Open3DSG_staged/training_repro/mlops/opensg/mlflow/363094050435167554/2a23a9af581b4666a207423aa6217853/checkpoints/epoch=13-step=13104.ckpt OPEN3DSG_FEATURE_SHARD_ONLY_MISSING=1 OPEN3DSG_FEATURE_SHARD_MAX_NEW_IDS=5 OPEN3DSG_BLIP_EMBED_CHUNK_SIZE=1 OPEN3DSG_BLIP_PROJECTOR_CHUNK_SIZE=1 PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True,max_split_size_mb:64 docker compose -f configs/open3dsg/compose.open3dsg.yaml run --rm dump_features_h001_eval; rc=\$?; echo \"finished_at=\$(date -Is)\"; echo \"exit_code=\$rc\"; printf \"%s\n\" \"\$rc\" > logs/open3dsg_dump_features_h001_eval_shard_${ts}.exit; exit \$rc' > logs/open3dsg_dump_features_h001_eval_shard_${ts}.log 2>&1"
```

## Verification Commands

```bash
tail -c 50000 logs/open3dsg_dump_features_h001_eval_shard_<timestamp>.log | tr '\r' '\n' | grep -E 'H001 feature shard|Testing DataLoader 0:|finished_at=|exit_code=|Traceback|CUDA out of memory|Killed|RuntimeError|Error' | tail -40
cat logs/open3dsg_dump_features_h001_eval_shard_<timestamp>.exit
env UID=$(id -u) GID=$(id -g) docker compose -f configs/open3dsg/compose.open3dsg.yaml run --rm feature_audit_h001_eval
```
