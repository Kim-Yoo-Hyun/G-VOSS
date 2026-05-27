# Qwen-VL Adapter Commands

Run from the repository root.

Generate the contract artifacts:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm qwen_vl_adapter_contract'
```

Docker services use fixed model/cache roots:

```text
HF_HOME=/workspace/local_dataset/model_cache/huggingface
QWEN_VL_MODEL_ID=Qwen/Qwen3-VL-4B-Instruct
QWEN_VL_LOCAL_DIR=/workspace/local_dataset/model_cache/huggingface/qwen_vl/Qwen3-VL-4B-Instruct
```

The locked Qwen3-VL-4B model cache has been downloaded and verified. Any
future model downloads must run in `tmux` or another background process and
write timestamped logs under `logs/`.

Validate the frozen input/output JSONL contract and parser skeleton before any
new prompt/parser change or inference run:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm qwen_vl_contract_validator'
```

Select and validate the non-held-out tiny pilot scope:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm qwen_vl_tiny_pilot_scope'
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm qwen_vl_tiny_pilot_validator'
```

Plan tiny-pilot crop rendering and model runtime lock without download or inference:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm qwen_vl_runtime_plan'
```

Render tiny-pilot pair crops, then revalidate:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm qwen_vl_pair_crop_render'
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm qwen_vl_tiny_pilot_validator'
```

Freeze the third-source full-promotion protocol before any full Qwen metric run:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm qwen_vl_full_source_plan'
```

This produces `full_source_plan/{manifest.json,protocol.json,commands.md,report.md}`.
It does not run Qwen inference. The next implementation gate is a
`qwen_vl_full_source_input` builder that audits the complete directed-pair /
family input universe, crop coverage, missing-row policy, and shard list.

Build and validate the full-source input audit:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm qwen_vl_full_source_input'
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm qwen_vl_contract_validator --repo-root /workspace --contract-dir /workspace/experiments/H001_geom_reliability/sources/qwen_vl --input-jsonl /workspace/experiments/H001_geom_reliability/sources/qwen_vl/full_source_input/input.jsonl --out /workspace/experiments/H001_geom_reliability/sources/qwen_vl/full_source_input/validation'
```

Current result: 77,748 universe query rows, 33,384 inferable input rows, 44,364
missing rows, and 134 shards. Full inference is still blocked until the
reserved pair-crop paths are rendered or verified by a render-on-demand shard
preflight.

Smoke-test full-source crop rendering on a single shard:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) QWEN_VL_FULL_SOURCE_SHARD_ID=qwen_full_source_shard_0000 docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm qwen_vl_full_source_crop_render'
sg docker -c 'env UID=$(id -u) GID=$(id -g) QWEN_VL_FULL_SOURCE_SHARD_ID=qwen_full_source_shard_0000 docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm qwen_vl_full_source_crop_preflight'
```

Current shard smoke result: 250 input rows, 84 unique pair crops, 84 verified
existing crops, and 0 errors. Artifacts are under
`full_source_crops/shards/qwen_full_source_shard_0000/`.

Launch all-scope crop rendering in the background:

```bash
mkdir -p logs
ts=$(date +%Y%m%d_%H%M%S)
tmux new-session -d -s h001_qwen_vl_full_crop_render "cd /home/yoohyun/research && bash -lc 'sg docker -c '\''env UID=$(id -u) GID=$(id -g) QWEN_VL_FULL_SOURCE_SHARD_ID=all docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm qwen_vl_full_source_crop_render'\''; rc=\$?; printf \"%s\n\" \"\$rc\" > logs/qwen_vl_full_source_crop_render_all_${ts}.exit; exit \"\$rc\"' > logs/qwen_vl_full_source_crop_render_all_${ts}.log 2>&1"
```

Current all-scope result: render exit `0`; preflight exit `0`; 33,384 input
rows, 11,128 unique pair crops, 11,128 verified crops, and 0 errors.

Verification command:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) QWEN_VL_FULL_SOURCE_SHARD_ID=all docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm qwen_vl_full_source_crop_preflight'
```

After this gate, Qwen full-source inference may be scheduled shard-wise, but the
result is not a paper metric until parser validation, adapter export, geometry
join, metrics, controls, bootstrap, and audit are complete.

Freeze the full-source inference runner and resume policy:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm qwen_vl_full_source_inference_plan'
```

Current result: `full_source_inference_runner_frozen_no_inference`, 33,384
planned rows, 134 shards, and 11,128 verified unique pair crops. Artifacts are
under `full_source_inference_plan/`.

Dry-run the first shard without model load or inference:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) QWEN_VL_FULL_SOURCE_SHARD_ID=qwen_full_source_shard_0000 docker compose -f experiments/H001_geom_reliability/sources/qwen_vl/compose.qwen.yaml run --rm qwen_vl_full_source_infer_dry_run'
```

Current dry-run result: `qwen_full_source_shard_0000`, 250 rows, 84 unique pair
crops, 0 blockers. The actual inference service is
`qwen_vl_full_source_infer_shard`, but it must be launched as a timestamped
background job and remains non-metric until the full validation/evaluation path
completes.
