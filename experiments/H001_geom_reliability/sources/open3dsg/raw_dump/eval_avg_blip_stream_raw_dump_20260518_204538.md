# Open3DSG H001 Streaming Raw Dump Rerun

Status: failed_exit_137_before_first_stream_batch
Launched at: 2026-05-18 20:45 KST
Ended at: 2026-05-18 20:53 KST
Last checked: 2026-05-18 20:58 KST

## Reason

The v13 clean raw-dump-only rerun still wrote raw rows only at
`on_test_epoch_end`; it was killed at about `228/377` before raw output was
written. Source patch `h001_open3dsg_source_patch_v14` adds per-batch streaming
append so partial progress is persisted and resumable.

## Settings

```text
OPEN3DSG_EVAL_WORKERS=0
OPEN3DSG_SHM_SIZE=16gb
OPEN3DSG_BLIP_GENERATE_MAX_NEW_TOKENS=20
OPEN3DSG_RAW_DUMP_STREAM_BATCHES=1
OPEN3DSG_RAW_DUMP_RESUME=1
OPEN3DSG_RAW_DUMP_EXIT_AFTER_WRITE=1
source_patch=h001_open3dsg_source_patch_v14
```

## Exact Command

```bash
mkdir -p logs experiments/H001_geom_reliability/sources/open3dsg/raw_dump
tmux new-session -d -s h001_open3dsg_eval_stream_raw_dump "cd /home/yoohyun/research && bash -lc 'set -o pipefail; echo \"started_at=\$(date -Is)\"; echo \"cwd=\$(pwd)\"; echo \"raw_dump=experiments/H001_geom_reliability/sources/open3dsg/raw_dump/raw_stream_20260518_204538.jsonl\"; echo \"guard=OPEN3DSG_RAW_DUMP_STREAM_BATCHES=1 OPEN3DSG_RAW_DUMP_RESUME=1 source_patch_v14\"; env UID=\$(id -u) GID=\$(id -g) OPEN3DSG_SHM_SIZE=16gb OPEN3DSG_EVAL_WORKERS=0 OPEN3DSG_BLIP_GENERATE_MAX_NEW_TOKENS=20 OPEN3DSG_RAW_DUMP_STREAM_BATCHES=1 OPEN3DSG_RAW_DUMP_RESUME=1 OPEN3DSG_RAW_DUMP_EXIT_AFTER_WRITE=1 OPEN3DSG_CHECKPOINT=/workspace/local_dataset/Open3DSG_staged/training_repro/mlops/opensg/mlflow/363094050435167554/2a23a9af581b4666a207423aa6217853/checkpoints/epoch=13-step=13104.ckpt OPEN3DSG_FEATURE_LOAD_DIR=/workspace/local_dataset/Open3DSG_staged/h001_runtime/output/features/clip_features_h001_eval_blip_top5_scales3 OPEN3DSG_RAW_DUMP_JSONL=/workspace/experiments/H001_geom_reliability/sources/open3dsg/raw_dump/raw_stream_20260518_204538.jsonl OPEN3DSG_RAW_DUMP_COMPLETED_JSONL=/workspace/experiments/H001_geom_reliability/sources/open3dsg/raw_dump/raw_stream_20260518_204538.completed.jsonl OPEN3DSG_RAW_DUMP_MANIFEST_JSON=/workspace/experiments/H001_geom_reliability/sources/open3dsg/raw_dump/raw_stream_20260518_204538.manifest.json OPEN3DSG_BASELINE_RUN_ID=open3dsg_avg_blip_epoch13_step13104 OPEN3DSG_MODEL_SOURCE_STAGE=avg_blip_full_variant docker compose -f configs/open3dsg/compose.open3dsg.yaml run --rm eval_h001_gt_objects; rc=\$?; echo \"finished_at=\$(date -Is)\"; echo \"exit_code=\$rc\"; printf \"%s\n\" \"\$rc\" > logs/open3dsg_eval_h001_gt_objects_stream_raw_dump_20260518_204538.exit; exit \$rc' > logs/open3dsg_eval_h001_gt_objects_stream_raw_dump_20260518_204538.log 2>&1"
```

## Output Paths

```text
experiments/H001_geom_reliability/sources/open3dsg/raw_dump/raw_stream_20260518_204538.jsonl
experiments/H001_geom_reliability/sources/open3dsg/raw_dump/raw_stream_20260518_204538.completed.jsonl
experiments/H001_geom_reliability/sources/open3dsg/raw_dump/raw_stream_20260518_204538.manifest.json
```

## Current Check

As of the 2026-05-18 20:58 KST check:

- tmux session `h001_open3dsg_eval_stream_raw_dump` has ended.
- exit file contains `137`.
- eval preflight passed.
- source patch returned status `ready`.
- log reached `LOCAL_RANK: 0 - CUDA_VISIBLE_DEVICES: [0]` after checkpoint loading.
- log did not enter `Testing DataLoader`.
- `raw_stream_20260518_204538.jsonl`, `.completed.jsonl`, and manifest were not written.
- Because no completed stream batch exists, same-path resume would restart from zero.
- Next provenance attempt, if still required, must reduce pre-test memory pressure before rerun.

## Verification Commands

```bash
cat logs/open3dsg_eval_h001_gt_objects_stream_raw_dump_20260518_204538.exit
wc -l experiments/H001_geom_reliability/sources/open3dsg/raw_dump/raw.jsonl experiments/H001_geom_reliability/sources/open3dsg/raw_dump/raw_stream_20260518_204538.jsonl experiments/H001_geom_reliability/sources/open3dsg/raw_dump/raw_stream_20260518_204538.completed.jsonl
sha256sum experiments/H001_geom_reliability/sources/open3dsg/raw_dump/raw.jsonl experiments/H001_geom_reliability/sources/open3dsg/raw_dump/raw_stream_20260518_204538.jsonl
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm open3dsg_raw_dump_identity --repo-root /workspace --raw-dump-jsonl /workspace/experiments/H001_geom_reliability/sources/open3dsg/raw_dump/raw_stream_20260518_204538.jsonl --out /workspace/experiments/H001_geom_reliability/sources/open3dsg/raw_dump_identity_stream_20260518_204538
```
