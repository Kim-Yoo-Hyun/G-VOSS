# Open3DSG Full Training Non-Averaged BLIP Retry

Status: completed_checkpoint_selected_no_downstream_metrics
Launched at: 2026-06-01 07:19:08 KST

## Reason

R1 tests whether the exact non-averaged BLIP projector route can reduce the
current Open3DSG averaged-BLIP variant caveat. This is a background retry only:
it is not paper evidence until the checkpoint is selected and the downstream
Open3DSG H001 chain is regenerated.

## Working Directory

```text
/home/yoohyun/research
```

## Exact Command

```bash
mkdir -p logs
TS=$(date +%Y%m%d_%H%M%S)
SESSION="h001_open3dsg_train_full_nonavg_retry_${TS}"
LOG="logs/open3dsg_train_full_nonavg_retry_${TS}.log"
EXITF="logs/open3dsg_train_full_nonavg_retry_${TS}.exit"
CMD="set -o pipefail; echo launched_at=\$(date -Is); echo session=${SESSION}; echo workdir=/home/yoohyun/research; env UID=\$(id -u) GID=\$(id -g) OPEN3DSG_TRAIN_WORKERS=0 OPEN3DSG_BLIP_EMBED_CHUNK_SIZE=1 OPEN3DSG_BLIP_PROJECTOR_CHUNK_SIZE=1 OPEN3DSG_MIN_GPU_FREE_MB=22000 PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True,max_split_size_mb:64 docker compose -f configs/open3dsg/compose.open3dsg.yaml run --rm train_full; rc=\$?; echo finished_at=\$(date -Is); echo exit_code=\$rc; printf '%s\n' \"\$rc\" > ${EXITF}; exit \$rc"
tmux new-session -d -s "$SESSION" "cd /home/yoohyun/research && bash -lc '$CMD' > '$LOG' 2>&1"
```

## Runtime Record

```text
tmux session: h001_open3dsg_train_full_nonavg_retry_20260601_071908
log: logs/open3dsg_train_full_nonavg_retry_20260601_071908.log
exit file: logs/open3dsg_train_full_nonavg_retry_20260601_071908.exit
prelaunch GPU gate: RTX 5090, 27,179 MiB free, threshold 22,000 MiB
initial MLflow experiment: 363094050435167554
initial MLflow run: 25da9c4c00214f3b880cedbb2a124177
initial run name: strong-sludge-4450
initial status check: active; train_full entered epoch 0, step 7/3744
```

## Latest Status Check

Checked at: 2026-06-04 17:24 KST

```text
tmux session: ended
exit file: present, exit code 0
finished_at: 2026-06-04T17:01:07+09:00
final training position: epoch 99, global step 93600
checkpoint selection status: checkpoint_selection_ready_official_non_avg_blip
selected checkpoint: local_dataset/Open3DSG_staged/training_repro/mlops/opensg/mlflow/363094050435167554/25da9c4c00214f3b880cedbb2a124177/checkpoints/epoch=13-step=13104.ckpt
selected checkpoint sha256: ca86d429b19e846aec2bfff014256bf36f6f90da07e566b90c461d6eca8d76bb
selected train-dev val/loss: 0.5724539160728455 at step 13103
route comparison: best avg-BLIP train-dev val/loss 0.32881081104278564; non-avg minus avg delta +0.24364310503005981
```

Interpretation: R1 completed and produced an official non-averaged BLIP
full-route checkpoint selected by train-dev `val/loss` before selected-route
H001 held-out metrics. This reduces only the route-feasibility blocker. It does
not replace the current averaged-BLIP Open3DSG paper evidence because the
non-avg H001 eval feature/raw dump, adapter, geometry join, metrics, bootstrap
CI, Table 6, and caveat wording have not been regenerated. The selected non-avg
checkpoint also has worse train-dev `val/loss` than the existing avg-BLIP
variant, so downstream regeneration is optional evidence gathering rather than
an automatic paper-table upgrade.

## Expected Outputs

```text
local_dataset/Open3DSG_staged/training_repro/mlops/opensg/mlflow/<experiment-id>/<run-id>/checkpoints/*.ckpt
```

## Verification Commands

Use these only when progress is explicitly requested or a dependent task needs
the result.

```bash
tmux ls | rg h001_open3dsg_train_full_nonavg_retry
tail -n 80 logs/open3dsg_train_full_nonavg_retry_20260601_071908.log
cat logs/open3dsg_train_full_nonavg_retry_20260601_071908.exit
find local_dataset/Open3DSG_staged/training_repro/mlops/opensg/mlflow -type f -name '*.ckpt' -printf '%TY-%Tm-%Td %TH:%TM:%TS %s %p\n' | sort | tail -30
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm open3dsg_checkpoint_selection
```

## Claim Boundary

Do not overwrite or relabel the existing avg-BLIP artifacts. If this retry
succeeds, add non-avg H001 eval services/output paths and rerun feature/cache
audit, checkpoint selection, H001 eval raw dump, adapter export, geometry join,
metrics, bootstrap CI, Table 6, and caveat wording before changing paper text.
