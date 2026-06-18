# H002 Full Train RGA Rows

Last updated: 2026-06-16

## Purpose

`58_full_train_geometry_join.md`에서 완료한 full-train geometry verification rows를
Open3DSG full-train prediction rows와 train GT relation subset에 join해서 H002 RGA
row contract를 만든다.

이 단계의 목표:

- full-train prediction / geometry row identity를 보존한다.
- H001 `violated` status를 H002 `unsatisfied`로 매핑한다.
- semantic axis, geometry axis, label axis, coverage, disagreement score를 계산한다.
- full-train `RGA-HL@K`, `RGA-LH-tail@K`, label-geometry distribution을 만든다.
- validation/test는 계속 사용하지 않는다.

## Decision

Current status:

```text
full_train_rga_rows_ready_with_exit_file_caveat
```

Meaning:

```text
The full-train RGA row artifact is complete and train_rga_summary.status =
ready. The tmux session has ended and no train_rga_rows.py process remains, but
the wrapper did not write the planned exit file. Treat this as a logging caveat,
not a scientific artifact blocker, because summary status, row counts, and
validation checks are verified.
```

## Tool Update

Updated:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/train_rga_rows.py
```

Change:

- 기존 pilot default는 유지했다.
- full-train 실행을 위해 `--label-source`, `--source-caveat`,
  `--split-boundary` arguments를 추가했다.
- source contract count는 `selected_contexts`를 우선 읽고, 없으면 기존
  `pilot_subset_contexts`로 fallback한다.

This avoids full-train artifacts carrying `train_pilot` provenance wording.

## Input Bundle

Predictions:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/adapter/predictions.jsonl
```

Geometry:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/geometry/verification.jsonl
```

Train GT subset:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/source_contract/relationships_train_full.json
```

Input counts:

| Input | Count |
| --- | ---: |
| prediction rows | 4,818,996 |
| geometry rows | 4,818,996 |
| selected train contexts | 3,738 |
| selected train scans | 1,157 |
| selected GT relations | 79,704 |

## Command

Launched in `tmux`:

```text
session: h002_open3dsg_train_full_rga_20260616_161755
log: logs/h002_open3dsg_train_full_rga_20260616_161755.log
exit: logs/h002_open3dsg_train_full_rga_20260616_161755.exit
```

Command:

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/train_rga_rows.py \
  --predictions-jsonl hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/adapter/predictions.jsonl \
  --geometry-jsonl hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/geometry/verification.jsonl \
  --subset-json hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/source_contract/relationships_train_full.json \
  --source-contract hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/source_contract/source_contract.json \
  --output-dir hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga \
  --source-id open3dsg_train_full \
  --scope-id open3dsg_train_full_all_ready_contexts \
  --label-source direct_join_relationships_train_full \
  --source-caveat 'Open3DSG full train; hypothesis-stage train-set diagnostic, not held-out paper result.' \
  --split-boundary 'train full only'
```

Reason for `tmux`:

```text
The run reads 4.8M prediction rows twice and writes a large match_rows.jsonl
artifact. It is long-running and disk-heavy, so it is tracked with logs and an
exit file.
```

## Initial Status Check

tmux status:

```text
running
```

Exit file:

```text
not yet written
```

Initial output:

```text
rga output directory exists, but no files have been written yet
```

Interpretation:

```text
This is expected early in the run because the tool first counts prediction rows
by context and loads train GT before writing match_rows.jsonl.
```

## Completion Evidence

Final process state:

```text
tmux session = not running
train_rga_rows.py process = not running
exit file = missing
log says: status=ready rows=4818996 hl=1828 lh=455598
```

Output files:

| Artifact | Count / Size |
| --- | ---: |
| `match_rows.jsonl` | 4,818,996 rows / 17G |
| `train_hl_queue.jsonl` | 1,828 rows / 2.1M |
| `train_lh_queue.jsonl` | 455,598 rows / 519M |
| `train_rga_summary.json` | status ready |
| `report.md` | written |

Summary status:

```text
status = ready
validation_error_count = 0
prediction_geometry_mismatches = 0
missing_identity_rows = 0
rank_gt_context_rows = 0
```

Input/output preservation:

| Item | Count |
| --- | ---: |
| prediction rows | 4,818,996 |
| geometry rows | 4,818,996 |
| rows written | 4,818,996 |
| ground-truth rows | 79,704 |
| ground-truth contexts | 3,738 |
| prediction contexts | 3,738 |

Geometry status after H002 mapping:

| H002 Status | Rows |
| --- | ---: |
| `satisfied` | 474,898 |
| `uncertain` | 490,410 |
| `unsatisfied` | 146,768 |
| `unsupported` | 3,706,920 |

Label status:

| Label Status | Rows |
| --- | ---: |
| `exact_match` | 61,227 |
| `family_match` | 137,978 |
| `pair_has_other_predicate` | 912,945 |
| `no_gt_for_pair` | 3,706,846 |

RGA top100 buckets:

| Bucket | Rows |
| --- | ---: |
| `RGA-HH` | 19,300 |
| `RGA-HL` | 1,828 |
| `RGA-HU` | 15,714 |
| `RGA-HM` | 336,910 |
| `RGA-LH` | 455,598 |
| `RGA-LL` | 144,940 |
| `RGA-LU` | 474,696 |
| `RGA-LM` | 3,370,010 |

Label-geometry buckets:

| Bucket | Rows |
| --- | ---: |
| `RGA-TP-GS` | 18,719 |
| `RGA-TP-GU` | 46 |
| `RGA-TP-GC` | 42,462 |
| `RGA-FP-GS` | 456,179 |
| `RGA-FP-GU` | 146,722 |
| `RGA-FP-GC` | 4,154,868 |

## RGA Metrics

| Metric | K=50 | K=100 |
| --- | ---: | ---: |
| `RGA-HL@K` | 3.02% | 4.96% |
| `RGA-valid@K` | 61.90% | 52.39% |
| `RGA-nonviolated@K` | 96.98% | 95.04% |
| `RGA-uncertain@K` | 35.08% | 42.65% |
| `RGA-coverage@K` | 2.91% | 9.86% |
| `RGA-LH-tail@K` | 42.61% | 42.37% |
| `RGA-LL-tail@K` | 13.25% | 13.48% |
| `RGA-LU-tail@K` | 44.14% | 44.15% |

Interpretation:

```text
Full train preserves the pilot-level pattern: high-semantic/low-geometry exists,
but the larger diagnostic mass is low-semantic/high-geometry. H002 should
therefore remain bidirectional and audit-aware rather than becoming only an
overconfidence detector.
```

## Expected Outputs

Output root:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/
```

Expected files:

```text
match_rows.jsonl
train_rga_summary.json
train_hl_queue.jsonl
train_lh_queue.jsonl
report.md
```

## Completion Gate

Pass criteria:

```text
summary.status = ready
input_counts.prediction_rows = 4,818,996
input_counts.geometry_rows = 4,818,996
validation.rows_written = 4,818,996
validation.prediction_geometry_mismatches = 0
validation.validation_error_count = 0
```

Process caveat:

```text
The planned exit file was not written by the tmux wrapper. Completion is verified
through the ready summary, output line counts, absence of a running process, and
the run log message.
```

The completion check must also record:

- geometry status counts.
- label status counts.
- RGA top50/top100 bucket counts.
- `RGA-HL@50/100`.
- `RGA-LH-tail@50/100`.
- queue counts.

## Boundary

Established:

- full-train RGA rows are materialized.
- prediction and geometry rows are row-preserved.
- direct train GT label status is available.
- full-train RGA-HL/RGA-LH distribution is available.
- prediction, geometry, and GT inputs are train-origin.
- validation/test rows are still unavailable.

Not established:

- controlled label mining.
- posterior revival evidence.

## Next TODO

Completed next action:

```text
full_train_controlled_label_mining
```

Result:

```text
60_full_train_controlled_mining.md
```

Original goal:

- mine controlled label/audit candidates from full-train HL/LH queues.
- balance by family, predicate, rank band, label status, and geometry status.
- prioritize `support_contact`, `relative_vertical`, and high-value
  `proximity` subsets while preserving dense-noise controls.
- keep validation/test unavailable.
