# Open3DSG H001 Streaming Raw Dump Rerun Retry

Status: failed_exit_137_after_stream_progress
Launched at: 2026-05-19 09:26 KST
Ended at: 2026-05-19 09:52 KST
Last checked: 2026-05-19 09:55 KST

## Reason

The previous v14 streaming raw-dump rerun exited `137` after checkpoint loading
and before `Testing DataLoader`, so no streamed raw rows or completed-batch
state were written. This retry keeps the v14 streaming contract but writes to
fresh timestamped output paths.

## Settings

```text
OPEN3DSG_EVAL_WORKERS=0
OPEN3DSG_SHM_SIZE=16gb
OPEN3DSG_DATASET_LOAD_WORKERS=1
OPEN3DSG_LAZY_DATASET=1
OPEN3DSG_MIN_GPU_FREE_MB=24000
OPEN3DSG_BLIP_GENERATE_MAX_NEW_TOKENS=20
OPEN3DSG_BLIP_EMBED_CHUNK_SIZE=1
OPEN3DSG_BLIP_PROJECTOR_CHUNK_SIZE=1
OPEN3DSG_RAW_DUMP_STREAM_BATCHES=1
OPEN3DSG_RAW_DUMP_RESUME=1
OPEN3DSG_RAW_DUMP_EXIT_AFTER_WRITE=1
PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True,max_split_size_mb:64
source_patch=h001_open3dsg_source_patch_v14_retry
```

## Exact Command

```bash
mkdir -p logs experiments/H001_geom_reliability/sources/open3dsg/raw_dump
tmux new-session -d -s h001_open3dsg_eval_stream_raw_dump_retry_20260519_092628 "cd /home/yoohyun/research && bash -lc 'set -o pipefail; echo started_at=$(date -Is); echo cwd=$(pwd); echo raw_dump=experiments/H001_geom_reliability/sources/open3dsg/raw_dump/raw_stream_retry_20260519_092628.jsonl; echo completed=experiments/H001_geom_reliability/sources/open3dsg/raw_dump/raw_stream_retry_20260519_092628.completed.jsonl; echo manifest=experiments/H001_geom_reliability/sources/open3dsg/raw_dump/raw_stream_retry_20260519_092628.manifest.json; echo guard=OPEN3DSG_RAW_DUMP_STREAM_BATCHES=1 OPEN3DSG_RAW_DUMP_RESUME=1 OPEN3DSG_RAW_DUMP_EXIT_AFTER_WRITE=1 source_patch_v14_retry; echo command_workdir=/home/yoohyun/research; env UID=$(id -u) GID=$(id -g) OPEN3DSG_SHM_SIZE=16gb OPEN3DSG_EVAL_WORKERS=0 OPEN3DSG_DATASET_LOAD_WORKERS=1 OPEN3DSG_LAZY_DATASET=1 OPEN3DSG_MIN_GPU_FREE_MB=24000 OPEN3DSG_BLIP_GENERATE_MAX_NEW_TOKENS=20 OPEN3DSG_BLIP_EMBED_CHUNK_SIZE=1 OPEN3DSG_BLIP_PROJECTOR_CHUNK_SIZE=1 OPEN3DSG_RAW_DUMP_STREAM_BATCHES=1 OPEN3DSG_RAW_DUMP_RESUME=1 OPEN3DSG_RAW_DUMP_EXIT_AFTER_WRITE=1 OPEN3DSG_CHECKPOINT=/workspace/local_dataset/Open3DSG_staged/training_repro/mlops/opensg/mlflow/363094050435167554/2a23a9af581b4666a207423aa6217853/checkpoints/epoch=13-step=13104.ckpt OPEN3DSG_FEATURE_LOAD_DIR=/workspace/local_dataset/Open3DSG_staged/h001_runtime/output/features/clip_features_h001_eval_blip_top5_scales3 OPEN3DSG_RAW_DUMP_JSONL=/workspace/experiments/H001_geom_reliability/sources/open3dsg/raw_dump/raw_stream_retry_20260519_092628.jsonl OPEN3DSG_RAW_DUMP_COMPLETED_JSONL=/workspace/experiments/H001_geom_reliability/sources/open3dsg/raw_dump/raw_stream_retry_20260519_092628.completed.jsonl OPEN3DSG_RAW_DUMP_MANIFEST_JSON=/workspace/experiments/H001_geom_reliability/sources/open3dsg/raw_dump/raw_stream_retry_20260519_092628.manifest.json OPEN3DSG_BASELINE_RUN_ID=open3dsg_avg_blip_epoch13_step13104 OPEN3DSG_MODEL_SOURCE_STAGE=avg_blip_full_variant PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True,max_split_size_mb:64 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 docker compose -f configs/open3dsg/compose.open3dsg.yaml run --rm eval_h001_gt_objects; rc=$?; echo finished_at=$(date -Is); echo exit_code=$rc; printf \"%s\n\" \"$rc\" > logs/open3dsg_eval_h001_gt_objects_stream_raw_dump_retry_20260519_092628.exit; exit $rc' > logs/open3dsg_eval_h001_gt_objects_stream_raw_dump_retry_20260519_092628.log 2>&1"
```

## Output Paths

```text
experiments/H001_geom_reliability/sources/open3dsg/raw_dump/raw_stream_retry_20260519_092628.jsonl
experiments/H001_geom_reliability/sources/open3dsg/raw_dump/raw_stream_retry_20260519_092628.completed.jsonl
experiments/H001_geom_reliability/sources/open3dsg/raw_dump/raw_stream_retry_20260519_092628.manifest.json
```

## Initial Check

- tmux session `h001_open3dsg_eval_stream_raw_dump_retry_20260519_092628` is active.
- Docker container `open3dsg-eval_h001_gt_objects-run-f9395446f022` is active.
- Eval preflight passed with status `ready`.
- Source patch passed with status `ready`.
- Initial check had no streamed raw output.

## Running Check

As of the 2026-05-19 09:30 KST check:

- tmux session is still active.
- Context scan reached `388/388`.
- `Testing DataLoader 0` started.
- Stream output file was initialized at `raw_stream_retry_20260519_092628.jsonl`.
- The log reported completed stream batches through batch `14`.
- The log reported `646` raw rows written by batch `14`.
- `raw_stream_retry_20260519_092628.jsonl` existed with size about `4.2 MB`.
- `raw_stream_retry_20260519_092628.completed.jsonl` existed with size about `4.0 KB`.

## Final Check

As of the 2026-05-19 09:55 KST check:

- tmux session ended.
- exit file contained `137`.
- log reached `Testing DataLoader 0` item `294/377`.
- the last completed stream batch was `completed_batches=294`.
- `raw_stream_retry_20260519_092628.jsonl` contained `15,010` rows.
- `raw_stream_retry_20260519_092628.completed.jsonl` contained `294` completed-batch records.
- last completed raw scan id: `bf9a3ddd-45a5-2e80-80bc-647365c7ca08-2`.
- log did not contain a Python `CUDA out of memory` exception.
- kernel log query did not return OOM/GPU Xid evidence in the checked window.
- current `nvidia-smi` after container exit showed only the unrelated
  `ipykernel_launcher` process using about `5.6 GB` GPU memory.
- host swap was still heavily used after exit (`7.7/8.0 GB`), so the most
  likely failure mode is SIGKILL under host/container memory pressure rather
  than a clean CUDA OOM exception.

The same output path is now resumable because the completed-batch file exists.

## Verification Commands

```bash
tmux has-session -t h001_open3dsg_eval_stream_raw_dump_retry_20260519_092628
tail -n 80 logs/open3dsg_eval_h001_gt_objects_stream_raw_dump_retry_20260519_092628.log
cat logs/open3dsg_eval_h001_gt_objects_stream_raw_dump_retry_20260519_092628.exit
wc -l experiments/H001_geom_reliability/sources/open3dsg/raw_dump/raw_stream_retry_20260519_092628.jsonl experiments/H001_geom_reliability/sources/open3dsg/raw_dump/raw_stream_retry_20260519_092628.completed.jsonl
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm open3dsg_raw_dump_identity --repo-root /workspace --raw-dump-jsonl /workspace/experiments/H001_geom_reliability/sources/open3dsg/raw_dump/raw_stream_retry_20260519_092628.jsonl --out /workspace/experiments/H001_geom_reliability/sources/open3dsg/raw_dump_identity_stream_retry_20260519_092628
```
