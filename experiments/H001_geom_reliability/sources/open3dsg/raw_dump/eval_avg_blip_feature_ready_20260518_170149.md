# Open3DSG H001 Raw Dump After Eval Feature Completion

Status: failed
Launched at: 2026-05-18 17:01 KST
Failed at: 2026-05-18 17:05 KST
Last checked: 2026-05-18 17:06 KST

## Reason

H001 eval feature dump shard loop completed with exit code `0` and the
feature cache reached the covered loadable scope:

```text
complete_feature_ids=377/377
total_pt_files=1131
```

Docker `feature_audit_h001_eval` confirms missing complete feature ids
`0`, but keeps status `blocked` because of the known 11 H001 eval
missing-preprocessed contexts. The raw dump proceeds on the loadable
covered scope.

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
tmux new-session -d -s h001_open3dsg_eval_avg_blip_feature_ready "cd /home/yoohyun/research && bash -lc 'set -o pipefail; echo \"started_at=\$(date -Is)\"; echo \"cwd=\$(pwd)\"; echo \"raw_dump=experiments/H001_geom_reliability/sources/open3dsg/raw_dump/raw.jsonl\"; env UID=\$(id -u) GID=\$(id -g) OPEN3DSG_CHECKPOINT=/workspace/local_dataset/Open3DSG_staged/training_repro/mlops/opensg/mlflow/363094050435167554/2a23a9af581b4666a207423aa6217853/checkpoints/epoch=13-step=13104.ckpt OPEN3DSG_FEATURE_LOAD_DIR=/workspace/local_dataset/Open3DSG_staged/h001_runtime/output/features/clip_features_h001_eval_blip_top5_scales3 OPEN3DSG_RAW_DUMP_JSONL=/workspace/experiments/H001_geom_reliability/sources/open3dsg/raw_dump/raw.jsonl OPEN3DSG_BASELINE_RUN_ID=open3dsg_avg_blip_epoch13_step13104 OPEN3DSG_MODEL_SOURCE_STAGE=avg_blip_full_variant docker compose -f experiments/H001_geom_reliability/sources/open3dsg/compose.open3dsg.yaml run --rm eval_h001_gt_objects; rc=\$?; echo \"finished_at=\$(date -Is)\"; echo \"exit_code=\$rc\"; printf \"%s\n\" \"\$rc\" > logs/open3dsg_eval_h001_gt_objects_avg_blip_feature_ready_20260518_170149.exit; exit \$rc' > logs/open3dsg_eval_h001_gt_objects_avg_blip_feature_ready_20260518_170149.log 2>&1"
```

## Log And Exit Files

```text
logs/open3dsg_eval_h001_gt_objects_avg_blip_feature_ready_20260518_170149.log
logs/open3dsg_eval_h001_gt_objects_avg_blip_feature_ready_20260518_170149.exit
```

## Result

As of the 2026-05-18 17:06 KST check:

- tmux session `h001_open3dsg_eval_avg_blip_feature_ready` ended.
- Exit file contains `1`.
- Docker `eval_preflight` passed and the test loop reached `388/388`.
- `raw_dump/raw.jsonl` was not created.
- Failure happened during post-test model/checkpoint loading / DataLoader shutdown path with Docker shared-memory pressure:

```text
RuntimeError: unable to write to file </torch_...>: No space left on device (28)
RuntimeError: DataLoader worker (...) is killed by signal: Bus error.
```

## Mitigation

The next retry uses Docker compose `shm_size: 16gb` and runs
`eval_h001_gt_objects` with `OPEN3DSG_EVAL_WORKERS=0` to avoid
multi-worker shared-memory transfer.

## Verification Commands

```bash
cat logs/open3dsg_eval_h001_gt_objects_avg_blip_feature_ready_20260518_170149.exit
wc -l experiments/H001_geom_reliability/sources/open3dsg/raw_dump/raw.jsonl
env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm open3dsg_raw_dump_identity
```
