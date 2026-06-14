# Open3DSG Post-Dump Handoff Commands

Status: `completed_superseded_by_runtime_outputs`
Created at: `2026-05-11T15:27:01+00:00`
Updated at: `2026-05-18T21:37:00+09:00`

Run from the repository root.

## Ordered Commands

### feature_audit

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f configs/open3dsg/compose.open3dsg.yaml run --rm feature_audit'
```

### train_full_avg_blip

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f configs/open3dsg/compose.open3dsg.yaml run --rm train_full_avg_blip'
```

The selected checkpoint is:

```text
local_dataset/Open3DSG_staged/training_repro/mlops/opensg/mlflow/363094050435167554/2a23a9af581b4666a207423aa6217853/checkpoints/epoch=13-step=13104.ckpt
```

### eval_preflight

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) OPEN3DSG_CHECKPOINT=/workspace/local_dataset/Open3DSG_staged/training_repro/mlops/opensg/mlflow/363094050435167554/2a23a9af581b4666a207423aa6217853/checkpoints/epoch=13-step=13104.ckpt docker compose -f configs/open3dsg/compose.open3dsg.yaml run --rm eval_preflight'
```

### eval_h001_gt_objects

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) OPEN3DSG_CHECKPOINT=/workspace/local_dataset/Open3DSG_staged/training_repro/mlops/opensg/mlflow/363094050435167554/2a23a9af581b4666a207423aa6217853/checkpoints/epoch=13-step=13104.ckpt docker compose -f configs/open3dsg/compose.open3dsg.yaml run --rm eval_h001_gt_objects'
```

### adapter_raw_dump

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) OPEN3DSG_RAW_DUMP_JSONL=/workspace/experiments/H001_geom_reliability/sources/open3dsg/raw_dump/raw.jsonl docker compose -f configs/h001/compose.yaml run --rm open3dsg_adapter_raw_dump'
```

### geometry_and_metrics

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm open3dsg_geometry_join'
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm open3dsg_metric_eval'
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm table_builder'
```

### failure_analysis_real

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm open3dsg_failure_generator_real'
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm open3dsg_failure_case_sampler'
```

## Hard Gates

- Non-averaged `train_pilot` / `train_full` are OOM-blocked and should be cited only as limitation records.
- Do not run Open3DSG evaluation without a recorded `OPEN3DSG_CHECKPOINT` path.
- Do not rerun source eval under host GPU/RAM/swap pressure; the current identity-audited raw dump retains an exit-137-after-write caveat.
- Do not promote reduced/pilot feature routes to paper-result evidence.
