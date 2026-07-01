# Compatibility Dataset V2 Capacity Scan

Artifact root:

```text
artifacts/compatibility_dataset_v2_capacity_scan/
```

Status:

```text
status = h002_compatibility_dataset_v2_capacity_scan_passed_with_controls_ready_for_candidate_materialization
decision = capacity_pass_but_direct_hl_lh_target_blocked_generate_counterfactuals_and_repackage_raw_witness
row_materialization_allowed_with_controls = true
direct_hl_lh_target_allowed = false
learned_smoke_allowed = false
validation_errors = 0
next_todo = compatibility_dataset_v2_candidate_materialization
```

## Result

Full-train queue scan:

```text
HL queue rows scanned = 1,828
LH queue rows scanned = 455,598
```

Primary family capacity:

```text
support_contact positive / negative = 74,364 / 896
relative_vertical positive / negative = 111,032 / 592
```

Both primary families pass the requested v2 class-mass requirement:

```text
support_contact requested = 120 / 120
relative_vertical requested = 80 / 80
```

## Critical Caveat

This does not mean a direct HL/LH target is usable.

Direct HL/LH target construction remains blocked because:

- `queue_kind` separates positive and negative by construction;
- `geometry_status` separates positive and negative by construction;
- `rank_band` is strongly coupled with HL/LH;
- predicate balance is poor on the negative side.

Observed predicate imbalance:

```text
support_contact positive = lying on 26,882 / standing on 23,713 / supported by 23,769
support_contact negative = lying on 896 / standing on 0 / supported by 0

relative_vertical positive = higher than 55,811 / lower than 55,221
relative_vertical negative = higher than 1 / lower than 591
```

## Decision

Materialization is allowed only with controls:

- join selected prediction ids to raw-witness numeric `G_e`;
- repackage rows into `T_e`, `Z_e`, `G_e`, and `Q_e`;
- use `C_e = compatibility(T_e, G_e)` only;
- keep `Z_e`, rank, queue kind, geometry status, and target construction fields out of `C_e`;
- generate `support_contact` negatives using wrong-pair, shuffled-geometry, and contact-gap/support perturbation controls;
- generate `relative_vertical` negatives using predicate flip and subject/object swap controls;
- run hidden shortcut audit before any learned smoke.

`attachment_like` remains diagnostic-only for `Q_e`, observability, and failure taxonomy.

## Next

```text
compatibility_dataset_v2_candidate_materialization
```
