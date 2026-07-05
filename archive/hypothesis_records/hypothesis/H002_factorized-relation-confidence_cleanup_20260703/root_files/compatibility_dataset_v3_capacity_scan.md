# Compatibility Dataset V3 Capacity Scan

Artifact root:

```text
artifacts/compatibility_dataset_v3_capacity_scan/
```

Status:

```text
status = h002_compatibility_dataset_v3_capacity_scan_passed_ready_for_candidate_materialization
candidate_materialization_allowed = true
requires_axis_controls = true
validation_errors = 0
next_todo = compatibility_dataset_v3_candidate_materialization
```

## Result

The scan used full train-side Open3DSG `match_rows.jsonl`:

```text
match_rows_scanned = 4,818,996
relative_vertical_rows = 370,692
relative_vertical_rows_with_raw = 370,692
directed_pair_groups_with_any_vertical_predicate = 185,346
clear_same_geometry_groups_at_frozen_margin = 122,570
higher_positive_groups = 61,285
lower_positive_groups = 61,285
balanced_group_capacity = 122,570
```

The v3 capacity gate passes. There are far more than the requested 200 primary geometry groups,
and the two vertical directions are exactly balanced at the full candidate level.

## Frozen Margin

The contract margin was:

```text
abs(center_delta_z) >= 0.10m
abs(normalized_center_delta_z) >= 0.20
```

Sensitivity remains safely above the requested quota even at stricter margins:

```text
0.15m / 0.30 normalized -> 97,362 balanced groups
0.20m / 0.40 normalized -> 74,822 balanced groups
0.30m / 0.50 normalized -> 57,404 balanced groups
```

## Shortcut Risk

The target is feasible, but materialization must include axis controls:

```text
high_risk_axes = visible_pair
medium_risk_axes = object_label, subject_label
```

Meaning: exact subject/object label pairs can be direction-biased. For example, some pairs like
object-floor or object-ceiling naturally imply one vertical direction. The next materialization
should therefore:

- sample equal numbers of `higher_positive` and `lower_positive` groups;
- prioritize mixed-direction visible-pair cells;
- cap single-direction visible pairs;
- avoid a structural-only floor/wall/ceiling slice;
- report predicate-only, visible-pair-only, predicate+visible-pair, and rank-band shortcut probes.

## Support/Contact Probe

Support/contact remains secondary:

```text
standing on / lying on / supported by
```

Rows and raw OBB features exist, but the current `match_rows` artifact does not expose the
role/orientation, contact direction, surface normal, or visual/mesh evidence needed to make
support/contact the primary v3 predicate-conditioned target.

## Boundary

This step:

- is train-only;
- scans capacity only;
- does not materialize v3 rows;
- does not run learned smoke;
- does not use validation/test data;
- does not create paper-level evidence;
- does not modify H001 artifacts.

## Next

```text
compatibility_dataset_v3_candidate_materialization
```
