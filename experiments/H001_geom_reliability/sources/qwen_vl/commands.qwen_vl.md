# Qwen-VL Adapter Commands

Run from the repository root.

Generate the contract artifacts:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm qwen_vl_adapter_contract'
```

Future Docker services should use fixed model/cache roots:

```text
HF_HOME=/workspace/local_dataset/model_cache/huggingface
QWEN_VL_MODEL_ID=Qwen/Qwen3-VL-4B-Instruct
QWEN_VL_LOCAL_DIR=/workspace/local_dataset/model_cache/huggingface/qwen_vl/Qwen3-VL-4B-Instruct
```

Long model downloads must run in `tmux` or another background process and write timestamped logs under `logs/`.

Before any model download or inference, validate the frozen input/output JSONL contract and parser skeleton:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm qwen_vl_contract_validator'
```

Select and validate the non-held-out tiny pilot scope without model download or inference:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm qwen_vl_tiny_pilot_scope'
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm qwen_vl_tiny_pilot_validator'
```

Plan tiny-pilot crop rendering and model runtime lock without download or inference:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm qwen_vl_runtime_plan'
```

Render tiny-pilot pair crops without model download or inference, then revalidate:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm qwen_vl_pair_crop_render'
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm qwen_vl_tiny_pilot_validator'
```
