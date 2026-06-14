# Open3DSG H001 Streaming Raw Dump Resume

Status: completed_exit_0_stream_complete
Launched at: 2026-05-19 10:32 KST
Ended at: 2026-05-19 10:55 KST
Last checked: 2026-05-19 11:46 KST

## Reason

The previous v14 streaming retry exited `137` after writing `294` completed
batches and `15,010` raw rows. This run resumes the same stream output path
using the existing completed-batch file instead of starting a new raw dump.

## Pre-Launch State

```text
raw rows: 15010
completed batches: 294
last completed raw_scan_id: bf9a3ddd-45a5-2e80-80bc-647365c7ca08-2
GPU memory before launch: 330 MB / 32607 MB
swap before launch: 0 B / 8.0 GB
root free space before launch: 125 GB
```

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
source_patch=h001_open3dsg_source_patch_v14_resume
```

## Exact Command

```bash
tmux new-session -d -s h001_open3dsg_eval_stream_raw_dump_resume_20260519_103227 "cd /home/yoohyun/research && bash -lc 'set -o pipefail; echo started_at=$(date -Is); echo cwd=$(pwd); echo resume_from_completed=experiments/H001_geom_reliability/sources/open3dsg/raw_dump/raw_stream_retry_20260519_092628.completed.jsonl; echo raw_dump=experiments/H001_geom_reliability/sources/open3dsg/raw_dump/raw_stream_retry_20260519_092628.jsonl; echo completed=experiments/H001_geom_reliability/sources/open3dsg/raw_dump/raw_stream_retry_20260519_092628.completed.jsonl; echo manifest=experiments/H001_geom_reliability/sources/open3dsg/raw_dump/raw_stream_retry_20260519_092628.manifest.json; echo guard=OPEN3DSG_RAW_DUMP_STREAM_BATCHES=1 OPEN3DSG_RAW_DUMP_RESUME=1 OPEN3DSG_RAW_DUMP_EXIT_AFTER_WRITE=1 source_patch_v14_resume; echo command_workdir=/home/yoohyun/research; env UID=$(id -u) GID=$(id -g) OPEN3DSG_SHM_SIZE=16gb OPEN3DSG_EVAL_WORKERS=0 OPEN3DSG_DATASET_LOAD_WORKERS=1 OPEN3DSG_LAZY_DATASET=1 OPEN3DSG_MIN_GPU_FREE_MB=24000 OPEN3DSG_BLIP_GENERATE_MAX_NEW_TOKENS=20 OPEN3DSG_BLIP_EMBED_CHUNK_SIZE=1 OPEN3DSG_BLIP_PROJECTOR_CHUNK_SIZE=1 OPEN3DSG_RAW_DUMP_STREAM_BATCHES=1 OPEN3DSG_RAW_DUMP_RESUME=1 OPEN3DSG_RAW_DUMP_EXIT_AFTER_WRITE=1 OPEN3DSG_CHECKPOINT=/workspace/local_dataset/Open3DSG_staged/training_repro/mlops/opensg/mlflow/363094050435167554/2a23a9af581b4666a207423aa6217853/checkpoints/epoch=13-step=13104.ckpt OPEN3DSG_FEATURE_LOAD_DIR=/workspace/local_dataset/Open3DSG_staged/h001_runtime/output/features/clip_features_h001_eval_blip_top5_scales3 OPEN3DSG_RAW_DUMP_JSONL=/workspace/experiments/H001_geom_reliability/sources/open3dsg/raw_dump/raw_stream_retry_20260519_092628.jsonl OPEN3DSG_RAW_DUMP_COMPLETED_JSONL=/workspace/experiments/H001_geom_reliability/sources/open3dsg/raw_dump/raw_stream_retry_20260519_092628.completed.jsonl OPEN3DSG_RAW_DUMP_MANIFEST_JSON=/workspace/experiments/H001_geom_reliability/sources/open3dsg/raw_dump/raw_stream_retry_20260519_092628.manifest.json OPEN3DSG_BASELINE_RUN_ID=open3dsg_avg_blip_epoch13_step13104 OPEN3DSG_MODEL_SOURCE_STAGE=avg_blip_full_variant PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True,max_split_size_mb:64 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 docker compose -f configs/open3dsg/compose.open3dsg.yaml run --rm eval_h001_gt_objects; rc=$?; echo finished_at=$(date -Is); echo exit_code=$rc; printf \"%s\n\" \"$rc\" > logs/open3dsg_eval_h001_gt_objects_stream_raw_dump_resume_20260519_103227.exit; exit $rc' > logs/open3dsg_eval_h001_gt_objects_stream_raw_dump_resume_20260519_103227.log 2>&1"
```

## Output Paths

```text
experiments/H001_geom_reliability/sources/open3dsg/raw_dump/raw_stream_retry_20260519_092628.jsonl
experiments/H001_geom_reliability/sources/open3dsg/raw_dump/raw_stream_retry_20260519_092628.completed.jsonl
experiments/H001_geom_reliability/sources/open3dsg/raw_dump/raw_stream_retry_20260519_092628.manifest.json
```

## Initial Check

- tmux session `h001_open3dsg_eval_stream_raw_dump_resume_20260519_103227` is active.
- Docker container `open3dsg-eval_h001_gt_objects-run-e0f8f3993ea3` is active.
- Eval preflight passed with status `ready`.
- Source patch passed with status `ready`.
- Open3DSG started and is rebuilding the test dataset/context scan before the
  test dataloader phase.
- Raw row count and completed-batch count had not changed at the initial check.

## Running Check

As of the 2026-05-19 10:46 KST check:

- tmux session is still active.
- no exit file has been written.
- the run resumed the stream output with
  `completed_batches=294`, `rows_kept=15010`, `rows_dropped=0`, and
  `invalid_rows=0`.
- `Testing DataLoader 0` is at about `196/377`.
- raw row count and completed-batch count are still `15010` and `294` because
  the dataloader has not yet passed the already-completed batch boundary.
- GPU is active at about `24.9/32.6 GB` and `99%` utilization.
- host swap is full again (`8.0/8.0 GB`), so this run remains at risk of
  another host/container SIGKILL before it reaches the append phase.

## Final Check

As of the 2026-05-19 11:46 KST check:

- tmux session ended.
- exit file contained `0`.
- stream output finalized with manifest status `raw_dump_stream_complete`.
- `raw_stream_retry_20260519_092628.jsonl` has `19,162` rows.
- `raw_stream_retry_20260519_092628.completed.jsonl` has `377` completed
  batches.
- manifest reports `rows_written=19162`, `completed_batches=377`,
  `dropped_partial_rows_on_resume=0`, and `invalid_partial_rows_on_resume=0`.
- the stream output SHA256 exactly matches the existing identity-audited
  `raw_dump/raw.jsonl`:
  `7072c77939a84f8739671025534cf09d5b834c507efad22fec3e3172e46ed2c2`.
- GPU memory after completion returned to about `330 MB`; the Open3DSG eval
  container is no longer running.

## Verification Commands

```bash
tmux has-session -t h001_open3dsg_eval_stream_raw_dump_resume_20260519_103227
tail -n 80 logs/open3dsg_eval_h001_gt_objects_stream_raw_dump_resume_20260519_103227.log
cat logs/open3dsg_eval_h001_gt_objects_stream_raw_dump_resume_20260519_103227.exit
wc -l experiments/H001_geom_reliability/sources/open3dsg/raw_dump/raw_stream_retry_20260519_092628.jsonl experiments/H001_geom_reliability/sources/open3dsg/raw_dump/raw_stream_retry_20260519_092628.completed.jsonl
```
