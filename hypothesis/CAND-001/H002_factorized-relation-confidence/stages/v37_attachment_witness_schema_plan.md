# V37 Attachment Witness Schema Plan

Date: 2026-06-23 KST

## Purpose

v36에서 선택한 `attachment_deferred_witness_schema_probe` route를 실제 capacity scan으로
넘길 수 있도록 typed witness schema, predicate template, capacity-scan contract, label-surface
boundary를 고정했다.

이 단계는 label sheet 생성, label fill, posterior smoke가 아니다.

## Artifact

```text
artifacts/train_rga_full/open3dsg_train_full/rga/
  reliability_target_v17_attachment_deferred_witness_schema_probe_plan/
    summary.json
    report.md
    witness_schema.json
    witness_schema.md
    predicate_templates.csv
    capacity_scan_contract.json
    label_surface_contract.json
    validation_errors.jsonl
```

Validation errors: `0`

Validation/test usage: `false`

Posterior smoke: `blocked`

## Status

```text
status = h002_reliability_target_v17_attachment_deferred_witness_schema_probe_plan_ready_for_capacity_scan
next_todo = reliability_target_v17_attachment_deferred_witness_schema_capacity_scan
validation_errors = 0
```

## Attachment Snapshot

v14 feasibility에서 attachment family는 row mass는 충분하지만 current geometry policy에서는
전부 unsupported였다.

```text
attachment_rows = 556038
attached_to_rows = 185346
hanging_on_rows = 185346
connected_to_rows = 185346
unique_directed_pairs = 185346
checkable_rows_before_schema = 0
raw_feature_rows_before_schema = 0
unsupported_share_before_schema = 1.0
```

따라서 이번 route의 목적은 candidate mining이 아니라, unsupported family를
geometry-checkable evidence family로 변환할 수 있는지 먼저 검증하는 것이다.

## Witness Schema

Predicate scope:

```text
attached to
hanging on
connected to
```

Evidence factors:

```text
near_contact_distance
projected_overlap
relative_vertical_anchor
floor_support_confound
anchor_affordance_bucket
coverage
uncertainty
```

Current raw feature source:

```text
match_rows directed_pair_id join
primary source = support_contact rows with geometry.raw_features
fallback source = relative_vertical rows with geometry.raw_features
```

이 join이 필요한 이유는 attachment row 자체는 현재 `unsupported_family`라 `raw_features`가
없지만, 같은 directed object pair의 OBB pair feature는 support/vertical family row에 존재하기
때문이다.

## Predicate Policy

- `attached to`: near-contact / anchor plausibility 중심 candidate.
- `hanging on`: vertical anchor / non-floor support / hanging plausibility 중심 candidate.
- `connected to`: OBB geometry만으로 functional connection을 확정하기 어렵기 때문에 처음에는 diagnostic으로 둔다.

Multi-view는 현재 deployable model input이 아니다. 이후 audit/confirmation evidence로만 사용한다.

## Capacity Scan Contract

Next scan must:

```text
minimum_raw_feature_join_coverage = 0.95
preview_total_rows = 240
attached_to_supported_and_counter_capacity_min = 80
hanging_on_supported_and_counter_capacity_min = 80
connected_to_diagnostic_capacity_min = 60
preview_rows_after_caps_min = 160
```

The capacity scan must separate:

```text
supported_candidate
contradicted_candidate
uncertain_candidate
missing_geometry
unsupported_template
```

## Boundary

This is train-only hypothesis planning.

It is not:

- a label-ready sheet
- posterior performance evidence
- validation/test evidence
- paper-level benchmark evidence
- a change to H001 or paper artifacts

## Next

```text
reliability_target_v17_attachment_deferred_witness_schema_capacity_scan
```

