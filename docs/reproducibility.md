# H001 Reproducibility Runbook

Last updated: 2026-05-19 KST

This document consolidates dataset, checkpoint, environment, Docker, reproduction,
and evaluation-summary information for `experiments/H001_geom_reliability/`.
Detailed stage logs remain in the experiment subfolders.

## Current Status

Facts:

- Active experiment root: `experiments/H001_geom_reliability/`.
- Paper-body experiment outputs must be generated through Docker.
- `VL-SAT` locked artifacts, Open3DSG second-source metrics, Open3DSG real
  failure rows, and Table 6 are ready.
- Qwen-VL is an optional modern semantic-source smoke path. The locked
  Qwen3-VL-4B cache is ready, but runtime inference is not paper metric
  evidence.
- As of 2026-05-18 21:37 KST, no H001/Open3DSG/Qwen Docker container is
  running. A non-Open3DSG `ipykernel_launcher` process is using about 9.7 GB GPU
  memory, 41 GiB host RAM is used, and swap usage is about 7.0/8.0 GiB. Do not
  start another heavy Open3DSG/Qwen run until GPU/RAM pressure is cleared.

## Data Locations

Large runtime data is intentionally under ignored local roots:

| Purpose | Path |
| --- | --- |
| Raw 3RScan payload | `local_dataset/3RScan/scans/` |
| Open3DSG training root | `local_dataset/Open3DSG_staged/training_repro/` |
| Open3DSG H001 eval root | `local_dataset/Open3DSG_staged/h001_runtime/` |
| Open3DSG train/dev features | `local_dataset/Open3DSG_staged/training_repro/output/features/clip_features_h001_official_blip_top5_scales3/` |
| Open3DSG H001 eval features | `local_dataset/Open3DSG_staged/h001_runtime/output/features/clip_features_h001_eval_blip_top5_scales3/` |
| Qwen-VL model cache | `local_dataset/model_cache/huggingface/qwen_vl/Qwen3-VL-4B-Instruct/ebb281ec70b05090aa6165b016eac8ec08e71b17/` |
| Qwen-VL tiny crops | `local_dataset/qwen_vl_crops/tiny_pilot/` |

Tracked experiment artifacts live under:

```text
experiments/H001_geom_reliability/
hypothesis/CAND-001/H001_geometry-grounded-verification/artifacts/evaluation/
```

## Environment And Docker

Build the main H001 table/evaluation image:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml build'
```

Build and check the Open3DSG reproduction image:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/sources/open3dsg/compose.open3dsg.yaml build'
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/sources/open3dsg/compose.open3dsg.yaml run --rm env_check'
```

Build and check the Qwen-VL runtime image/cache:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/sources/qwen_vl/compose.qwen.yaml build'
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/sources/qwen_vl/compose.qwen.yaml run --rm qwen_vl_cache_verify'
```

## Data Download And Staging

VL-SAT / 3DSSG local roots:

- Source/runtime root: `local_dataset/VLSAT_code/CVPR2023-VLSAT/`.
- Staged validation roots:
  `local_dataset/VLSAT_staged/CVPR2023-VLSAT/` and
  `local_dataset/VLSAT_staged/h001_validation_hardened/CVPR2023-VLSAT/`.
- The official VL-SAT `data_processing/README.md` also records a Google Drive
  data link:
  `https://drive.google.com/file/d/1V_QIDvu1fZqKkjP2Kg41HNCjX8TPfH6u/view?usp=sharing`.

VL-SAT data download template if rebuilding the local staged root:

```bash
mkdir -p logs local_dataset/VLSAT_staged
python -m gdown 'https://drive.google.com/uc?id=1V_QIDvu1fZqKkjP2Kg41HNCjX8TPfH6u' -O local_dataset/VLSAT_staged/vlsat_data_processing_payload
```

Audit current Open3DSG/3RScan payload readiness:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm open3dsg_payload --repo-root /workspace'
```

Run a small resumable download/extract pilot:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm open3dsg_payload --repo-root /workspace --download-missing --extract-sequence --limit 1 --workers 2'
```

Run a resumable batch:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm open3dsg_payload --repo-root /workspace --download-missing --extract-sequence --limit 20 --workers 4 --timeout 300 --retries 1'
```

For long batches, use `tmux` and timestamped logs under `logs/`. Example:

```bash
mkdir -p logs
ts=$(date +%Y%m%d_%H%M%S)
tmux new-session -d -s h001_open3dsg_payload_batch \
  "cd /home/yoohyun/research && bash -lc 'set -o pipefail; sg docker -c '\''env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm open3dsg_payload --repo-root /workspace --download-missing --extract-sequence --limit 100 --workers 4 --timeout 300 --retries 1'\''; rc=\$?; printf \"%s\n\" \"\$rc\" > logs/open3dsg_payload_batch_${ts}.exit; exit \$rc' > logs/open3dsg_payload_batch_${ts}.log 2>&1"
```

Stage H001 held-out eval scan symlinks:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/sources/open3dsg/compose.open3dsg.yaml run --rm h001_eval_payload'
```

## Checkpoints And Model Downloads

VL-SAT:

- Official checkpoint link recorded in local README:
  `https://drive.google.com/file/d/1_C-LXRlSobupApb-JsajKG5oxKnfKgdx/view?usp=sharing`.
- Local checkpoint root:
  `local_dataset/VLSAT_code/CVPR2023-VLSAT/output/ckp/Mmgnet/3dssg/`.
- Local CLIP adapter checkpoint:
  `local_dataset/VLSAT_code/CVPR2023-VLSAT/clip_adapter/checkpoint/origin_mean.pth`.
- Current local files include `rel_predictor_3d_best.pth`,
  `rel_encoder_3d_best.pth`, `obj_encoder_best.pth`, `mmg_best.pth`, and the
  matching optimizer/config scheduler files.

Download template if the VL-SAT checkpoint root must be rebuilt:

```bash
mkdir -p logs local_dataset/VLSAT_code/CVPR2023-VLSAT
python -m gdown 'https://drive.google.com/uc?id=1_C-LXRlSobupApb-JsajKG5oxKnfKgdx' -O local_dataset/VLSAT_code/CVPR2023-VLSAT/vlsat_checkpoint_download
```

Verify local VL-SAT checkpoint files:

```bash
find local_dataset/VLSAT_code/CVPR2023-VLSAT/output/ckp/Mmgnet/3dssg -maxdepth 1 -type f -name '*_best.pth' | sort
test -f local_dataset/VLSAT_code/CVPR2023-VLSAT/clip_adapter/checkpoint/origin_mean.pth
```

Open3DSG:

- The official Open3DSG repository did not expose a trusted final trained
  relation checkpoint in the checked path. The H001 Open3DSG checkpoint is
  generated by our Docker reproduction.
- Selected checkpoint:
  `local_dataset/Open3DSG_staged/training_repro/mlops/opensg/mlflow/363094050435167554/2a23a9af581b4666a207423aa6217853/checkpoints/epoch=13-step=13104.ckpt`.
- Selection signal: train-dev `val/loss` 0.32881081104278564 at step 13103.
- Limitation: this is an explicitly labeled Open3DSG averaged-BLIP variant;
  the exact non-averaged BLIP projector route failed under CUDA OOM.

Open3DSG component model downloads, if the staged checkpoint/component root must
be rebuilt:

```bash
python -m gdown 'https://drive.google.com/uc?id=1BfvxB6eo3XksE6AfMUgoBHwzVYce1ed1' -O local_dataset/Open3DSG_staged/training_repro/output/checkpoints/blip2_positional_embedding.pt
python -m gdown 'https://drive.google.com/uc?id=18RIPkqlt7KXiG8BzxNIweMxYvjlMZifO' -O local_dataset/Open3DSG_staged/training_repro/output/checkpoints/pointnet.pth
python -m gdown 'https://drive.google.com/uc?id=14oH-eZjyB4rlh2-_25pNpGBhbegKi16I' -O local_dataset/Open3DSG_staged/training_repro/output/checkpoints/pointnet2_ulip.pt
```

OpenSeg component model files are hosted under
`https://storage.googleapis.com/cloud-tpu-checkpoints/detection/projects/openseg/colab/exported_model/`
and are verified by Docker `cache_preflight`.

Qwen-VL:

- Model id: `Qwen/Qwen3-VL-4B-Instruct`
- Revision: `ebb281ec70b05090aa6165b016eac8ec08e71b17`
- Local dir:
  `local_dataset/model_cache/huggingface/qwen_vl/Qwen3-VL-4B-Instruct/ebb281ec70b05090aa6165b016eac8ec08e71b17/`
- Download status: completed, exit code 0, Docker `qwen_vl_cache_verify`
  status `model_cache_ready`.

Exact Qwen-VL background download command used:

```bash
mkdir -p logs experiments/H001_geom_reliability/sources/qwen_vl/model_cache
tmux new-session -d -s h001_qwen_vl_model_download "cd /home/yoohyun/research && bash -lc 'set -o pipefail; sg docker -c '\''env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/sources/qwen_vl/compose.qwen.yaml build qwen_vl_model_download && env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/sources/qwen_vl/compose.qwen.yaml run --rm qwen_vl_model_download && env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/sources/qwen_vl/compose.qwen.yaml run --rm qwen_vl_cache_verify'\''; rc=$?; printf \"%s\n\" \"$rc\" > logs/qwen_vl_model_download_20260512_082830.exit; exit $rc' > logs/qwen_vl_model_download_20260512_082830.log 2>&1"
```

## Experiment Reproduction Commands

Regenerate paper-facing H001 tables/report from locked artifacts:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm table_builder'
```

Recreate Open3DSG adapter, geometry join, metrics, and Table 6 from the
identity-audited raw dump:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) OPEN3DSG_RAW_DUMP_JSONL=/workspace/experiments/H001_geom_reliability/sources/open3dsg/raw_dump/raw.jsonl docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm open3dsg_adapter_raw_dump'
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm open3dsg_geometry_join'
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm open3dsg_metric_eval'
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm table_builder'
```

Regenerate Open3DSG failure-analysis rows and qualitative case queue:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm open3dsg_failure_generator_real'
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm open3dsg_failure_case_sampler'
```

Optional Qwen-VL runtime smoke after GPU/RAM pressure is cleared:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/sources/qwen_vl/compose.qwen.yaml run --rm qwen_vl_runtime_preflight'
sg docker -c 'env UID=$(id -u) GID=$(id -g) QWEN_VL_TINY_INFERENCE_LIMIT=3 docker compose -f experiments/H001_geom_reliability/sources/qwen_vl/compose.qwen.yaml run --rm qwen_vl_tiny_inference_smoke'
```

Raw Open3DSG source eval has clean provenance through the v14 streaming
same-path resume. The canonical raw dump remains `raw_dump/raw.jsonl`, and the
streaming resume output `raw_stream_retry_20260519_092628.jsonl` completed with
exit 0, manifest status `raw_dump_stream_complete`, 377/377 completed batches,
19,162 rows, dropped/invalid partial rows 0/0, and SHA256 matching the canonical
raw dump. Earlier exit-137 attempts are historical run records.

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) OPEN3DSG_CHECKPOINT=/workspace/local_dataset/Open3DSG_staged/training_repro/mlops/opensg/mlflow/363094050435167554/2a23a9af581b4666a207423aa6217853/checkpoints/epoch=13-step=13104.ckpt docker compose -f experiments/H001_geom_reliability/sources/open3dsg/compose.open3dsg.yaml run --rm eval_h001_gt_objects'
```

## Verification Commands

Check key row counts:

```bash
wc -l \
  experiments/H001_geom_reliability/sources/open3dsg/raw_dump/raw.jsonl \
  experiments/H001_geom_reliability/sources/open3dsg/adapter/predictions.jsonl \
  experiments/H001_geom_reliability/sources/open3dsg/geometry/verification.jsonl \
  experiments/H001_geom_reliability/sources/open3dsg/failure_rows/rows.jsonl \
  experiments/H001_geom_reliability/sources/open3dsg/failure_cases/queue.jsonl
```

Check Open3DSG metric status and key conditions:

```bash
jq -r '.status' experiments/H001_geom_reliability/sources/open3dsg/metrics/metrics.json
jq -r '.conditions | to_entries[] | select(.key=="semantic_only" or .key=="probabilistic_recalibrated" or .key=="rule_verified_point_subtype" or .key=="control_family_specific_p_geom_valid") | [.key, (.value.recall.by_k["50"].recall|tostring), (.value.recall.by_k["100"].recall|tostring), (.value.violation_rate.by_k["50"].violation_rate|tostring), (.value.violation_rate.by_k["100"].violation_rate|tostring)] | @tsv' experiments/H001_geom_reliability/sources/open3dsg/metrics/metrics.json
```

Check Qwen-VL cache:

```bash
cat logs/qwen_vl_model_download_20260512_082830.exit
find local_dataset/model_cache/huggingface/qwen_vl/Qwen3-VL-4B-Instruct/ebb281ec70b05090aa6165b016eac8ec08e71b17 -maxdepth 2 -type f | wc -l
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/sources/qwen_vl/compose.qwen.yaml run --rm qwen_vl_cache_verify'
```

## Artifact And Evaluation Summary

`VL-SAT` locked H001 result:

| Condition | R@50 | R@100 | Violation@50 | Violation@100 |
| --- | ---: | ---: | ---: | ---: |
| `semantic_only` | 0.9599 | 0.9894 | 0.0247 | 0.0469 |
| `probabilistic_recalibrated` | 0.9642 | 0.9921 | 0.0234 | 0.0391 |
| `family_specific_p_geom_valid` | 0.9619 | 0.9914 | 0.0204 | 0.0310 |

Additional `VL-SAT` verifier/audit evidence:

- GT-positive rows: 2,545.
- GT-derived negatives: 2,545.
- `p_geom_valid` AUROC/AUPRC: 0.9779 / 0.9737.
- Reduced visual sanity check: 50/50 labels, reviewer `yhkim`,
  `ready_sanity_pass`.

Open3DSG second-source result:

| Condition | R@50 | R@100 | Violation@50 | Violation@100 |
| --- | ---: | ---: | ---: | ---: |
| `semantic_only` | 0.3945 | 0.4963 | 0.1326 | 0.1195 |
| `probabilistic_recalibrated` | 0.3843 | 0.5580 | 0.0575 | 0.0803 |
| `rule_verified_point_subtype` | 0.4149 | 0.5238 | 0.0000 | 0.0000 |
| `family_specific_p_geom_valid` | 0.4530 | 0.5984 | 0.0228 | 0.0311 |

Open3DSG artifact summary:

- Raw dump: `raw_dump/raw.jsonl`, 19,162 rows.
- Adapter predictions: 496,600 rows; 62 raw rows filtered outside the fixed
  H001 object context.
- Geometry join: 496,600/496,600 rows preserved; 114,600 geometry-checkable
  rows scored.
- Real failure-analysis rows: 57,736 rows, 0 validation errors.
- Qualitative queue: 36 high-severity cases from 6,162 visual-audit candidates.
- Required caveats are frozen under
  `experiments/H001_geom_reliability/sources/open3dsg/paper_caveats/`:
  filtered train split, averaged-BLIP Open3DSG variant, covered loadable H001
  eval scope, residual calibration risk, and `validation_missing_preprocessed:11`.
