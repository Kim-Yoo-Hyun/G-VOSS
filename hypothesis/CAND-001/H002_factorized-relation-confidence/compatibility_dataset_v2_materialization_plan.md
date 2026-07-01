# Compatibility Dataset V2 Materialization Plan

Artifact root:

```text
artifacts/compatibility_dataset_v2_materialization_plan/
```

Status:

```text
status = h002_compatibility_dataset_v2_materialization_plan_ready
selected_route = v2_capacity_scan_before_materialization
direct_materialization_allowed = false
validation_errors = 0
next_todo = compatibility_dataset_v2_capacity_scan
```

## Decision

`h002_compatibility_dataset_v2` should not be directly materialized from the current
prototype or all-label-ready artifacts.

The selected route is:

```text
raw-witness feature seed
  -> v2 capacity scan
  -> v2 row materialization
  -> schema/control audit
  -> learned compatibility smoke
```

## Reason

The current artifacts are useful, but not sufficient as the final v2 dataset:

- `prototype_dataset_v1` has `support_contact` `50/49` and `relative_vertical` `17/18`
  compatibility rows, below the v2 minimum reportable `60/60` per primary family.
- all-label-ready support/vertical labels have `support_contact` `50/121` and
  `relative_vertical` `20/40` relation-reliability rows. This is a useful seed, but it is
  not a clean `C_e = compatibility(T_e, G_e)` target and still misses positive mass.
- raw-witness feature join v2 is the best geometry feature seed, but its rows are
  posterior-ready `baseline_inputs` records, not the new `T_e/Z_e/G_e/Q_e` dataset schema.
- the older v16 capacity scan shows that full-train candidate capacity exists, but also
  shows control/shortcut risk. A v2-specific capacity scan is required before row creation.

## Materialization Scope

Primary:

- `support_contact`: `standing on`, `lying on`, `supported by`
- `relative_vertical`: `higher than`, `lower than`

Diagnostic:

- `attachment_like`: `attached to`, `hanging on`, `connected to`

Future:

- `proximity`: `close by`

Deferred:

- `relative_horizontal`
- `containment`

## Next Capacity Scan Requirements

The next scan must verify:

- train-only provenance;
- `T_e`, `Z_e`, `G_e`, and `Q_e` separability;
- `C_e` excludes `Z_e`;
- `G_e` excludes predicate, family, source score/rank, labels, and construction keys;
- family-level positive/negative mass;
- predicate, endpoint-label, rank, and source-score balance;
- hidden construction probe risk;
- wrong-pair and shuffled-geometry availability;
- `relative_vertical` predicate flip and subject/object swap availability.

## Next

```text
compatibility_dataset_v2_capacity_scan
```
