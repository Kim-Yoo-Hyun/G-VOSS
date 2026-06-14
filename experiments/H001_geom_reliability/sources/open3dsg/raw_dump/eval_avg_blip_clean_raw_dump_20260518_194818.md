# Open3DSG H001 Clean Raw-Dump-Only Rerun

Status: failed_exit_137_before_raw_write
Launched at: 2026-05-18 19:48 KST
Ended at: 2026-05-18 20:16 KST
Last checked: 2026-05-18 20:20 KST

## Reason

The previous v12 source eval wrote the identity-audited `raw_dump/raw.jsonl`
but the container exited `137` after raw dump writing. This rerun keeps the
same checkpoint/features and adds source patch `h001_open3dsg_source_patch_v13`,
which exits with code `0` immediately after writing the raw dump when
`OPEN3DSG_RAW_DUMP_EXIT_AFTER_WRITE=1`.

## Settings

```text
OPEN3DSG_EVAL_WORKERS=0
OPEN3DSG_SHM_SIZE=16gb
OPEN3DSG_BLIP_GENERATE_MAX_NEW_TOKENS=20
OPEN3DSG_RAW_DUMP_EXIT_AFTER_WRITE=1
source_patch=h001_open3dsg_source_patch_v13
```

## Exact Command

```bash
mkdir -p logs experiments/H001_geom_reliability/sources/open3dsg/raw_dump
tmux new-session -d -s h001_open3dsg_eval_clean_raw_dump "cd /home/yoohyun/research && bash -lc 'set -o pipefail; echo \"started_at=\$(date -Is)\"; echo \"cwd=\$(pwd)\"; echo \"raw_dump=experiments/H001_geom_reliability/sources/open3dsg/raw_dump/raw_clean_exit_20260518_194818.jsonl\"; echo \"guard=OPEN3DSG_RAW_DUMP_EXIT_AFTER_WRITE=1 source_patch_v13\"; env UID=\$(id -u) GID=\$(id -g) OPEN3DSG_SHM_SIZE=16gb OPEN3DSG_EVAL_WORKERS=0 OPEN3DSG_BLIP_GENERATE_MAX_NEW_TOKENS=20 OPEN3DSG_RAW_DUMP_EXIT_AFTER_WRITE=1 OPEN3DSG_CHECKPOINT=/workspace/local_dataset/Open3DSG_staged/training_repro/mlops/opensg/mlflow/363094050435167554/2a23a9af581b4666a207423aa6217853/checkpoints/epoch=13-step=13104.ckpt OPEN3DSG_FEATURE_LOAD_DIR=/workspace/local_dataset/Open3DSG_staged/h001_runtime/output/features/clip_features_h001_eval_blip_top5_scales3 OPEN3DSG_RAW_DUMP_JSONL=/workspace/experiments/H001_geom_reliability/sources/open3dsg/raw_dump/raw_clean_exit_20260518_194818.jsonl OPEN3DSG_BASELINE_RUN_ID=open3dsg_avg_blip_epoch13_step13104 OPEN3DSG_MODEL_SOURCE_STAGE=avg_blip_full_variant docker compose -f configs/open3dsg/compose.open3dsg.yaml run --rm eval_h001_gt_objects; rc=\$?; echo \"finished_at=\$(date -Is)\"; echo \"exit_code=\$rc\"; printf \"%s\n\" \"\$rc\" > logs/open3dsg_eval_h001_gt_objects_clean_raw_dump_20260518_194818.exit; exit \$rc' > logs/open3dsg_eval_h001_gt_objects_clean_raw_dump_20260518_194818.log 2>&1"
```

## Output Path

```text
experiments/H001_geom_reliability/sources/open3dsg/raw_dump/raw_clean_exit_20260518_194818.jsonl
```

## Expected Files

```text
logs/open3dsg_eval_h001_gt_objects_clean_raw_dump_20260518_194818.log
logs/open3dsg_eval_h001_gt_objects_clean_raw_dump_20260518_194818.exit
experiments/H001_geom_reliability/sources/open3dsg/raw_dump/raw_clean_exit_20260518_194818.jsonl
```

## Current Check

As of the 2026-05-18 20:20 KST check:

- tmux session `h001_open3dsg_eval_clean_raw_dump` has ended.
- exit file contains `137`.
- eval preflight passed.
- H001 context load reached `388/388`.
- Lightning test loop reached about `228/377`, then the container was killed.
- `raw_clean_exit_20260518_194818.jsonl` was not written.
- The v13 exit-after-write guard did not fire because raw export still occurs at `on_test_epoch_end`.
- Next provenance route, if required, should stream raw rows per test batch with resumable append rather than waiting for epoch end.

## Verification Commands

```bash
cat logs/open3dsg_eval_h001_gt_objects_clean_raw_dump_20260518_194818.exit
wc -l experiments/H001_geom_reliability/sources/open3dsg/raw_dump/raw.jsonl experiments/H001_geom_reliability/sources/open3dsg/raw_dump/raw_clean_exit_20260518_194818.jsonl
sha256sum experiments/H001_geom_reliability/sources/open3dsg/raw_dump/raw.jsonl experiments/H001_geom_reliability/sources/open3dsg/raw_dump/raw_clean_exit_20260518_194818.jsonl
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm open3dsg_raw_dump_identity --repo-root /workspace --raw-dump-jsonl /workspace/experiments/H001_geom_reliability/sources/open3dsg/raw_dump/raw_clean_exit_20260518_194818.jsonl --out /workspace/experiments/H001_geom_reliability/sources/open3dsg/raw_dump_identity_clean_20260518_194818
```
