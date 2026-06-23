# V39 Attachment Path Decision

Date: 2026-06-23 KST

## Purpose

v38에서 `attachment_deferred` typed witness schema capacity가 통과된 뒤,
이 route를 candidate mining으로 넘길지 결정했다. 이 단계는 label sheet 생성이나
posterior smoke가 아니라 path decision이다.

## Artifact

```text
artifacts/train_rga_full/open3dsg_train_full/rga/
  reliability_target_v17_attachment_deferred_witness_schema_path_decision_after_capacity_scan/
    summary.json
    report.md
    option_matrix.json
    selected_plan.json
    validation_errors.jsonl
```

Validation errors: `0`

Validation/test usage: `false`

Posterior smoke: `blocked`

## Status

```text
status = h002_reliability_target_v17_attachment_deferred_witness_schema_path_decision_select_attachment_candidate_mining
selected_path = select_v18_attachment_deferred_candidate_mining_attached_hanging_primary_connected_diagnostic
next_todo = reliability_target_v18_attachment_deferred_candidate_mining
validation_errors = 0
```

## Decision

v18 candidate mining으로 진행한다.

단, primary binary target 후보는 다음 두 relation으로 제한한다.

```text
attached to
hanging on
```

`connected to`는 diagnostic-only로 유지한다.

## Rationale

`attached to`와 `hanging on`은 supported/counter 또는 uncertain cell capacity가 모두
충분하고, v16 `support_contact`에서 반복적으로 발생한 `HL ~= unsatisfied`,
`LH ~= satisfied` shortcut에 덜 직접적으로 묶인다.

반면 `connected to`는 near-contact 또는 overlap만으로 relation reliability를 확정하기 어렵다.
두 object가 가까워도 실제 기능적 연결이 아닐 수 있고, 멀어 보여도 cable, pipe, hinge,
device context처럼 point/OBB geometry에 잘 드러나지 않는 연결일 수 있다. 따라서 현재 단계에서는
primary binary label이 아니라 diagnostic/audit row로만 둔다.

## Evidence

```text
attachment_rows = 556038
joined_rows = 556038
raw_feature_join_coverage = 1.000000
selection_deficits = {}
selected_preview_rows = 240
selected_scan_count = 202
selected_subgraph_count = 230
selected_directed_pair_count = 240
```

v18 candidate mining contract:

```text
primary_binary_candidate_rows = 160
diagnostic_rows = 60
uncertainty_audit_rows = 20
primary_cells =
  A1 attached supported: 40
  A2 attached counter/uncertain: 40
  H1 hanging supported: 40
  H2 hanging counter/uncertain: 40
diagnostic_cells =
  C1 connected near/overlap: 30
  C2 connected counter/uncertain: 30
audit_cells =
  U1 missing/uncertain coverage: 20
```

## Boundary

This is train-only path-decision evidence.

It authorizes:

- hidden-field-safe candidate mining
- primary `attached to` / `hanging on` label packet construction
- diagnostic `connected to` audit rows

It does not authorize:

- direct label sheet creation from the v38 internal preview
- posterior smoke
- validation/test usage
- paper-level benchmark claims
- multi-view as model input

## Next

```text
reliability_target_v18_attachment_deferred_candidate_mining
```
