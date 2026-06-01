# Open3DSG Full Training Non-Averaged BLIP Retry

Status: launched_running
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
CMD="set -o pipefail; echo launched_at=\$(date -Is); echo session=${SESSION}; echo workdir=/home/yoohyun/research; env UID=\$(id -u) GID=\$(id -g) OPEN3DSG_TRAIN_WORKERS=0 OPEN3DSG_BLIP_EMBED_CHUNK_SIZE=1 OPEN3DSG_BLIP_PROJECTOR_CHUNK_SIZE=1 OPEN3DSG_MIN_GPU_FREE_MB=22000 PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True,max_split_size_mb:64 docker compose -f experiments/H001_geom_reliability/sources/open3dsg/compose.open3dsg.yaml run --rm train_full; rc=\$?; echo finished_at=\$(date -Is); echo exit_code=\$rc; printf '%s\n' \"\$rc\" > ${EXITF}; exit \$rc"
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

Checked at: 2026-06-01 19:40 KST

```text
tmux session: active
exit file: not present
latest training position: epoch 15, about 595/3744 steps, 16%
recent speed: about 1.30 it/s
best current checkpoint: epoch=13-step=13104.ckpt
best current train-dev val/loss: 0.5724539161
checkpoint dir contents: epoch 6, 7, 8, 11, 13 top-k checkpoints plus last.ckpt
run directory size: about 7.5G
disk free: about 56G
GPU status: RTX 5090, about 9.4-14.7G used during checks, utilization active
checked log tail: no OOM, traceback, exit_code, or no-space error found
```

Interpretation: R1 has advanced beyond the earlier OOM-blocked pilot range and
is currently stable, but it is still only a background caveat-reduction retry.
It does not replace the averaged-BLIP paper caveat or current Open3DSG evidence
until completion, checkpoint selection, and the downstream H001 eval chain.

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
env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm open3dsg_checkpoint_selection
```

## Claim Boundary

Do not overwrite or relabel the existing avg-BLIP artifacts. If this retry
succeeds, add non-avg H001 eval services/output paths and rerun feature/cache
audit, checkpoint selection, H001 eval raw dump, adapter export, geometry join,
metrics, bootstrap CI, Table 6, and caveat wording before changing paper text.
