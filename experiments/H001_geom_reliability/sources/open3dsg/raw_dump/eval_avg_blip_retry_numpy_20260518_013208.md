# Open3DSG H001 Raw Dump Avg-BLIP NumPy Retry

Status: failed_missing_h001_eval_features
Launched at: 2026-05-18 01:32 KST
Finished at: 2026-05-18 01:35 KST

## Scope

This retries the selected explicitly labeled averaged-BLIP Open3DSG variant
after source patch schema `h001_open3dsg_source_patch_v7` installed a
`numpy._core` pickle compatibility alias for staged H001 runtime preprocess
artifacts.

Docker load sanity before launch:

```text
contexts=388
loaded=377
missing_or_failed=11
```

The 11 missing/failed contexts are the pre-existing H001 runtime preprocess
caveat and must remain visible before final metric promotion.

## Selected Checkpoint

```text
local_dataset/Open3DSG_staged/training_repro/mlops/opensg/mlflow/363094050435167554/2a23a9af581b4666a207423aa6217853/checkpoints/epoch=13-step=13104.ckpt
```

Selection signal:

```text
Open3DSG train-dev val/loss 0.32881081104278564 at step 13103, before any H001 held-out raw dump, metric, failure-analysis, or visual inspection.
```

## Exact Command

```bash
mkdir -p logs experiments/H001_geom_reliability/sources/open3dsg/raw_dump
tmux new-session -d -s h001_open3dsg_eval_avg_blip_retry_numpy "cd /home/yoohyun/research && bash -lc 'set -o pipefail; echo \"started_at=\$(date -Is)\"; echo \"cwd=\$(pwd)\"; echo \"checkpoint=local_dataset/Open3DSG_staged/training_repro/mlops/opensg/mlflow/363094050435167554/2a23a9af581b4666a207423aa6217853/checkpoints/epoch=13-step=13104.ckpt\"; echo \"raw_dump=experiments/H001_geom_reliability/sources/open3dsg/raw_dump/raw.jsonl\"; env UID=\$(id -u) GID=\$(id -g) OPEN3DSG_CHECKPOINT=/workspace/local_dataset/Open3DSG_staged/training_repro/mlops/opensg/mlflow/363094050435167554/2a23a9af581b4666a207423aa6217853/checkpoints/epoch=13-step=13104.ckpt OPEN3DSG_RAW_DUMP_JSONL=/workspace/experiments/H001_geom_reliability/sources/open3dsg/raw_dump/raw.jsonl OPEN3DSG_BASELINE_RUN_ID=open3dsg_avg_blip_epoch13_step13104 OPEN3DSG_MODEL_SOURCE_STAGE=avg_blip_full_variant docker compose -f configs/open3dsg/compose.open3dsg.yaml run --rm eval_h001_gt_objects; rc=\$?; echo \"finished_at=\$(date -Is)\"; echo \"exit_code=\$rc\"; printf \"%s\n\" \"\$rc\" > logs/open3dsg_eval_h001_gt_objects_avg_blip_retry_numpy_20260518_013208.exit; exit \$rc' > logs/open3dsg_eval_h001_gt_objects_avg_blip_retry_numpy_20260518_013208.log 2>&1"
```

## Log And Exit Files

```text
logs/open3dsg_eval_h001_gt_objects_avg_blip_retry_numpy_20260518_013208.log
logs/open3dsg_eval_h001_gt_objects_avg_blip_retry_numpy_20260518_013208.exit
```

## Expected Output

```text
experiments/H001_geom_reliability/sources/open3dsg/raw_dump/raw.jsonl
```

## Result

```text
exit_code=1
raw_dump_missing=true
```

The NumPy compatibility fix worked: Open3DSG loaded the validation set and
advanced through the 388 context preload, with only the 11 known missing
preprocess contexts reported. The run then failed in `load_features_disk`
because `OPEN3DSG_FEATURE_LOAD_DIR` pointed to the official `training_repro`
feature dump, which does not contain H001 held-out eval feature ids such as
`ab835faa-54c6-29a1-9b55-1a5217fcba19-1.pt`.

Follow-up: create H001 eval feature coverage under
`local_dataset/Open3DSG_staged/h001_runtime/output/features/clip_features_h001_eval_blip_top5_scales3`,
audit it, then rerun `eval_h001_gt_objects` with that directory.

## Verification Commands

```bash
cat logs/open3dsg_eval_h001_gt_objects_avg_blip_retry_numpy_20260518_013208.exit
wc -l experiments/H001_geom_reliability/sources/open3dsg/raw_dump/raw.jsonl
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm open3dsg_raw_dump_identity'
```
