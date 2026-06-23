# V38 Attachment Witness Capacity Scan

Date: 2026-06-23 KST

## Purpose

v37에서 고정한 `attachment_deferred` typed witness schema가 train-only
`match_rows.jsonl`에서 실제 capacity를 갖는지 확인했다. 이 단계는 같은
`directed_pair_id`를 가진 support/vertical raw geometry를 attachment rows에 join하고,
`attached to`, `hanging on`, `connected to`에 대한 provisional witness state를 계산한다.

이 단계는 label sheet 생성, label fill, posterior smoke가 아니다.

## Artifact

```text
artifacts/train_rga_full/open3dsg_train_full/rga/
  reliability_target_v17_attachment_deferred_witness_schema_capacity_scan/
    summary.json
    report.md
    capacity_by_cell.csv
    predicate_counts.csv
    provisional_status_counts.csv
    anchor_bucket_counts.csv
    uncertainty_flag_counts.csv
    raw_feature_join_summary.json
    selection_preview_internal.jsonl
    validation_errors.jsonl
```

Validation errors: `0`

Validation/test usage: `false`

Posterior smoke: `blocked`

## Status

```text
status = h002_reliability_target_v17_attachment_deferred_witness_schema_capacity_scan_passed_ready_for_path_decision
next_todo = reliability_target_v17_attachment_deferred_witness_schema_path_decision_after_capacity_scan
capacity_pass = true
validation_errors = 0
```

## Join Result

```text
attachment_rows = 556038
joined_rows = 556038
raw_feature_join_coverage = 1.000000
pair_geometry_join_keys = 185346
missing_raw_feature_rows = 0
```

Attachment rows were previously fully `unsupported_family`, but the same directed
object pairs have pair-level OBB geometry through support/contact or vertical rows.
The schema therefore has enough raw geometry coverage for a capacity decision.

## Capacity Result

```text
A1 attached supported candidates = 54034
A2 attached contradicted/uncertain candidates = 131312
H1 hanging supported candidates = 25457
H2 hanging contradicted/uncertain candidates = 159889
C1 connected near/overlap diagnostic candidates = 105712
C2 connected contradicted/uncertain diagnostic candidates = 79634
U1 missing/uncertain coverage audit candidates = 381295
```

Preview after caps:

```text
selected_preview_rows = 240
selection_deficits = {}
selected_by_cell =
  A1: 40
  A2: 40
  H1: 40
  H2: 40
  C1: 30
  C2: 30
  U1: 20
```

The preview spans:

```text
selected_scan_count = 202
selected_subgraph_count = 230
selected_directed_pair_count = 240
selected_visible_pair_count = 199
```

## Interpretation

The capacity scan supports the next path decision:

```text
typed attachment witness capacity = sufficient
label sheet creation = still blocked
posterior smoke = still blocked
next step = decide whether candidate mining is allowed
```

The important caveat is that `connected to` remains diagnostic. OBB proximity and
overlap can suggest possible connection evidence, but functional connection may
require visual/mesh confirmation. Multi-view remains audit/confirmation evidence
only at this stage.

## Boundary

This is train-only schema capacity evidence.

It is not:

- a label-ready sheet
- posterior performance evidence
- validation/test evidence
- paper-level benchmark evidence
- a change to H001 or paper artifacts

## Next

```text
reliability_target_v17_attachment_deferred_witness_schema_path_decision_after_capacity_scan
```

