# V35 Cross-Stratum Capacity Scan

Date: 2026-06-23 KST

## Purpose

v34에서 고정한 `controlled_cross_stratum_support_contact_contrast` plan이 실제
train-only queue 안에서 label sheet 생성 전 capacity/control gate를 통과하는지 확인했다.
이 단계는 label fill, target ingestion, posterior smoke가 아니다.

## Artifact

```text
artifacts/train_rga_full/open3dsg_train_full/rga/
  reliability_target_v16_cross_stratum_support_contact_contrast_capacity_scan/
    summary.json
    report.md
    capacity_by_cell.csv
    quota_feasibility.csv
    block_capacity.csv
    selection_preview_internal.jsonl
    shortcut_risk_precheck.json
    validation_errors.jsonl
```

Validation errors: `0`

Validation/test usage: `false`

Posterior smoke: `blocked`

## Status

```text
status = h002_reliability_target_v16_cross_stratum_support_contact_contrast_capacity_scan_blocked_capacity_or_controls
next_todo = reliability_target_v16_cross_stratum_support_contact_contrast_path_decision_after_capacity_scan
capacity_pass = false
validation_errors = 0
```

## Capacity Result

Raw/minimum quota capacity itself passed:

```text
P1 lying on HL eligible = 896 / target 100 / minimum 80
P2 lying on LH eligible = 26882 / target 100 / minimum 80
D1 standing on LH eligible = 23713 / target 24
C1 lower than LH eligible = 55221 / target 16
```

But cap/control selection failed:

```text
selected_by_cell = {
  P1_lie_hl_primary_overconfidence: 52,
  P2_lie_lh_primary_underconfidence: 98
}
selection_deficits = {
  P1_lie_hl_primary_overconfidence: 48,
  P2_lie_lh_primary_underconfidence: 2,
  D1_stand_lh_diversity_diagnostic: 24,
  C1_vertical_lower_control: 16
}
primary_mixed_blocks_available = 4
selected_primary_blocks_with_both_sides = 2
minimum_primary_blocks_required = 40
```

## Main Blocker

The primary `lying on` rows are not distributionally independent enough:

```text
HL geometry_status = unsatisfied: 896/896
LH geometry_status = satisfied: 26882/26882
HL reason_family = support_gap_large: 879/896, support_unsatisfied: 17/896
LH reason_family = support_near_contact_or_subtype_supported: 22056/26882, support_satisfied: 4826/26882
```

Thus, v16 has enough rows, but the target can still collapse to mismatch-construction
axes such as `geometry_status` or `reason_family`. This is exactly the failure the
capacity scan was designed to catch before producing a label sheet.

## Interpretation

This does not reject H002. It rejects the current v16 target-construction route as a
posterior-ready target.

The important distinction:

```text
row capacity = sufficient
independent contrast capacity = insufficient
posterior smoke = still blocked
```

If we force a label sheet now, the future classifier could appear to work by learning
`HL -> unsatisfied` and `LH -> satisfied`, rather than by learning factorized relation
reliability.

## Next

```text
reliability_target_v16_cross_stratum_support_contact_contrast_path_decision_after_capacity_scan
```

The next decision should choose one of:

- keep v16 only as diagnostic evidence and move to attachment/contact schema probe
- redefine cross-stratum blocks as broader audit slices without treating geometry-status cap as a side-level hard cap
- mine a different support/contact predicate or relation family where HL/LH do not deterministically equal geometry status
- move to multi-view-assisted audit only after a clean factorized target route is specified

