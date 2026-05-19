# Open3DSG H001 Raw Dump Retry With BLIP Generation Guard

Status: raw_dump_written_exit_137
Launched at: 2026-05-18 17:18 KST
Ended at: 2026-05-18 17:46 KST
Last checked: 2026-05-18 17:49 KST

## Reason

The dtype-guarded retry passed the previous Float/BFloat16 issue but failed
because the legacy Open3DSG BLIP generation call used `max_length=20`,
which current Transformers rejected after prompt/input embedding handling.
Source patch schema `h001_open3dsg_source_patch_v12` switches the call to
`max_new_tokens`.

## Settings

```text
OPEN3DSG_EVAL_WORKERS=0
OPEN3DSG_SHM_SIZE=16gb
OPEN3DSG_BLIP_GENERATE_MAX_NEW_TOKENS=20
source_patch=h001_open3dsg_source_patch_v12
```

## Exact Command

```bash
mkdir -p logs experiments/H001_geom_reliability/sources/open3dsg/raw_dump
tmux new-session -d -s h001_open3dsg_eval_avg_blip_retry_generate "cd /home/yoohyun/research && bash -lc 'set -o pipefail; echo \"started_at=\$(date -Is)\"; echo \"cwd=\$(pwd)\"; echo \"raw_dump=experiments/H001_geom_reliability/sources/open3dsg/raw_dump/raw.jsonl\"; echo \"mitigation=OPEN3DSG_EVAL_WORKERS=0 OPEN3DSG_SHM_SIZE=16gb source_patch_v12_blip_dtype_max_new_tokens\"; env UID=\$(id -u) GID=\$(id -g) OPEN3DSG_SHM_SIZE=16gb OPEN3DSG_EVAL_WORKERS=0 OPEN3DSG_BLIP_GENERATE_MAX_NEW_TOKENS=20 OPEN3DSG_CHECKPOINT=/workspace/local_dataset/Open3DSG_staged/training_repro/mlops/opensg/mlflow/363094050435167554/2a23a9af581b4666a207423aa6217853/checkpoints/epoch=13-step=13104.ckpt OPEN3DSG_FEATURE_LOAD_DIR=/workspace/local_dataset/Open3DSG_staged/h001_runtime/output/features/clip_features_h001_eval_blip_top5_scales3 OPEN3DSG_RAW_DUMP_JSONL=/workspace/experiments/H001_geom_reliability/sources/open3dsg/raw_dump/raw.jsonl OPEN3DSG_BASELINE_RUN_ID=open3dsg_avg_blip_epoch13_step13104 OPEN3DSG_MODEL_SOURCE_STAGE=avg_blip_full_variant docker compose -f experiments/H001_geom_reliability/sources/open3dsg/compose.open3dsg.yaml run --rm eval_h001_gt_objects; rc=\$?; echo \"finished_at=\$(date -Is)\"; echo \"exit_code=\$rc\"; printf \"%s\n\" \"\$rc\" > logs/open3dsg_eval_h001_gt_objects_avg_blip_retry_generate_20260518_171846.exit; exit \$rc' > logs/open3dsg_eval_h001_gt_objects_avg_blip_retry_generate_20260518_171846.log 2>&1"
```

## Log And Exit Files

```text
logs/open3dsg_eval_h001_gt_objects_avg_blip_retry_generate_20260518_171846.log
logs/open3dsg_eval_h001_gt_objects_avg_blip_retry_generate_20260518_171846.exit
```

## Result

As of the 2026-05-18 17:49 KST check:

- tmux session `h001_open3dsg_eval_avg_blip_retry_generate` ended.
- Exit file contains `137`.
- Docker `eval_preflight` passed.
- H001 context load reached `388/388`.
- Lightning test loop reached `377/377`.
- Raw dump hook wrote `19162` rows to `raw_dump/raw.jsonl`.
- Docker `open3dsg_raw_dump_identity` reports `raw_dump_identity_audit_ready` with no blockers.

## Caveat

The process exit is nonzero because the container was killed after raw dump
writing and Open3DSG's own evaluation pass. The raw dump is therefore usable
only after the separate identity audit, not because the original eval command
exited cleanly.

## Verification Commands

```bash
cat logs/open3dsg_eval_h001_gt_objects_avg_blip_retry_generate_20260518_171846.exit
wc -l experiments/H001_geom_reliability/sources/open3dsg/raw_dump/raw.jsonl
env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm open3dsg_raw_dump_identity
```
