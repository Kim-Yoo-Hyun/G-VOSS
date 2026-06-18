# H002 Full Train Runtime Stage

Last updated: 2026-06-15

## Purpose

`54_full_train_source_runner.md`에서 생성한 full-train source contract를 isolated
Open3DSG runtime에 stage하고, raw dump 실행 전 Docker preflight를 완료한다.

이번 단계의 목표:

- full-train source contract를 Open3DSG runtime layout에 안전하게 연결한다.
- pilot runtime root를 덮지 않는다.
- `compose.open3dsg_train_full.yaml`을 생성한다.
- raw dump를 시작하기 전 scope/checkpoint/import/runtime gate를 확인한다.
- validation/test를 H002 target design에 사용하지 않는다.

## Tool Update

Updated:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/stage_train_raw_dump_runtime.py
```

Change:

- 기존 pilot default는 유지했다.
- full-train을 위해 context/subset filename, runtime root, output dir, scope label,
  report title을 arguments로 받도록 parameterized했다.
- full-train manifest에서는 `pilot_subset`/`pilot_contexts` legacy alias를 쓰지 않도록
  정리했다.

Full-train invocation:

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/stage_train_raw_dump_runtime.py \
  --repo-root . \
  --runtime-root local_dataset/Open3DSG_staged/h002_train_full_runtime \
  --source-contract-dir hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/source_contract \
  --contexts-file-name train_contexts.jsonl \
  --subset-file-name relationships_train_full.json \
  --out-dir hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/runtime_stage \
  --scope-label train_full \
  --report-title 'H002 Open3DSG Full Train Runtime Stage' \
  --write
```

Result:

```text
status = ready
contexts = 3,738
selected_scans = 1,157
blockers = []
```

## Compose File

Added:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/compose.open3dsg_train_full.yaml
```

Services:

```text
stage_runtime
open3dsg_base
preflight
raw_dump_train_full
```

Validation command:

```bash
docker compose -f hypothesis/CAND-001/H002_factorized-relation-confidence/compose.open3dsg_train_full.yaml \
  config --services
```

Result:

```text
stage_runtime
open3dsg_base
preflight
raw_dump_train_full
```

Important:

```text
raw_dump_train_full was defined but not launched in this step.
```

## Runtime Stage Output

Output root:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/runtime_stage/
```

Artifacts:

```text
manifest.json
records.jsonl
subset_records.jsonl
metadata_records.jsonl
runtime_records.jsonl
report.md
```

Runtime root:

```text
local_dataset/Open3DSG_staged/h002_train_full_runtime
```

Runtime counts:

| Item | Count |
| --- | ---: |
| selected scans | 1,157 |
| linked scans | 1,157 |
| sequence-ready scans | 1,157 |
| contexts | 3,738 |
| feature-checked contexts | 3,738 |
| missing feature contexts | 0 |

Feature gate:

```text
status = ready
missing_contexts = 0
```

## Runtime Staging Boundary

Open3DSG upstream `--test` reads validation filenames. Therefore H002 stages:

```text
relationships_train_full.json -> isolated runtime relationships_validation.json
selected train scans -> isolated runtime validation_scans.txt
```

This is allowed only inside:

```text
local_dataset/Open3DSG_staged/h002_train_full_runtime
```

The provenance owner remains:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/source_contract/relationships_train_full.json
```

This does not open validation/test rows.

## Docker Preflight

Command:

```bash
docker compose -f hypothesis/CAND-001/H002_factorized-relation-confidence/compose.open3dsg_train_full.yaml \
  run --rm preflight
```

Result:

```text
status = ready
blockers = []
```

Preflight output root:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/preflight/
```

Artifacts:

```text
manifest.json
raw_dump_contract.json
report.md
```

Preflight gates:

| Gate | Passed |
| --- | --- |
| checkpoint | true |
| runtime | true |
| scope | true |
| imports | true |

Checkpoint:

```text
local_dataset/Open3DSG_staged/training_repro/mlops/opensg/mlflow/363094050435167554/25da9c4c00214f3b880cedbb2a124177/checkpoints/epoch=13-step=13104.ckpt
```

Checkpoint bytes:

```text
1,328,810,637
```

Scope:

| Item | Count |
| --- | ---: |
| selected scans | 1,157 |
| contexts | 3,738 |

Imports:

| Module | Version |
| --- | --- |
| `torch` | `2.8.0+cu128` |
| `pytorch_lightning` | `2.1.1` |
| `tensorflow` | `2.12.0` |
| `open3d` | `0.19.0` |
| `transformers` | `4.46.3` |
| `open_clip` | `3.3.0` |

CUDA:

```text
available = true
device_count = 1
torch_version = 2.8.0+cu128
```

Raw dump contract:

```text
contract_ready_raw_dump_missing
```

This is expected because raw dump has not been launched yet.

## Established

- full-train isolated runtime is staged.
- full-train feature gate passes for all `3,738` contexts.
- Docker preflight passes.
- checkpoint exists and imports pass.
- raw dump output contract is ready.
- raw dump itself has not been started.

## Not Established

- full-train Open3DSG raw dump.
- raw dump completion status.
- raw dump dedup/repair status.
- adapter export.
- geometry join.
- RGA rows.
- labels or posterior smoke.

## Decision

Current status:

```text
full_train_runtime_preflight_ready
```

Meaning:

```text
H002 full-train runtime is ready for a resumable raw dump launch. The next step
is raw dump launch planning and background execution, not posterior modeling.
```

## Next TODO

Next document:

```text
56_full_train_raw_dump.md
```

Goal:

- launch `raw_dump_train_full` as a resumable background/tmux job.
- write timestamped log and exit file under `logs/`.
- verify `stream_manifest.status`, completed batches, row count, and exit code.
- do not proceed to adapter export until raw dump completeness is verified.
