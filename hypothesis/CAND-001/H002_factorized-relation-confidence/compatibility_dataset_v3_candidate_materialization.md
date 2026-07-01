# Compatibility Dataset V3 Candidate Materialization

Artifact root:

```text
artifacts/compatibility_dataset_v3_candidate_materialization/
```

Status:

```text
status = h002_compatibility_dataset_v3_candidate_materialization_ready_for_schema_shortcut_audit
candidate_rows = 400
geometry_groups = 200
selected_visible_pair_cells = 100
higher_positive_groups = 100
lower_positive_groups = 100
validation_errors = 0
next_todo = compatibility_dataset_v3_schema_shortcut_audit
```

## What Was Materialized

The v3 dataset now contains controlled same-geometry `relative_vertical` pairs:

```text
same directed pair + same G_e + higher than
same directed pair + same G_e + lower than
```

Each geometry group emits exactly two rows:

- one compatible predicate row;
- one incompatible opposite-predicate row;
- identical `G_e_numeric.geometry_feature_hash`;
- the same directed subject/object pair;
- different `T_e.predicate_label`.

This directly targets:

```text
C_e = compatibility(T_e, G_e)
```

It is not a final `p_rel` human reliability dataset.

## Selection Policy

The capacity scan showed `visible_pair` as a high-risk shortcut axis. The materializer therefore did
not sample groups independently. It selected:

```text
100 mixed visible-pair cells
1 higher_positive group per visible-pair cell
1 lower_positive group per visible-pair cell
```

This makes `predicate + visible_pair` balanced by construction.

## Materialized Counts

```text
rows = 400
geometry_groups = 200
predicate counts:
  higher than = 200
  lower than = 200
compatibility labels:
  positive = 200
  negative = 200
direction groups:
  higher_positive = 100
  lower_positive = 100
```

Endpoint distribution:

```text
movable_object_pair = 140 groups
same_label_pair = 40 groups
structural_endpoint = 20 groups
```

## Shortcut Check Before Formal Audit

Row-level axis balance after selection:

```text
predicate_label majority accuracy = 0.500
visible_pair majority accuracy = 0.500
predicate + visible_pair majority accuracy = 0.500
endpoint_state majority accuracy = 0.500
subject_label majority accuracy = 0.500
object_label majority accuracy = 0.500
source_rank_band majority accuracy = 0.5375
```

No high-risk or medium-risk row-level shortcut axis remained in this materialized candidate set.

This does not replace the next formal schema shortcut audit. The next audit still must verify that
model views exclude labels, hidden controls, construction route, source predicate provenance, group
ids as features, and any other generated-field leakage.

## Outputs

```text
candidate_rows.jsonl
sanitized_model_view.jsonl
group_manifest.jsonl
group_integrity.csv
axis_balance.csv
selection_diagnostics.csv
rejection_reasons.csv
model_view_contract.json
summary.json
validation_errors.jsonl
report.md
```

## Boundary

This step:

- is train-only;
- materializes candidate rows only;
- does not run learned smoke;
- does not use validation/test data;
- does not create paper-level evidence;
- does not modify H001 artifacts.

## Next

```text
compatibility_dataset_v3_schema_shortcut_audit
```
