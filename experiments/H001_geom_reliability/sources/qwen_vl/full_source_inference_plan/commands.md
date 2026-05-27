# Qwen-VL Full-Source Inference Runner Commands

Generate this plan:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm qwen_vl_full_source_inference_plan'
```

Build the Qwen runtime image after runner changes:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/sources/qwen_vl/compose.qwen.yaml build qwen_vl_full_source_infer_dry_run qwen_vl_full_source_infer_shard'
```

Dry-run one shard without model load or inference:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) QWEN_VL_FULL_SOURCE_SHARD_ID=qwen_full_source_shard_0000 docker compose -f experiments/H001_geom_reliability/sources/qwen_vl/compose.qwen.yaml run --rm qwen_vl_full_source_infer_dry_run'
```

Launch one inference shard in a timestamped background job:

```bash
mkdir -p logs
ts=$(date +%Y%m%d_%H%M%S)
shard=qwen_full_source_shard_0000
tmux new-session -d -s h001_qwen_vl_infer_${shard} "cd /home/yoohyun/research && bash -lc 'sg docker -c '\''env UID=$(id -u) GID=$(id -g) QWEN_VL_FULL_SOURCE_SHARD_ID=${shard} docker compose -f experiments/H001_geom_reliability/sources/qwen_vl/compose.qwen.yaml run --rm qwen_vl_full_source_infer_shard'\''; rc=\$?; printf "%s\n" "\$rc" > logs/qwen_vl_full_source_infer_${shard}_${ts}.exit; exit "\$rc"' > logs/qwen_vl_full_source_infer_${shard}_${ts}.log 2>&1"
```

Launch remaining shards sequentially in one resumable background loop:

```bash
mkdir -p logs
ts=$(date +%Y%m%d_%H%M%S)
tmux new-session -d -s h001_qwen_vl_infer_remaining \
  "cd /home/yoohyun/research && QWEN_VL_LOOP_RUN_ID=${ts} QWEN_VL_LOOP_START_SUFFIX=0001 QWEN_VL_LOOP_END_SUFFIX=0133 bash experiments/H001_geom_reliability/scripts/run_qwen_vl_full_source_shard_loop.sh > logs/qwen_vl_full_source_infer_remaining_${ts}.log 2>&1"
```

Loop outputs and lightweight checks:

```bash
tmux has-session -t h001_qwen_vl_infer_remaining
tail -40 logs/qwen_vl_full_source_infer_remaining_${ts}.log
tail -20 logs/qwen_vl_full_source_infer_remaining_${ts}.status.tsv
cat logs/qwen_vl_full_source_infer_remaining_${ts}.exit
find experiments/H001_geom_reliability/sources/qwen_vl/full_source_runtime/manifests -name 'qwen_full_source_shard_*.json' | wc -l
```

Plan outputs:

- `experiments/H001_geom_reliability/sources/qwen_vl/full_source_inference_plan/manifest.json`
- `experiments/H001_geom_reliability/sources/qwen_vl/full_source_inference_plan/runner_contract.json`
- `experiments/H001_geom_reliability/sources/qwen_vl/full_source_inference_plan/shards.jsonl`
- `experiments/H001_geom_reliability/sources/qwen_vl/full_source_inference_plan/commands.md`
- `experiments/H001_geom_reliability/sources/qwen_vl/full_source_inference_plan/report.md`
