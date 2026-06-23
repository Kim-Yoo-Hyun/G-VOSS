# V36 Cross-Stratum Path Decision

Date: 2026-06-23 KST

## Purpose

v35 capacity scan이 `blocked_capacity_or_controls`로 끝난 뒤, v16
`controlled_cross_stratum_support_contact_contrast` route를 계속 밀고 갈지,
diagnostic-only로 고정할지, 다음 relation-family route로 이동할지 결정했다.

## Artifact

```text
artifacts/train_rga_full/open3dsg_train_full/rga/
  reliability_target_v16_cross_stratum_support_contact_contrast_path_decision_after_capacity_scan/
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
status = h002_reliability_target_v16_cross_stratum_path_decision_select_attachment_deferred_witness_schema_probe
selected_path = freeze_v16_diagnostic_select_v17_attachment_deferred_witness_schema_probe
next_todo = reliability_target_v17_attachment_deferred_witness_schema_probe_plan
validation_errors = 0
```

## Decision

v16 route는 posterior-ready target으로 승격하지 않고 diagnostic-only로 고정한다.
다음 route는 `attachment_deferred_witness_schema_probe`로 선택한다.

## Rationale

v16의 실패는 row count 부족이 아니다.

```text
lying_on_hl_eligible = 896
lying_on_lh_eligible = 26882
standing_on_lh_eligible = 23713
lower_than_lh_eligible = 55221
```

하지만 core contrast가 독립적이지 않다.

```text
HL side ~= geometry_status unsatisfied
LH side ~= geometry_status satisfied
primary_mixed_blocks_available = 4
selected_primary_blocks_with_both_sides = 2
```

따라서 geometry-status/reason caps를 완화해서 label sheet를 만들면 target이 쉬워질 수는
있지만, H002가 검증하려는 relation reliability 문제가 아니라 construction artifact를
검증하게 된다.

## Rejected Options

- `create_v16_label_sheet_now`: capacity/control gate가 실패했으므로 reject.
- `relax_geometry_status_and_reason_caps`: shortcut을 허용하므로 reject.
- `mine_more_lying_on_rows`: raw row count는 이미 충분하므로 reject.
- `try_more_support_contact_predicates_immediately`: `standing on` HL이 hard filter 이후 0개이고, support/contact는 현재 `lying on` 중심으로 geometry-status coupling이 강하므로 보류.
- `add_multi_view_as_model_input_now`: clean target이 없으므로 deployable input으로 쓰지 않고 audit evidence로만 유지.

## Selected Next Route

```text
attachment_deferred_witness_schema_probe
```

Relation scope:

```text
attached to
hanging on
connected to
```

Initial witness axes:

```text
contact_or_near_contact_distance
relative_pose_and_vertical_anchor_plausibility
surface_or_support_normal_alignment_if_available
containment_or_overlap_proxy_when_relevant
object_affordance_or_attachment_context_bucket
coverage_state
uncertainty_state
```

Attachment route가 더 적합한 이유는 현재 `lying on` support/contact처럼 단일 support gap 또는
geometry status 하나로 쉽게 환원되지 않을 가능성이 크기 때문이다. 다만 현재 RGA에서는
attachment family가 deferred/unsupported 상태였으므로, 바로 candidate mining을 하지 않고
witness schema probe부터 진행한다.

## Boundary

This is train-only hypothesis path decision evidence.

It is not:

- a new label sheet
- posterior performance evidence
- validation/test evidence
- paper-level benchmark evidence
- a change to H001 or paper artifacts

## Next

```text
reliability_target_v17_attachment_deferred_witness_schema_probe_plan
```

