# Full-Validation Upload Artifact Bundle Commands

Status: `upload_bundle_file_list_and_verification_fixed_no_archive_created`

This runbook fixes the paper-facing upload bundle for Google Drive, Zenodo, or
Hugging Face Dataset. The archive is not created automatically here because the
payload is large. Run packaging as a timestamped tmux/background job when an
actual upload archive is needed.

## Fixed Payload

The default upload bundle contains:

- selected official non-avg Open3DSG checkpoint
- full-validation scope contract
- paper-facing H001 manifest, report, and tables
- full-validation VL-SAT controlled-anchor artifacts
- full-validation Open3DSG unmodified-source sensitivity artifacts
- full-validation Open3DSG 548/548 recovery primary artifacts
- Open3DSG checkpoint-selection provenance

It does not contain raw 3RScan/3DSSG datasets, Open3DSG feature `.pt` caches,
Qwen-VL model cache/runtime outputs, or optional attachment/lateral expansion
outputs.

## Generate Payload File List

Run from the repository root:

```bash
bundle_dir=experiments/H001_geom_reliability/full_validation_transition/artifact_bundle
checkpoint=local_dataset/Open3DSG_staged/training_repro/mlops/opensg/mlflow/363094050435167554/25da9c4c00214f3b880cedbb2a124177/checkpoints/epoch=13-step=13104.ckpt
{
  printf '%s\n' "$checkpoint"
  printf '%s\n' experiments/H001_geom_reliability/manifest.lock.json
  printf '%s\n' experiments/H001_geom_reliability/report.md
  find experiments/H001_geom_reliability/full_validation_transition/scope_contract -type f
  find experiments/H001_geom_reliability/tables -type f
  find experiments/H001_geom_reliability/sources/vlsat/full_validation -type f
  find experiments/H001_geom_reliability/sources/open3dsg/full_validation -type f
  find experiments/H001_geom_reliability/sources/open3dsg/checkpoint_selection -type f
} | sort -u > "${bundle_dir}/upload_payload_files.txt"
wc -l "${bundle_dir}/upload_payload_files.txt"
```

## Generate Per-File Checksums

This reads the full payload and can be I/O-heavy. Use tmux/background if it
will block interactive work.

```bash
mkdir -p logs
ts=$(date +%Y%m%d_%H%M%S)
tmux new-session -d -s h001_fullval_upload_checksums_${ts} \
  "cd /home/yoohyun/research && xargs -a experiments/H001_geom_reliability/full_validation_transition/artifact_bundle/upload_payload_files.txt sha256sum > experiments/H001_geom_reliability/full_validation_transition/artifact_bundle/upload_payload_sha256s.txt 2> logs/h001_fullval_upload_checksums_${ts}.log; rc=\$?; printf '%s\n' \"\$rc\" > logs/h001_fullval_upload_checksums_${ts}.exit; exit \"\$rc\""
```

## Record Key Row Counts

```bash
wc -l \
  experiments/H001_geom_reliability/sources/vlsat/full_validation/raw/raw.jsonl \
  experiments/H001_geom_reliability/sources/vlsat/full_validation/adapter/predictions.jsonl \
  experiments/H001_geom_reliability/sources/vlsat/full_validation/adapter/ground_truth.jsonl \
  experiments/H001_geom_reliability/sources/vlsat/full_validation/geometry/verification.jsonl \
  experiments/H001_geom_reliability/sources/vlsat/full_validation/gt_eval/gt_positive.jsonl \
  experiments/H001_geom_reliability/sources/vlsat/full_validation/gt_eval/counterfactuals.jsonl \
  experiments/H001_geom_reliability/sources/vlsat/full_validation/failure_rows/rows.jsonl \
  experiments/H001_geom_reliability/sources/vlsat/full_validation/failure_cases/queue.jsonl \
  experiments/H001_geom_reliability/sources/open3dsg/full_validation/raw_dump/raw.jsonl \
  experiments/H001_geom_reliability/sources/open3dsg/full_validation/adapter/predictions.jsonl \
  experiments/H001_geom_reliability/sources/open3dsg/full_validation/geometry/verification.jsonl \
  experiments/H001_geom_reliability/sources/open3dsg/full_validation/failure_rows/rows.jsonl \
  experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2/raw_dump/raw.jsonl \
  experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2/adapter/predictions.jsonl \
  experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2/geometry/verification.jsonl \
  experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2/failure_rows/rows.jsonl \
  experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2/failure_cases/queue.jsonl \
  > experiments/H001_geom_reliability/full_validation_transition/artifact_bundle/upload_payload_row_counts.txt
```

## Verify In Place

```bash
bash experiments/H001_geom_reliability/full_validation_transition/artifact_bundle/verify_upload_bundle.sh
```

## Create Upload Archive

Create this only when upload packaging is explicitly needed.

```bash
mkdir -p release logs
ts=$(date +%Y%m%d_%H%M%S)
tmux new-session -d -s h001_fullval_upload_archive_${ts} \
  "cd /home/yoohyun/research && tar --zstd -cf release/h001_full_validation_results_${ts}.tar.zst -T experiments/H001_geom_reliability/full_validation_transition/artifact_bundle/upload_payload_files.txt experiments/H001_geom_reliability/full_validation_transition/artifact_bundle > logs/h001_fullval_upload_archive_${ts}.log 2>&1 && sha256sum release/h001_full_validation_results_${ts}.tar.zst > release/h001_full_validation_results_${ts}.sha256; rc=\$?; printf '%s\n' \"\$rc\" > logs/h001_fullval_upload_archive_${ts}.exit; exit \"\$rc\""
```

After download/extraction on another machine:

```bash
sha256sum -c release/h001_full_validation_results_<timestamp>.sha256
bash experiments/H001_geom_reliability/full_validation_transition/artifact_bundle/verify_upload_bundle.sh
```
