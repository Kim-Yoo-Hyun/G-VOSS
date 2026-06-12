# H002 Train Geometry Join

Last updated: 2026-06-12

## Purpose

`20_train_adapter_export.md`에서 생성한 Open3DSG train pilot predictions에 H001
geometry verifier를 붙인다. 이 단계의 목적은 H002 train-set RGA rows를 만들기 전,
semantic prediction row마다 geometry status와 `p_geom_valid`를 row-preserving하게
확보하는 것이다.

## Input Bundle

Predictions:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/adapter/predictions.jsonl
```

Prediction count:

```text
118,560
```

Geometry model:

```text
hypothesis/CAND-001/H001_geometry-grounded-verification/artifacts/calibration/p_geom_valid_smoke/model.json
```

Important boundary:

```text
p_geom_valid is geometry-only calibrated validity evidence.
It is not H002 posterior_edge_valid.
```

## Command

Launched in `tmux`:

```text
session: h002_train_geometry_join_20260612_045651
log: logs/h002_train_geometry_join_20260612_045651.log
exit: logs/h002_train_geometry_join_20260612_045651.exit
```

Command:

```bash
python3 hypothesis/CAND-001/H001_geometry-grounded-verification/tools/join_predictions.py \
  --predictions-jsonl hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/adapter/predictions.jsonl \
  --dataset-root local_dataset \
  --model-json hypothesis/CAND-001/H001_geometry-grounded-verification/artifacts/calibration/p_geom_valid_smoke/model.json \
  --output-dir hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/geometry \
  --selected-scans hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/source_contract/selected_scans.txt \
  --verification-policy point_subtype
```

Status:

```text
exit code: 0
manifest status: ready
```

## Output Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/geometry/verification.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/geometry/manifest.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/geometry/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/geometry/h002_summary.json
```

## Row Preservation

Verification:

```text
prediction rows: 118,560
verification rows: 118,560
rows_preserved: true
prediction_id_mismatches: 0
extra_prediction_rows: 0
extra_verification_rows: 0
```

This means H002 can now join semantic score and geometry status by
`prediction_id` without row loss.

## Geometry Coverage

Overall status under selected `point_subtype` policy:

| Status | Rows |
| --- | ---: |
| `satisfied` | 12,285 |
| `uncertain` | 11,841 |
| `violated` | 3,234 |
| `unsupported` | 91,200 |

Coverage:

| Item | Rows |
| --- | ---: |
| all predictions | 118,560 |
| primary geometry-checkable rows | 27,360 |
| unsupported-family rows | 91,200 |
| geometry available rows | 27,360 |
| calibration scored rows | 27,360 |
| missing point evidence rows | 5,421 |

Family status:

| Family | Satisfied | Uncertain | Violated | Unsupported |
| --- | ---: | ---: | ---: | ---: |
| `proximity` | 4,312 | 128 | 120 | 0 |
| `relative_vertical` | 2,764 | 3,592 | 2,764 | 0 |
| `support_contact` | 5,209 | 8,121 | 350 | 0 |
| `attachment_deferred` | 0 | 0 | 0 | 13,680 |
| `relative_horizontal` | 0 | 0 | 0 | 18,240 |
| `unsupported_first_pass` | 0 | 0 | 0 | 59,280 |

Support subtype counts:

| Support Subtype | Rows |
| --- | ---: |
| `legged_floor_support` | 1,050 |
| `rigid_object_on_furniture` | 6,334 |
| `soft_support_contact` | 6,296 |

## `p_geom_valid` Coverage

`p_geom_valid` is available for the geometry-checkable families only:

```text
p_geom_valid_non_null: 27,360
p_geom_valid_null: 91,200
```

By family:

| Family | N | Mean | P10 | P50 | P90 |
| --- | ---: | ---: | ---: | ---: | ---: |
| `proximity` | 4,560 | 0.6943 | 0.1566 | 0.8019 | 0.9991 |
| `relative_vertical` | 9,120 | 0.7792 | 0.0878 | 0.9581 | 0.9999 |
| `support_contact` | 13,680 | 0.3612 | 0.0109 | 0.2015 | 0.9854 |

Interpretation:

- H002 now has both deterministic geometry status and continuous geometry-only
  `p_geom_valid` for the primary relation families.
- `support_contact` has much lower median `p_geom_valid` than `proximity` and
  `relative_vertical`, so RGA-HL/RGA-LH must be family-aware.
- Unsupported families should be retained for denominator/coverage accounting,
  not treated as geometry violations.

## Current Boundary

Established:

- Train pilot semantic predictions and geometry rows are row-aligned.
- `p_geom_valid` is available for all 27,360 geometry-checkable rows.
- deterministic status buckets are available for `RGA-HL/RGA-LH` construction.

Not established:

- label match / exact-match / no-GT match status for this train pilot.
- train RGA-HL/RGA-LH summary.
- factorized reliability posterior.
- paper-level held-out results.

This join was executed as H002 hypothesis-stage work using the existing H001
joiner. If promoted to paper evidence, the same command path should be wrapped
or reproduced through the H002/H001 Docker experiment workflow.

## Next TODO

Next document:

```text
22_train_rga_rows.md
```

Required next work:

- join `adapter/predictions.jsonl`, `geometry/verification.jsonl`, and
  `relationships_train_pilot.json`.
- assign label-match status:
  - exact predicate match
  - pair has other GT predicate
  - no-GT pair
- compute train-set `RGA-HL@K` and `RGA-LH-tail@K`.
- output train HL/LH queues for audit.
