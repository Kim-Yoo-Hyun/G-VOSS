# H002 Train Raw Dump Runner

Last updated: 2026-06-12

## Purpose

`18_train_source_contract.md`에서 고정한 Open3DSG train pilot scope를 실제
Open3DSG semantic source에 연결한다. 이 문서는 H002 전용 Docker runner, runtime
staging, preflight, raw dump launch 상태를 기록한다.

핵심 원칙:

```text
Use train-origin relationships_train_pilot.json, not H001 full_validation artifacts.
```

## Runner Files

Added runner files:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/stage_train_raw_dump_runtime.py
hypothesis/CAND-001/H002_factorized-relation-confidence/compose.open3dsg_train_pilot.yaml
```

The runner uses a separate runtime root:

```text
local_dataset/Open3DSG_staged/h002_train_pilot_runtime
```

This avoids overwriting H001 runtime or H001 full-validation runtime files.

## Runtime Staging

Staging command:

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/stage_train_raw_dump_runtime.py \
  --repo-root . \
  --write
```

Staging result:

```text
status: ready
selected_scans: 100
pilot_contexts: 100
blockers: none
```

Staging artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/runtime_stage/manifest.json
```

Important staging behavior:

- `relationships_train_pilot.json` is written into the Open3DSG runtime as
  `relationships_validation.json` because upstream Open3DSG `--test` reads the
  validation/test files.
- This is an execution adapter, not a split change. Provenance remains train
  because the source file is the H002 train pilot subset.
- `relationships_train.json` and `relationships_test.json` are empty in the H002
  runtime to avoid accidental train/full-test expansion.
- raw 3RScan scan folders are symlinked under the H002 runtime.
- train preprocessed/view directories and feature directory are read-only
  symlink/input sources from `training_repro`.

Feature gate:

```text
checked_contexts: 100
missing_contexts: 0
```

## Docker Compose

Compose file:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/compose.open3dsg_train_pilot.yaml
```

Services:

```text
stage_runtime
preflight
raw_dump_train_pilot
```

Compose validation:

```bash
docker compose -f hypothesis/CAND-001/H002_factorized-relation-confidence/compose.open3dsg_train_pilot.yaml config --services
```

Observed services:

```text
open3dsg_base
preflight
raw_dump_train_pilot
stage_runtime
```

UID/GID note:

- Current host UID/GID is `1001:1001`.
- Compose default user was set to `${UID:-1001}:${GID:-1001}`.
- This avoids container writes being blocked on H002 artifact files.

## Docker Preflight

Container preflight command:

```bash
docker compose -f hypothesis/CAND-001/H002_factorized-relation-confidence/compose.open3dsg_train_pilot.yaml \
  run --rm preflight
```

Result:

```text
status: ready
blockers: none
```

Preflight artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/preflight/manifest.json
```

GPU check:

```text
torch.cuda.is_available(): True
torch.cuda.device_count(): 1
torch: 2.8.0+cu128
```

## Raw Dump Launch

Raw dump command is launched in `tmux` because it is a GPU job.

Session:

```text
h002_open3dsg_raw_dump_20260612_042106
```

Log:

```text
logs/h002_open3dsg_raw_dump_20260612_042106.log
```

Exit file:

```text
logs/h002_open3dsg_raw_dump_20260612_042106.exit
```

Launched command:

```bash
docker compose -f hypothesis/CAND-001/H002_factorized-relation-confidence/compose.open3dsg_train_pilot.yaml \
  run --rm raw_dump_train_pilot
```

Final status:

```text
completed
exit code: 0
```

Initial log observations:

- H002 runtime staging completed with `status: ready`.
- Docker preflight completed with `status: ready`.
- PyTorch sees `NVIDIA GeForce RTX 5090`.
- raw dump streaming started and wrote initial batches.
- Open3DSG checkpoint loaded path:

```text
/workspace/local_dataset/Open3DSG_staged/training_repro/mlops/opensg/mlflow/363094050435167554/25da9c4c00214f3b880cedbb2a124177/checkpoints/epoch=13-step=13104.ckpt
```

Observed after completion:

```text
raw_dump/raw.jsonl: 4,626 rows
raw_dump/raw.completed.jsonl: 100 completed batches
stream_manifest.rows_written: 4,626
stream_manifest.completed_batches: 100
```

Expected raw dump outputs:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/raw_dump/raw.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/raw_dump/raw.completed.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/raw_dump/stream_manifest.json
```

## Progress Checks

Check whether the job is still running:

```bash
tmux list-sessions | rg h002_open3dsg_raw_dump_20260612_042106
```

Check recent log:

```bash
tail -n 80 logs/h002_open3dsg_raw_dump_20260612_042106.log
```

Check exit status:

```bash
cat logs/h002_open3dsg_raw_dump_20260612_042106.exit
```

Check raw dump row count:

```bash
wc -l hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/raw_dump/raw.jsonl
wc -l hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/raw_dump/raw.completed.jsonl
```

Check stream manifest:

```bash
python3 - <<'PY'
import json
from pathlib import Path
p = Path("hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/raw_dump/stream_manifest.json")
m = json.loads(p.read_text())
print(m["rows_written"], m["completed_batches"])
PY
```

## Completion Criteria

The raw dump step is complete only if:

- exit file exists and equals `0`.
- `raw_dump/raw.jsonl` exists and has more than zero rows.
- `raw_dump/raw.completed.jsonl` exists.
- `raw_dump/stream_manifest.json` exists.
- stream manifest has `completed_batches == 100` or another explicitly justified
  count matching the pilot contexts that were actually evaluated.
- adapter export without `--contract-only` produces `adapter/manifest.json`
  with `status == ready`.

## Next Command After Raw Dump

If the raw dump exits successfully, run:

```bash
python3 experiments/H001_geom_reliability/scripts/export_open3dsg_predictions.py \
  --repo-root . \
  --raw-dump-jsonl hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/raw_dump/raw.jsonl \
  --subset-json hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/source_contract/relationships_train_pilot.json \
  --relationships-file local_dataset/3DSSG_subset/relationships.txt \
  --selected-scans hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/source_contract/selected_scans.txt \
  --output-dir hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/adapter \
  --split-name h002_train_open3dsg_pilot \
  --baseline-run-id open3dsg_train_pilot_epoch13_step13104
```

## Current Boundary

Established:

- H002 train-only pilot runtime is staged.
- Docker preflight passes.
- GPU is visible to PyTorch in the raw dump container.
- raw dump job has been launched in `tmux`.

Established by the next step:

- raw dump completion.
- adapter prediction export is recorded in `20_train_adapter_export.md`.

Not yet established:

- geometry join.
- train RGA-HL/RGA-LH diagnostic.

Therefore H002 has moved past the source-runner stage and is ready for train
geometry join.

## Next TODO

Next document:

```text
20_train_adapter_export.md
```

Completed next work:

- inspected raw dump job completion.
- exported Open3DSG train pilot adapter predictions without `--contract-only`.
- verified adapter row identity and context counts.
- next active step is `21_train_geometry_join.md`.
