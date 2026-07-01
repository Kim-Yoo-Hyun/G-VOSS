# H002 Support/Contact Class-Pair Repair Capacity Scan

Default artifact:

```text
artifacts/compatibility_dataset_v3_independent_validity_support_contact_class_pair_repair_capacity_scan/
```

Status:

```text
status = h002_compatibility_dataset_v3_independent_validity_support_contact_class_pair_repair_capacity_scan_strict_blocked_class_pair_diagnostic_possible
validation_errors = 1
next_todo = compatibility_dataset_v3_independent_validity_support_contact_class_pair_repair_path_decision_after_capacity_scan
```

## Purpose

This stage tests the first repair option after the support/contact shortcut
audit: stronger class-pair and within-class contrast. The target question is
whether the full train-side support/contact pool contains enough mixed
accept/reject rows inside:

- `subject_class + object_class`
- `predicate + subject_class + object_class`
- `predicate + subject_class + object_class + rank_band`

The strict target is the second condition. It is the cleanest repair because it
directly controls the previous `predicate_x_class_pair` shortcut.

## Input

```text
source = train-side Open3DSG match_rows.jsonl
scanned rows = 4,818,996
support/contact family rows = 370,692
primary support/contact candidate rows = 8,631
predicates = lying on, standing on
```

Primary target policy:

```text
positive = exact GT match + geometry satisfied
negative = family/pair-other-predicate GT relation + geometry unsatisfied
no-GT rows = excluded
source Z_e required = true
raw G_e required = true
```

## Result

Full candidate availability:

```text
lying on positive / negative = 1,643 / 685
standing on positive / negative = 5,921 / 382
```

Repair capacity:

```text
class_pair mixed groups = 50
class_pair raw balanced capacity = 456
class_pair scan-capped capacity = 426

predicate_x_class_pair mixed groups = 13
predicate_x_class_pair raw balanced capacity = 104
predicate_x_class_pair scan-capped capacity = 88

predicate_x_class_pair_x_rank_band mixed groups = 18
predicate_x_class_pair_x_rank_band raw balanced capacity = 98
predicate_x_class_pair_x_rank_band scan-capped capacity = 88
```

Strict predicate-class capacity by predicate:

```text
lying on scan-capped capacity = 64
standing on scan-capped capacity = 24
```

Gate:

```text
strict_ready = false
diagnostic_class_pair_possible = true
min_strict_main_rows = 800
min_strict_per_predicate_rows = 200
min_strict_mixed_groups = 20
min_class_pair_diagnostic_rows = 400
```

## Interpretation

The first-choice repair does not support a main support/contact learned-smoke
target. The exact `predicate + subject_class + object_class` capacity is only
`88` scan-capped rows, and `standing on` contributes only `24` scan-capped rows.
That is too small and too imbalanced to claim that support/contact reliability
can be learned under strict predicate-class shortcut control.

The relaxed `subject_class + object_class` axis has `426` scan-capped rows, so a
small diagnostic contrast is possible. However, it does not fully remove the
previous `predicate_x_class_pair` shortcut. It can only answer a weaker
question: whether object-class-only shortcut remains after balancing class
pairs, not whether the full semantic predicate-class shortcut is removed.

## Decision

Do not run learned smoke as a main support/contact result. The next step is a
path decision:

```text
compatibility_dataset_v3_independent_validity_support_contact_class_pair_repair_path_decision_after_capacity_scan
```

The viable options are:

- run a small relaxed class-pair diagnostic, explicitly not main evidence;
- run object-class-masked diagnostic smoke on the previous `1200`-row target;
- freeze support/contact independent-validity as diagnostic-only and keep the
  earlier pose-conditioned support/contact result as scoped `C_e` mechanism
  evidence;
- search for a different GT/source construction if support/contact must become
  a main family.

## Boundary

- Train-only capacity scan.
- No validation/test usage.
- No row materialization.
- No learned smoke or model training.
- No calibrated `p_rel` / `p_obs` claim.
- No paper-level evidence.
- No H001 artifact modification.
