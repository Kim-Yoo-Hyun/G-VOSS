# H002 Size-Relative Candidate Materialization After Plan

Date: 2026-06-29 KST

## Purpose

Frozen materialization plan에 따라 `size_relative` family의 train-only same-G
predicate-flip candidate rows를 생성했다. 이 단계는 row materialization과 schema precheck까지만
수행했으며, learned smoke나 schema/shortcut audit은 아직 수행하지 않았다.

## Artifact

```text
artifact_root = artifacts/compatibility_dataset_v3_size_relative_candidate_materialization_after_plan/
status = h002_compatibility_dataset_v3_size_relative_candidate_materialization_after_plan_ready_for_schema_shortcut_audit
selected_path = size_relative_same_g_candidates_ready_for_schema_shortcut_audit
validation_errors = 0
next_todo = compatibility_dataset_v3_size_relative_schema_shortcut_audit_after_materialization
```

Generated files:

- `candidate_rows.jsonl`
- `model_safe_main_view.jsonl`
- `model_safe_qe_view.jsonl`
- `hidden_manifest.jsonl`
- `group_manifest.jsonl`
- `schema_precheck.json`
- `cap_audit.csv`
- `quota_audit.csv`
- `selection_profile.json`
- `manifest.json`
- `summary.json`
- `report.md`
- `validation_errors.jsonl`

## Counts

```text
candidate_rows = 2572
group_rows = 1286
hidden_rows = 2572
model_safe_main_rows = 2400
model_safe_qe_rows = 2572
validation_errors = 0
```

Subset counts:

```text
primary_compatibility = 2400
diagnostic_ambiguous_size = 100
audit_gt_geometry_conflict = 72
```

Primary label balance:

```text
C_e positive / negative = 1200 / 1200
subject_bigger / subject_smaller groups = 600 / 600
bigger than / smaller than primary rows = 1200 / 1200
```

## Materialization Structure

Each primary group contains two rows with the same object pair and the same
continuous `G_e_size` values:

```text
row A: T_e = bigger than
row B: T_e = smaller than
```

If the subject is geometrically larger, `bigger than` is positive and `smaller than`
is negative. If the subject is geometrically smaller, the labels are reversed.

This preserves the intended H002 test: geometry-only sees identical `G_e_size` for
both rows in a group, so the primary target should require `T_e x G_e_size`
compatibility rather than a simple size threshold.

## Schema Precheck

```text
blocked_model_input_hits = 0
group_integrity_errors = 0
paired_geometry_control_groups = 1200
```

Cap audit:

```text
max_groups_per_class_pair = 232 / 240
max_groups_per_class_pair_direction = 116 / 120
max_groups_per_scan = 13 / 24
```

Selection profile:

```text
strict_candidates = 1728
selected_primary_groups = 1200
selected_class_pairs = 14
selected_scans = 361
skipped = {}
```

## Field Boundary

`model_safe_main_view.jsonl` contains:

- `T_e`: predicate text/label and relation family
- `G_e_size`: continuous log-ratio geometry features
- `labels`: target-only block for downstream audit/smoke runner

It does not expose class labels, class-pair, scan/object ids, GT/source/construction
fields, discretized direction fields, or `Z_e` as model input features. Those fields
are stored in `hidden_manifest.jsonl` for audit and controls.

## Boundary

- Train-only materialization.
- No validation/test source used.
- No learned smoke or model training run.
- No H001 artifacts modified.
- Not paper-level evidence.

## Next

```text
compatibility_dataset_v3_size_relative_schema_shortcut_audit_after_materialization
```
