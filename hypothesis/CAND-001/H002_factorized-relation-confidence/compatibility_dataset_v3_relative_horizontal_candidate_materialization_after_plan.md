# Relative-Horizontal Candidate Materialization After Plan

## Status

```text
status = h002_compatibility_dataset_v3_relative_horizontal_candidate_materialization_after_plan_ready_for_schema_shortcut_audit
selected_path = relative_horizontal_same_g_candidates_ready_for_schema_shortcut_audit
validation_errors = 0
next_todo = compatibility_dataset_v3_relative_horizontal_schema_shortcut_audit_after_materialization
```

This step materialized train-only `relative_horizontal` rows under the frozen
frame/Q_e plan. It did not train a model, use validation/test, modify H001
artifacts, or promote the result to paper evidence.

## Command

```bash
python hypothesis/CAND-001/H002_factorized-relation-confidence/tools/compatibility_dataset_v3_relative_horizontal_candidate_materialization_after_plan.py
```

## Artifact Root

```text
artifacts/compatibility_dataset_v3_relative_horizontal_candidate_materialization_after_plan/
```

Key outputs:

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
- `report.md`
- `summary.json`
- `validation_errors.jsonl`

## Counts

```text
candidate_rows = 3,040
group_rows = 1,520
model_safe_main_rows = 2,400
model_safe_qe_rows = 3,040

primary_groups = 1,200
primary_rows = 2,400
primary_positive_rows = 1,200
primary_negative_rows = 1,200

left/right groups = 600
front/behind groups = 600

axis_boundary_diagnostic_rows = 320
frame_disagreement_diagnostic_rows = 320
```

Primary predicate balance:

```text
left rows = 600
right rows = 600
front rows = 600
behind rows = 600

positive left rows = 300
positive right rows = 300
positive front rows = 300
positive behind rows = 300
```

## Schema Precheck

```text
blocked_model_input_hits = 0
group_integrity_errors = 0
paired_geometry_control_groups = 1,200
diagnostic_c_label_errors = 0
scan_max_groups = 11 <= 24
class_pair_max_groups = 109 <= 160
class_pair_axis_pair_max_groups = 59 <= 80
```

The model-safe main view contains only `T_e` predicate content and continuous
`G_e_horizontal` features. Source/GT/construction fields, endpoint IDs,
class-pair fields, frame-compatibility fields, and discretized axis buckets are
kept in the hidden manifest.

## Interpretation

This materialization creates the intended same-geometry predicate-flip target:
within each primary group, the two rows have identical `G_e_horizontal` and
differ only by the predicate in `T_e`.

Therefore:

- geometry-only should not solve the target;
- predicate-only should not solve the target because positive labels are balanced
  by predicate;
- a valid signal should come from `T_e x G_e_horizontal` compatibility;
- axis-boundary and frame-disagreement rows remain `Q_e`/diagnostic, not binary
  `C_e` target rows.

## Boundary

- Train-only artifact.
- No validation/test source used.
- No learned smoke or training run.
- No H001 artifact modified.
- Not paper-level evidence.

