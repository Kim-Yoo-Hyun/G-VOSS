# Open3DSG Post-Dump Handoff Commands

Status: `waiting_for_feature_dump_completion`
Created at: `2026-05-10T15:57:57+00:00`

Run from the repository root.

## Ordered Commands

### feature_audit

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/sources/open3dsg/compose.open3dsg.yaml run --rm feature_audit'
```

### train_pilot

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/sources/open3dsg/compose.open3dsg.yaml run --rm train_pilot'
```

### train_full

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/sources/open3dsg/compose.open3dsg.yaml run --rm train_full'
```

### eval_preflight

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) OPEN3DSG_CHECKPOINT=/workspace/local_dataset/Open3DSG_staged/training_repro/output/checkpoints/<checkpoint>.ckpt docker compose -f experiments/H001_geom_reliability/sources/open3dsg/compose.open3dsg.yaml run --rm eval_preflight'
```

### eval_h001_gt_objects

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) OPEN3DSG_CHECKPOINT=/workspace/local_dataset/Open3DSG_staged/training_repro/output/checkpoints/<checkpoint>.ckpt docker compose -f experiments/H001_geom_reliability/sources/open3dsg/compose.open3dsg.yaml run --rm eval_h001_gt_objects'
```

### adapter_raw_dump

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) OPEN3DSG_RAW_DUMP_JSONL=/workspace/experiments/H001_geom_reliability/sources/open3dsg/raw_dump/raw.jsonl docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm open3dsg_adapter_raw_dump'
```

### failure_analysis_real_guard

```bash
# blocked: add/run the real Open3DSG failure-analysis generator only after prediction JSONL, GT join, geometry join, and metrics exist; the current Docker smoke service in experiments/H001_geom_reliability/compose.yaml is not metric evidence
```

## Hard Gates

- Do not run `train_pilot` until Docker `feature_audit` reports `ready` on the official BLIP TopK5/scales3 run.
- Do not run `train_full` until the pilot checkpoint path and logs are recorded.
- Do not run Open3DSG evaluation without a recorded `OPEN3DSG_CHECKPOINT` path.
- Do not run adapter/metrics until an identity-preserving raw dump exists.
- Do not promote reduced/pilot feature routes to paper-result evidence.
