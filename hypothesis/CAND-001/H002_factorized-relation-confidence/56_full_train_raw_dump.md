# H002 Full Train Raw Dump

Last updated: 2026-06-16

## Purpose

`55_full_train_runtime_stage.md`에서 preflight-ready 상태가 된 full-train
Open3DSG runtime을 사용해 full-train raw semantic source dump를 실행하고,
adapter export 전에 completeness gate를 확인한다.

이번 단계의 목표:

- `raw_dump_train_full`을 resumable background job으로 실행한다.
- log와 exit file을 `logs/`에 남긴다.
- stream manifest, completed batch count, row count, exit code를 확인한다.
- raw dump completion이 확인된 뒤에만 raw repair / adapter export로 진행한다.

## Decision

Current status:

```text
full_train_raw_dump_complete
```

Meaning:

```text
The full-train raw dump completed with stream_manifest.status =
raw_dump_stream_complete, completed_batches = 3,738, rows_written = 186,218,
and process exit code = 0.
```

## Command

Launched through tmux:

```bash
docker compose -f hypothesis/CAND-001/H002_factorized-relation-confidence/compose.open3dsg_train_full.yaml \
  run --rm raw_dump_train_full
```

tmux session:

```text
h002_open3dsg_train_full_raw_20260615_180429
```

Log:

```text
logs/h002_open3dsg_train_full_raw_20260615_180429.log
```

Exit file:

```text
logs/h002_open3dsg_train_full_raw_20260615_180429.exit
```

The tmux session is no longer running. The exit file contains:

```text
0
```

## Completion Evidence

Raw dump root:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/raw_dump/
```

Files:

| Artifact | Count / Size |
| --- | ---: |
| `raw.jsonl` | 186,218 rows |
| `raw.completed.jsonl` | 3,738 rows |
| `stream_manifest.json` | status ready |

Stream manifest summary:

```json
{
  "status": "raw_dump_stream_complete",
  "completed_batches": 3738,
  "rows_written": 186218,
  "dropped_partial_rows_on_resume": 0,
  "invalid_partial_rows_on_resume": 0
}
```

Final log includes:

```text
H001 raw dump stream finalized ... rows=186218 completed_batches=3738
H001 raw dump stream exit-after-write requested; returning cleanly
```

There is a PyTorch/NCCL teardown warning:

```text
destroy_process_group() was not called before program exit
```

This is recorded as a runtime warning, not a completion blocker, because the
stream manifest is complete and the process exit code is `0`.

## Raw Repair / Dedup

After completion, raw repair was run on the H002 full-train raw dump.

Command:

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/repair_open3dsg_raw_dump.py \
  --repo-root . \
  --raw-dump-jsonl hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/raw_dump/raw.jsonl \
  --out-jsonl hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/raw_dump/raw.dedup.jsonl \
  --manifest hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/raw_dump/repair_manifest.json
```

Result:

```text
status = ready
input_rows = 186,218
output_rows = 186,139
duplicate_groups = 79
duplicate_extra_rows = 79
label_conflict_groups = 0
max_abs_score_diff = 1.1920928955078125e-07
malformed_identity_rows = 0
```

The repaired raw dump preserves the original raw dump and writes:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/raw_dump/raw.dedup.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/raw_dump/repair_manifest.json
```

The deduplicated raw dump is contiguous by subgraph:

```text
raw rows checked = 186,139
subgraph transitions = 3,738
noncontiguous repeats = 0
```

## Boundary

Established:

- full-train raw dump completed.
- process exit code is `0`.
- stream manifest is complete.
- raw row count and completed batch count match the full-train source scope.
- raw repair/dedup is ready.
- validation/test rows were not used for H002 target design or metrics.

Not established in this document:

- adapter prediction export.
- geometry join.
- full-train RGA rows.
- full-train controlled label target.
- posterior revival evidence.

## Next TODO

Next document:

```text
57_full_train_adapter_export.md
```

Goal:

- export the repaired full-train raw dump into identity-preserving prediction
  rows.
- keep train subset provenance.
- avoid the pilot exporter's list-in-memory risk on full-train scale.
- verify row counts, warnings, and no validation provenance before geometry join.
