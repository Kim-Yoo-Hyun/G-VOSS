# H002 Full Train Geometry Join

Last updated: 2026-06-16

## Purpose

`57_full_train_adapter_export.md`에서 생성한 full-train Open3DSG prediction rows에
H001 frozen geometry verifier evidence를 붙인다. 이 단계는 full-train RGA rows를 만들기
전, 각 semantic prediction row에 deterministic geometry status와 geometry-only
continuous score인 `p_geom_valid`를 row-preserving하게 확보하는 gate다.

## Decision

Current status:

```text
full_train_geometry_join_ready_with_exit_file_caveat
```

Meaning:

```text
The full-train geometry artifact is complete and manifest.status = ready.
The tmux session has ended and no join process remains, but the wrapper did not
write the planned exit file. Treat this as a logging caveat, not a scientific
artifact blocker, because manifest status, row count, and errors are verified.
```

## Input Bundle

Predictions:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/adapter/predictions.jsonl
```

Prediction count:

```text
4,818,996
```

Selected train scans:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/source_contract/selected_scans.txt
```

Selected scan count:

```text
1,157
```

Geometry model:

```text
archive/hypothesis_records/hypothesis/CAND-001/H001_geometry-grounded-verification/artifacts/calibration/p_geom_valid_smoke/model.json
```

Important boundary:

```text
p_geom_valid is geometry-only calibrated validity evidence.
It is not H002 posterior_edge_valid.
```

## Command

Launched in `tmux`:

```text
session: h002_open3dsg_train_full_geometry_20260616_120342
log: logs/h002_open3dsg_train_full_geometry_20260616_120342.log
exit: logs/h002_open3dsg_train_full_geometry_20260616_120342.exit
```

Command:

```bash
python3 src/geocalib/join_predictions.py \
  --predictions-jsonl hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/adapter/predictions.jsonl \
  --dataset-root local_dataset \
  --model-json archive/hypothesis_records/hypothesis/CAND-001/H001_geometry-grounded-verification/artifacts/calibration/p_geom_valid_smoke/model.json \
  --output-dir hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/geometry \
  --selected-scans hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/source_contract/selected_scans.txt \
  --verification-policy point_subtype
```

Reason for `tmux`:

```text
The input has 4.8M prediction rows and the output is expected to be large. This
is a long-running hypothesis-stage join, so it is tracked through logs and an
exit file rather than blocking the interactive session.
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

Initial log:

```text
empty
```

Interpretation:

```text
This is expected early in the run because the joiner first scans predictions to
collect support-contact point-evidence object ids before writing
verification.jsonl.
```

## Completion Evidence

Final process state:

```text
tmux session = not running
join_predictions.py process = not running
exit file = missing
```

Output files:

```text
verification.jsonl
manifest.json
report.md
```

Manifest summary:

```text
manifest.status = ready
selected_verification_policy = point_subtype
errors = 0
warnings = 9
```

Row preservation:

| Item | Count / Status |
| --- | ---: |
| predictions | 4,818,996 |
| verification rows | 4,818,996 |
| rows preserved | true |

Geometry coverage:

| Item | Count |
| --- | ---: |
| primary family rows | 1,112,076 |
| unsupported family rows | 3,706,920 |
| geometry available rows | 1,112,076 |
| calibration scored rows | 1,112,076 |
| missing point evidence rows | 226,359 |

Status counts under selected `point_subtype` policy:

| Status | Rows |
| --- | ---: |
| `satisfied` | 474,898 |
| `uncertain` | 490,410 |
| `violated` | 146,768 |
| `unsupported` | 3,706,920 |

Family status:

| Family | Satisfied | Uncertain | Violated | Unsupported |
| --- | ---: | ---: | ---: | ---: |
| `proximity` | 171,326 | 7,328 | 6,692 | 0 |
| `relative_vertical` | 124,604 | 121,484 | 124,604 | 0 |
| `support_contact` | 178,968 | 361,598 | 15,472 | 0 |
| `attachment_deferred` | 0 | 0 | 0 | 556,038 |
| `relative_horizontal` | 0 | 0 | 0 | 741,384 |
| `unsupported_first_pass` | 0 | 0 | 0 | 2,409,498 |

Support subtype counts:

| Support Subtype | Rows |
| --- | ---: |
| `legged_floor_support` | 43,746 |
| `rigid_object_on_furniture` | 276,414 |
| `soft_support_contact` | 235,878 |

Warnings:

```text
9 invalid_obb warnings with non_positive_aabb_extent
```

These warnings are retained in `manifest.json`. They do not block row
preservation or geometry join readiness.

## Expected Outputs

Output root:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/geometry/
```

Expected files after completion:

```text
verification.jsonl
manifest.json
report.md
```

## Completion Gate

Pass criteria:

```text
manifest.status = ready
counts.predictions = 4,818,996
counts.verification_rows = 4,818,996
counts.rows_preserved = true
errors = []
```

Process caveat:

```text
The planned exit file was not written by the tmux wrapper. Completion is verified
through manifest.status, row count, absence of a running process, and generated
report/log artifacts.
```

The completion check must also record:

- `by_status`
- `by_family_status`
- `primary_family_rows`
- `unsupported_family_rows`
- `calibration_scored_rows`
- `missing_point_evidence_rows`
- `support_subtype_counts`

## Verification Commands

Check session:

```bash
tmux list-sessions | rg h002_open3dsg_train_full_geometry_20260616_120342
```

Check exit:

```bash
cat logs/h002_open3dsg_train_full_geometry_20260616_120342.exit
```

Check output row count:

```bash
wc -l hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/geometry/verification.jsonl
```

Check manifest:

```bash
python3 -m json.tool hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/geometry/manifest.json
```

## Boundary

Established:

- full-train geometry join artifact is complete.
- every prediction row has a verification row.
- deterministic geometry status is available.
- `p_geom_valid` is available for 1,112,076 geometry-checkable rows.
- train-origin predictions and train selected scans are the inputs.
- validation/test rows are still unavailable.

Not established:

- full-train RGA bucket distribution.
- controlled label mining.
- posterior revival evidence.

## Next TODO

Next action:

```text
full_train_rga_rows
```

Goal:

- join full-train predictions, geometry verification rows, and
  `relationships_train_full.json`.
- map H001 `violated` to H002 `unsatisfied`.
- compute full-train RGA-HL/RGA-LH distribution.
- keep validation/test unavailable.
