# H001 Covered Recovery Commands

Date: 2026-06-05 KST

This branch is a historical H001 covered-scope caveat-reduction sensitivity
track. It is not the current paper-facing full-validation main route.

## Scope

- runtime root: `local_dataset/Open3DSG_staged/h001_runtime`
- split file: `local_dataset/Open3DSG_staged/h001_runtime/data/3RScan/3DSSG_subset/relationships_validation.json`
- target: 127 scans / 388 contexts
- canonical historical covered result before R2: 377/388 loadable contexts

## Preprocess Recovery Summary

- initial audit: `preprocess_audit/`, 377/388 ready contexts
- missing diagnosis: `missing11_diagnosis_after_views/`, 11/11 visible-object
  gate drops
- default view audit: `views_default_audit/`, 10/10 missing scans readable
- min-visible recovery: `OPEN3DSG_MIN_VISIBLE_OBJECTS=2`, 10/11 recovered
- final relaxed-view scan: `0cac7532-8d6f-2d13-8cea-1e70d5ae4856`
- final preprocess audit: `preprocess_audit_388/`, 388/388 ready contexts

## Feature Shard Result

Working directory:

```text
/home/yoohyun/research
```

Output feature run:

```text
local_dataset/Open3DSG_staged/h001_runtime/output/features/clip_features_h001_eval_blip_top5_scales3
```

Launched tmux job:

```text
h001_open3dsg_h001_r2_feature_388_retry
```

Log:

```text
logs/open3dsg_h001_r2_feature_388_retry_20260605_144854.log
```

Exit file:

```text
logs/open3dsg_h001_r2_feature_388_retry_20260605_144854.exit
```

Command:

```bash
python experiments/H001_geom_reliability/scripts/run_open3dsg_h001_eval_feature_shards.py \
  --repo-root /home/yoohyun/research \
  --max-new-ids 11 \
  --max-iterations 1 \
  --blip-embed-chunk-size 1 \
  --blip-projector-chunk-size 1
```

The shard wrapper launches Docker compose service `dump_features_h001_eval`
with:

```text
OPEN3DSG_FEATURE_SHARD_ONLY_MISSING=1
OPEN3DSG_FEATURE_SHARD_MAX_NEW_IDS=11
OPEN3DSG_BLIP_EMBED_CHUNK_SIZE=1
OPEN3DSG_BLIP_PROJECTOR_CHUNK_SIZE=1
PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True,max_split_size_mb:64
```

Expected files after successful completion:

```text
local_dataset/Open3DSG_staged/h001_runtime/output/features/clip_features_h001_eval_blip_top5_scales3/export_obj_clip_emb/*.pt
local_dataset/Open3DSG_staged/h001_runtime/output/features/clip_features_h001_eval_blip_top5_scales3/export_obj_clip_valids/*.pt
local_dataset/Open3DSG_staged/h001_runtime/output/features/clip_features_h001_eval_blip_top5_scales3/export_rel_clip_emb/*.pt
```

Expected count after completion: 388 complete feature ids, 1,164 `.pt` files.

Verification command:

```bash
env UID=$(id -u) GID=$(id -g) docker compose \
  -f experiments/H001_geom_reliability/sources/open3dsg/compose.open3dsg.yaml \
  run --rm feature_audit_h001_eval
```

If feature audit reports 388/388, rerun raw dump, adapter export, geometry
join, metrics, bootstrap CI, and Table/caveat refresh before changing paper
wording.

Status on 2026-06-05 KST: completed with exit `0`; branch-local feature audit
`features_388/` reports 388/388 complete feature ids.

## Raw Dump Result

Working directory:

```text
/home/yoohyun/research
```

Output root:

```text
experiments/H001_geom_reliability/sources/open3dsg/h001_covered_recovery/raw_dump/
```

Launched tmux job:

```text
h001_open3dsg_h001_r2_raw_388
```

Log:

```text
logs/open3dsg_h001_r2_raw_388_20260605_150256.log
```

Exit file:

```text
logs/open3dsg_h001_r2_raw_388_20260605_150256.exit
```

Expected files:

```text
experiments/H001_geom_reliability/sources/open3dsg/h001_covered_recovery/raw_dump/raw.jsonl
experiments/H001_geom_reliability/sources/open3dsg/h001_covered_recovery/raw_dump/raw.completed.jsonl
experiments/H001_geom_reliability/sources/open3dsg/h001_covered_recovery/raw_dump/stream_manifest.json
```

Completion check:

```bash
cat logs/open3dsg_h001_r2_raw_388_20260605_150256.exit
jq '{status, completed_batches, rows_written, dropped_partial_rows_on_resume, invalid_partial_rows_on_resume}' \
  experiments/H001_geom_reliability/sources/open3dsg/h001_covered_recovery/raw_dump/stream_manifest.json
```

Expected stream status: `raw_dump_stream_complete` with 388/388 completed
batches. After this passes, run raw identity, adapter export, geometry join,
metric eval, bootstrap CI, and Table/caveat refresh under
`h001_covered_recovery/`.

Status on 2026-06-05 KST: stream artifact completed, but the process exited
`137` after finalization because this run used the old H001 streaming hook that
raised `SystemExit(0)` inside the Lightning test hook.

Observed manifest:

```text
status=raw_dump_stream_complete
completed_batches=388
rows_written=19224
dropped_partial_rows_on_resume=0
invalid_partial_rows_on_resume=0
```

Clean-exit follow-up: `experiments/H001_geom_reliability/scripts/patch_open3dsg_source.py`
and the active H001/Open3DSG runtime `trainer.py` files now use a clean
`return` after raw stream finalization instead of raising `SystemExit(0)`.
Do not rerun the 388-context raw stream solely to change the historical exit
file; run raw identity and downstream conversion first.

## Clean-Return Raw Dump Rerun

User requested a process-provenance cleanup rerun on 2026-06-06 KST. This run
uses the patched H001 raw-stream hook that returns cleanly after manifest
finalization instead of raising `SystemExit(0)`.

Working directory:

```text
/home/yoohyun/research
```

Output root:

```text
experiments/H001_geom_reliability/sources/open3dsg/h001_covered_recovery/raw_dump_clean_return_20260606_003130/
```

Launched tmux job:

```text
h001_open3dsg_h001_r2_raw_clean_return_20260606_003130
```

Log:

```text
logs/open3dsg_h001_r2_raw_clean_return_20260606_003130.log
```

Exit file:

```text
logs/open3dsg_h001_r2_raw_clean_return_20260606_003130.exit
```

Expected files:

```text
experiments/H001_geom_reliability/sources/open3dsg/h001_covered_recovery/raw_dump_clean_return_20260606_003130/raw.jsonl
experiments/H001_geom_reliability/sources/open3dsg/h001_covered_recovery/raw_dump_clean_return_20260606_003130/raw.completed.jsonl
experiments/H001_geom_reliability/sources/open3dsg/h001_covered_recovery/raw_dump_clean_return_20260606_003130/stream_manifest.json
```

Command:

```bash
env UID=$(id -u) GID=$(id -g) \
  OPEN3DSG_SHM_SIZE=16gb \
  OPEN3DSG_EVAL_WORKERS=0 \
  OPEN3DSG_RAW_DUMP_STREAM_BATCHES=1 \
  OPEN3DSG_RAW_DUMP_RESUME=0 \
  OPEN3DSG_RAW_DUMP_EXIT_AFTER_WRITE=1 \
  OPEN3DSG_CHECKPOINT=/workspace/local_dataset/Open3DSG_staged/training_repro/mlops/opensg/mlflow/363094050435167554/2a23a9af581b4666a207423aa6217853/checkpoints/epoch=13-step=13104.ckpt \
  OPEN3DSG_FEATURE_LOAD_DIR=/workspace/local_dataset/Open3DSG_staged/h001_runtime/output/features/clip_features_h001_eval_blip_top5_scales3 \
  OPEN3DSG_RAW_DUMP_JSONL=/workspace/experiments/H001_geom_reliability/sources/open3dsg/h001_covered_recovery/raw_dump_clean_return_20260606_003130/raw.jsonl \
  OPEN3DSG_RAW_DUMP_COMPLETED_JSONL=/workspace/experiments/H001_geom_reliability/sources/open3dsg/h001_covered_recovery/raw_dump_clean_return_20260606_003130/raw.completed.jsonl \
  OPEN3DSG_RAW_DUMP_MANIFEST_JSON=/workspace/experiments/H001_geom_reliability/sources/open3dsg/h001_covered_recovery/raw_dump_clean_return_20260606_003130/stream_manifest.json \
  OPEN3DSG_BASELINE_RUN_ID=open3dsg_avg_blip_epoch13_step13104_r2_388_clean_return \
  OPEN3DSG_MODEL_SOURCE_STAGE=avg_blip_full_variant_h001_r2_388_clean_return \
  PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True,max_split_size_mb:64 \
  docker compose -f experiments/H001_geom_reliability/sources/open3dsg/compose.open3dsg.yaml \
    run --rm \
    -e OPEN3DSG_RAW_DUMP_JSONL=/workspace/experiments/H001_geom_reliability/sources/open3dsg/h001_covered_recovery/raw_dump_clean_return_20260606_003130/raw.jsonl \
    -e OPEN3DSG_RAW_DUMP_COMPLETED_JSONL=/workspace/experiments/H001_geom_reliability/sources/open3dsg/h001_covered_recovery/raw_dump_clean_return_20260606_003130/raw.completed.jsonl \
    -e OPEN3DSG_RAW_DUMP_MANIFEST_JSON=/workspace/experiments/H001_geom_reliability/sources/open3dsg/h001_covered_recovery/raw_dump_clean_return_20260606_003130/stream_manifest.json \
    -e OPEN3DSG_RAW_DUMP_STREAM_BATCHES=1 \
    -e OPEN3DSG_RAW_DUMP_RESUME=0 \
    -e OPEN3DSG_RAW_DUMP_EXIT_AFTER_WRITE=1 \
    -e OPEN3DSG_CHECKPOINT=/workspace/local_dataset/Open3DSG_staged/training_repro/mlops/opensg/mlflow/363094050435167554/2a23a9af581b4666a207423aa6217853/checkpoints/epoch=13-step=13104.ckpt \
    -e OPEN3DSG_FEATURE_LOAD_DIR=/workspace/local_dataset/Open3DSG_staged/h001_runtime/output/features/clip_features_h001_eval_blip_top5_scales3 \
    -e OPEN3DSG_BASELINE_RUN_ID=open3dsg_avg_blip_epoch13_step13104_r2_388_clean_return \
    -e OPEN3DSG_MODEL_SOURCE_STAGE=avg_blip_full_variant_h001_r2_388_clean_return \
    -e PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True,max_split_size_mb:64 \
    eval_h001_gt_objects
```

Completion check:

```bash
cat logs/open3dsg_h001_r2_raw_clean_return_20260606_003130.exit
jq '{status, completed_batches, rows_written, dropped_partial_rows_on_resume, invalid_partial_rows_on_resume}' \
  experiments/H001_geom_reliability/sources/open3dsg/h001_covered_recovery/raw_dump_clean_return_20260606_003130/stream_manifest.json
wc -l experiments/H001_geom_reliability/sources/open3dsg/h001_covered_recovery/raw_dump_clean_return_20260606_003130/raw.jsonl
```

Observed result:

```text
exit=137
status=raw_dump_stream_complete
completed_batches=388
rows_written=19224
dropped_partial_rows_on_resume=0
invalid_partial_rows_on_resume=0
raw.jsonl rows=19224
raw.completed.jsonl rows=388
```

The log confirms `H001 raw dump stream exit-after-write requested; returning
cleanly`, followed by wrapper `exit_code=137`. Targeted grep found no
`Traceback`, `RuntimeError`, `Exception`, `Killed`, `OOM`, or out-of-memory
string in the Python log. Docker events, however, confirm `container oom` for
`open3dsg-eval_h001_gt_objects-run-494244438c14` at 2026-06-06 01:05:41 KST,
followed by `exitCode=137`. This output is a complete raw-stream artifact but
failed the process-level clean-exit promotion condition. Treat the remaining
`137` as a Docker/container OOM during or just after Lightning teardown rather
than an incomplete raw dump.

## Clean-Return Retry2 After Swap Reset

User freed swap and requested one more exit-0 attempt on 2026-06-06 KST.
Initial host memory state in the log records swap use `0B`.

Launched tmux job:

```text
h001_open3dsg_h001_r2_raw_clean_return_retry2_20260606_021154
```

Log:

```text
logs/open3dsg_h001_r2_raw_clean_return_retry2_20260606_021154.log
```

Exit file:

```text
logs/open3dsg_h001_r2_raw_clean_return_retry2_20260606_021154.exit
```

Output root:

```text
experiments/H001_geom_reliability/sources/open3dsg/h001_covered_recovery/raw_dump_clean_return_retry2_20260606_021154/
```

Expected files:

```text
experiments/H001_geom_reliability/sources/open3dsg/h001_covered_recovery/raw_dump_clean_return_retry2_20260606_021154/raw.jsonl
experiments/H001_geom_reliability/sources/open3dsg/h001_covered_recovery/raw_dump_clean_return_retry2_20260606_021154/raw.completed.jsonl
experiments/H001_geom_reliability/sources/open3dsg/h001_covered_recovery/raw_dump_clean_return_retry2_20260606_021154/stream_manifest.json
```

Completion check:

```bash
cat logs/open3dsg_h001_r2_raw_clean_return_retry2_20260606_021154.exit
jq '{status, completed_batches, rows_written, dropped_partial_rows_on_resume, invalid_partial_rows_on_resume}' \
  experiments/H001_geom_reliability/sources/open3dsg/h001_covered_recovery/raw_dump_clean_return_retry2_20260606_021154/stream_manifest.json
wc -l experiments/H001_geom_reliability/sources/open3dsg/h001_covered_recovery/raw_dump_clean_return_retry2_20260606_021154/raw.jsonl
docker events --since '2026-06-06T02:11:54+09:00' --filter 'event=oom' --filter 'event=die'
```

Promotion condition remains unchanged: exit file `0`, manifest
`raw_dump_stream_complete`, 388/388 completed batches, 19,224 raw rows, no
dropped/invalid partial rows, and no Docker `container oom` event for the
retry2 container.

Observed result:

```text
exit=137
status=raw_dump_stream_complete
completed_batches=388
rows_written=19224
dropped_partial_rows_on_resume=0
invalid_partial_rows_on_resume=0
raw.jsonl rows=19224
raw.completed.jsonl rows=388
Docker event: container oom at 2026-06-06 02:54:41 KST, exitCode=137
```

The log again confirms `H001 raw dump stream exit-after-write requested;
returning cleanly` before wrapper `exit_code=137`. Initial swap use was `0B`,
but the wrapper memory snapshot at finish showed 5.8 GiB swap in use. Treat this
as a complete raw-stream artifact with a process-level Docker teardown/OOM
caveat. Repeating the same Lightning/DDP `eval_h001_gt_objects` route is not
recommended; use the completed artifact for downstream sensitivity analysis, or
implement a raw-dump-only runner if process-level exit `0` is strictly required.
