# Qwen-VL Runtime Plan Commands

These are future commands. They were not executed by this planning artifact.

Recommended first model:

```text
QWEN_VL_MODEL_ID=Qwen/Qwen3-VL-4B-Instruct
QWEN_VL_MODEL_REVISION=ebb281ec70b05090aa6165b016eac8ec08e71b17
QWEN_VL_LOCAL_DIR=/workspace/local_dataset/model_cache/huggingface/qwen_vl/Qwen3-VL-4B-Instruct/ebb281ec70b05090aa6165b016eac8ec08e71b17
```

Future resumable download template:

```bash
mkdir -p logs
ts=$(date +%Y%m%d_%H%M%S)
tmux new-session -d -s qwen_vl_model_download \
  "cd /home/yoohyun/research && huggingface-cli download Qwen/Qwen3-VL-4B-Instruct --revision ebb281ec70b05090aa6165b016eac8ec08e71b17 --local-dir local_dataset/model_cache/huggingface/qwen_vl/Qwen3-VL-4B-Instruct/ebb281ec70b05090aa6165b016eac8ec08e71b17 --local-dir-use-symlinks False > logs/qwen_vl_model_download_${ts}.log 2>&1"
```

Verification template after download:

```bash
find local_dataset/model_cache/huggingface/qwen_vl/Qwen3-VL-4B-Instruct/ebb281ec70b05090aa6165b016eac8ec08e71b17 -maxdepth 2 -type f | wc -l
test -f local_dataset/model_cache/huggingface/qwen_vl/Qwen3-VL-4B-Instruct/ebb281ec70b05090aa6165b016eac8ec08e71b17/config.json
```
