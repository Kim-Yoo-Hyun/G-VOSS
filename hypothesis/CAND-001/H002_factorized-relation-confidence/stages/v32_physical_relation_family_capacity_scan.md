# V32 Physical Relation-Family Capacity Scan

Date: 2026-06-23 KST

## Purpose

v31 repair contract가 요구한 witness-matched `support_contact` 후보가 train queue에 실제로
충분한지 확인했다. 이 단계는 label sheet 생성이나 posterior smoke가 아니라, candidate mining
전에 capacity와 mixed-stratum 조건을 검증하는 단계다.

## Artifact

```text
artifacts/train_rga_full/open3dsg_train_full/rga/
  reliability_target_v15_physical_relation_family_capacity_scan/
    summary.json
    report.md
    raw_capacity_by_predicate_queue.csv
    eligible_capacity_by_predicate_queue.csv
    hard_filtered_by_predicate_queue.csv
    quota_feasibility.csv
    mixed_witness_strata_top.csv
    strict_strata_top.csv
    selection_preview_internal.jsonl
    validation_errors.jsonl
```

Validation errors: `0`

Validation/test usage: `false`

Posterior smoke: `blocked`

## Status

```text
status = h002_reliability_target_v15_physical_relation_family_capacity_scan_blocked_capacity_or_mixed_strata
eligible_target_rows = 107303
support_contact_rows_available = 51491
support_contact_rows_after_caps = 224
support_contact_mixed_witness_strata = 0
selection_preview_rows = 240
selection_deficits = {}
posterior_smoke_allowed = false
validation_errors = 0
next_todo = reliability_target_v15_physical_relation_family_path_decision_after_capacity_scan
```

## Key Result

수량은 충분하다.

```text
support_contact lying on eligible = 27778
support_contact standing on eligible = 23713
relative_vertical lower than eligible = 55812
```

Cap을 적용해도 v15 preview는 채울 수 있다.

```text
lying on = 192
standing on = 32
lower than = 16
total = 240
```

하지만 selected preview는 전부 `LH`이고 geometry status도 전부 `satisfied`다.

```text
selected_queue_kind = LH:240
selected_geometry_status = satisfied:240
```

v15의 핵심 gate였던 mixed witness stratum은 0개다.

```text
required_mixed_witness_strata = 8
observed_mixed_witness_strata = 0
```

## Interpretation

이 실패는 row count 부족이 아니다. 현재 RGA construction에서는 semantic-high/geometry-low
`HL` row와 semantic-low/geometry-high `LH` row가 geometry status, `p_geom_bin`, reason
signature, witness bucket을 공유하지 않는다. 즉 같은 witness stratum 안에서 HL/LH를 같이
요구하면, 정의상 거의 만나기 어렵다.

따라서 v15 contract의 다음 판단은 다음 중 하나여야 한다.

- mixed witness stratum 요구를 완화하고 다른 independence control을 도입한다.
- HL/LH cross-stratum contrast로 문제를 다시 정의한다.
- `support_contact` current queue를 diagnostic evidence로 고정하고 `attachment_deferred` witness schema probe로 이동한다.

## Boundary

This is train-only capacity evidence.

It is not:

- a label-ready sheet
- posterior performance evidence
- paper-level benchmark evidence
- validation/test evidence
- a change to H001 or paper artifacts

## Next

```text
reliability_target_v15_physical_relation_family_path_decision_after_capacity_scan
```
