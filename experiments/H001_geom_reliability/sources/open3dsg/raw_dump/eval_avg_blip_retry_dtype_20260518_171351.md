# Open3DSG H001 Raw Dump Retry With BLIP Dtype Guard

Status: failed
Launched at: 2026-05-18 17:13 KST
Failed at: 2026-05-18 17:17 KST
Last checked: 2026-05-18 17:18 KST

## Reason

The SHM-guarded retry passed preflight and avoided the previous
shared-memory crash, but failed when float relationship image embeddings
were passed into the bfloat16 InstructBLIP path. Source patch schema
`h001_open3dsg_source_patch_v11` now casts avg-BLIP relationship image
embeddings to the loaded BLIP model dtype before `BLIP.generate_caption`.

## Settings

```text
OPEN3DSG_EVAL_WORKERS=0
OPEN3DSG_SHM_SIZE=16gb
source_patch=h001_open3dsg_source_patch_v11
```

## Inputs

```text
checkpoint=/workspace/local_dataset/Open3DSG_staged/training_repro/mlops/opensg/mlflow/363094050435167554/2a23a9af581b4666a207423aa6217853/checkpoints/epoch=13-step=13104.ckpt
feature_load_dir=/workspace/local_dataset/Open3DSG_staged/h001_runtime/output/features/clip_features_h001_eval_blip_top5_scales3
raw_dump_jsonl=/workspace/experiments/H001_geom_reliability/sources/open3dsg/raw_dump/raw.jsonl
baseline_run_id=open3dsg_avg_blip_epoch13_step13104
model_source_stage=avg_blip_full_variant
```

## Exact Command

```bash
mkdir -p logs experiments/H001_geom_reliability/sources/open3dsg/raw_dump
tmux new-session -d -s h001_open3dsg_eval_avg_blip_retry_dtype "cd /home/yoohyun/research && bash -lc 'set -o pipefail; echo \"started_at=\$(date -Is)\"; echo \"cwd=\$(pwd)\"; echo \"raw_dump=experiments/H001_geom_reliability/sources/open3dsg/raw_dump/raw.jsonl\"; echo \"mitigation=OPEN3DSG_EVAL_WORKERS=0 OPEN3DSG_SHM_SIZE=16gb source_patch_v11_blip_dtype\"; env UID=\$(id -u) GID=\$(id -g) OPEN3DSG_SHM_SIZE=16gb OPEN3DSG_EVAL_WORKERS=0 OPEN3DSG_CHECKPOINT=/workspace/local_dataset/Open3DSG_staged/training_repro/mlops/opensg/mlflow/363094050435167554/2a23a9af581b4666a207423aa6217853/checkpoints/epoch=13-step=13104.ckpt OPEN3DSG_FEATURE_LOAD_DIR=/workspace/local_dataset/Open3DSG_staged/h001_runtime/output/features/clip_features_h001_eval_blip_top5_scales3 OPEN3DSG_RAW_DUMP_JSONL=/workspace/experiments/H001_geom_reliability/sources/open3dsg/raw_dump/raw.jsonl OPEN3DSG_BASELINE_RUN_ID=open3dsg_avg_blip_epoch13_step13104 OPEN3DSG_MODEL_SOURCE_STAGE=avg_blip_full_variant docker compose -f experiments/H001_geom_reliability/sources/open3dsg/compose.open3dsg.yaml run --rm eval_h001_gt_objects; rc=\$?; echo \"finished_at=\$(date -Is)\"; echo \"exit_code=\$rc\"; printf \"%s\n\" \"\$rc\" > logs/open3dsg_eval_h001_gt_objects_avg_blip_retry_dtype_20260518_171351.exit; exit \$rc' > logs/open3dsg_eval_h001_gt_objects_avg_blip_retry_dtype_20260518_171351.log 2>&1"
```

## Log And Exit Files

```text
logs/open3dsg_eval_h001_gt_objects_avg_blip_retry_dtype_20260518_171351.log
logs/open3dsg_eval_h001_gt_objects_avg_blip_retry_dtype_20260518_171351.exit
```

## Result

As of the 2026-05-18 17:18 KST check:

- tmux session `h001_open3dsg_eval_avg_blip_retry_dtype` ended.
- Exit file contains `1`.
- Docker `eval_preflight` passed.
- H001 eval context load reached `388/388`.
- `raw_dump/raw.jsonl` was not created.
- The BLIP dtype mismatch was mitigated, but current Transformers generation length validation rejected Open3DSG's legacy `max_length=20` call:

```text
ValueError: Input length of input_ids is 0, but `max_length` is set to -41.
```

## Mitigation

Source patch schema `h001_open3dsg_source_patch_v12` replaces the BLIP
generation call with `max_new_tokens`, defaulting to
`OPEN3DSG_BLIP_GENERATE_MAX_NEW_TOKENS=20`.

## Verification Commands

```bash
cat logs/open3dsg_eval_h001_gt_objects_avg_blip_retry_dtype_20260518_171351.exit
wc -l experiments/H001_geom_reliability/sources/open3dsg/raw_dump/raw.jsonl
env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm open3dsg_raw_dump_identity
```
