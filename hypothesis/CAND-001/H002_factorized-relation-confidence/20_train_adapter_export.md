# H002 Train Adapter Export

Last updated: 2026-06-12

## Purpose

`19_train_raw_dump_runner.md`에서 시작한 Open3DSG train pilot raw dump를
adapter prediction contract로 변환한다. 이 문서는 raw dump completion, raw identity
repair, adapter export, train provenance fix 결과를 기록한다.

## Raw Dump Completion

Raw dump job:

```text
tmux session: h002_open3dsg_raw_dump_20260612_042106
log: logs/h002_open3dsg_raw_dump_20260612_042106.log
exit: logs/h002_open3dsg_raw_dump_20260612_042106.exit
```

Completion status:

```text
exit code: 0
completed_batches: 100
rows_written: 4,626
```

Raw dump files:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/raw_dump/raw.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/raw_dump/raw.completed.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/raw_dump/stream_manifest.json
```

Verification:

```text
raw.jsonl: 4,626 rows
raw.completed.jsonl: 100 rows
stream_manifest.rows_written: 4,626
stream_manifest.completed_batches: 100
```

## Raw Identity Repair

The first adapter export failed with:

```text
status: blocked_conversion_errors
reason: duplicate_prediction_ids
```

Cause:

- Open3DSG raw dump contained duplicate rows for the same
  `(subgraph_id, subject_id, object_id)` key.
- Duplicate rows were limited to one subgraph:

```text
0cac7613-8d6f-2d13-8d92-487a50d40794_2
```

Repair tool:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/repair_open3dsg_raw_dump.py
```

Command:

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/repair_open3dsg_raw_dump.py \
  --repo-root .
```

Repair policy:

```text
Deduplicate raw rows by (subgraph_id, subject_id, object_id).
Keep the earliest raw line and drop later duplicates before adapter export.
```

Repair result:

```text
status: ready
input_rows: 4,626
output_rows: 4,615
duplicate_groups: 11
duplicate_extra_rows: 11
label_conflict_groups: 0
max_abs_score_diff: 1.19e-7
```

Repaired raw:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/raw_dump/raw.dedup.jsonl
```

Repair manifest:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/raw_dump/repair_manifest.json
```

Interpretation:

- The duplicate issue is an identity duplication from repeated node indices for
  the same object instance id.
- There was no predicate-label conflict.
- The only score drift was floating-point noise below `1e-6`.

## Adapter Export

Command:

```bash
python3 experiments/H001_geom_reliability/scripts/export_open3dsg_predictions.py \
  --repo-root . \
  --raw-dump-jsonl hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/raw_dump/raw.dedup.jsonl \
  --subset-json hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/source_contract/relationships_train_pilot.json \
  --relationships-file local_dataset/3DSSG_subset/relationships.txt \
  --selected-scans hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/source_contract/selected_scans.txt \
  --output-dir hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/adapter \
  --split-name h002_train_open3dsg_pilot \
  --baseline-run-id open3dsg_train_pilot_epoch13_step13104
```

Adapter result:

```text
status: ready
contexts: 100
raw_rows: 4,615
prediction_rows: 118,560
raw_rows_filtered_outside_h001_context: 54
same_endpoint_skipped: 1
errors: 0
warnings: 55
```

Adapter artifacts:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/adapter/predictions.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/adapter/manifest.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/adapter/report.md
```

Prediction verification:

```text
prediction rows: 118,560
duplicate_prediction_ids: 0
subgraphs: 100
min rows per subgraph: 312
max rows per subgraph: 1,872
split_name: h002_train_open3dsg_pilot
```

Warnings:

- `54` raw rows were filtered because raw edge endpoints were outside the frozen
  train pilot object context.
- `1` same-endpoint row was skipped.
- These warnings are retained as source-adapter noise and are not geometry/RGA
  evidence.

## Provenance Fix

The reused H001 adapter hardcodes:

```text
subset_source = local_dataset/3DSSG_subset/relationships_validation.json
```

This is wrong for H002 train pilot even though the adapter was invoked with the
correct `--subset-json`. H002 therefore normalizes prediction provenance after
export.

Fix tool:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/fix_adapter_provenance.py
```

Command:

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/fix_adapter_provenance.py \
  --repo-root .
```

Result:

```text
status: ready
rows: 118,560
changed_rows: 118,560
```

Final `subset_source`:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/source_contract/relationships_train_pilot.json
```

Anti-leak check:

```bash
rg -n -m 1 "relationships_validation" \
  hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/adapter/predictions.jsonl
```

Expected:

```text
no match
```

## Current Boundary

Established:

- Open3DSG train pilot semantic predictions exist for the frozen 100 train
  subgraphs.
- prediction ids are unique.
- prediction provenance now points to the H002 train pilot subset.
- adapter warnings are explicit and bounded.

Established by the next step:

- geometry verification for these 118,560 prediction rows is recorded in
  `21_train_geometry_join.md`.

Not yet established:

- match-status/RGA rows.
- train-set `RGA-HL/RGA-LH` diagnostic.
- any factorized posterior comparison.

Therefore H002 is now ready for train RGA row construction, not for paper-level
claims.

## Next TODO

Next document:

```text
21_train_geometry_join.md
```

Completed next work:

- join `adapter/predictions.jsonl` with H001 geometry evidence using the
  geometry-only `p_geom_valid` model.
- verify geometry row count equals adapter prediction row count.
- compute coverage by relation family.
- next active step is `22_train_rga_rows.md`.
