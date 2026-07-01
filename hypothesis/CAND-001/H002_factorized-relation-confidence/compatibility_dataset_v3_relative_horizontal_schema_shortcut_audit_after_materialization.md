# Relative-Horizontal Schema Shortcut Audit After Materialization

## Status

```text
status = h002_compatibility_dataset_v3_relative_horizontal_schema_shortcut_audit_after_materialization_ready_for_smoke_plan
selected_path = relative_horizontal_smoke_ready_view_ready
validation_errors = 0
next_todo = compatibility_dataset_v3_relative_horizontal_sanitized_view_smoke_plan_after_schema_audit
```

This step audits the materialized train-only `relative_horizontal` model-safe
view before any learned smoke. It does not train a model, use validation/test,
modify H001 artifacts, or promote the result to paper evidence.

## Command

```bash
python hypothesis/CAND-001/H002_factorized-relation-confidence/tools/compatibility_dataset_v3_relative_horizontal_schema_shortcut_audit_after_materialization.py
```

## Artifact Root

```text
artifacts/compatibility_dataset_v3_relative_horizontal_schema_shortcut_audit_after_materialization/
```

Key outputs:

- `summary.json`
- `feature_path_audit.csv`
- `feature_path_violations.jsonl`
- `shortcut_probe_results.csv`
- `hidden_shortcut_probe_results.csv`
- `group_integrity_audit.csv`
- `group_integrity_errors.jsonl`
- `smoke_ready_view.jsonl`
- `report.md`
- `validation_errors.jsonl`

## Gate Result

```text
primary_rows = 2,400
primary_label_counts = 1,200 / 1,200
smoke_ready_rows = 2,400

schema_leakage_pass = true
allowed_single_feature_pass = true
group_integrity_pass = true
validation_errors = 0
```

## Main Probe Results

Allowed single-factor probes:

```text
T_predicate_label_only = 0.500
T_relation_family_only = 0.500
G_exact_tuple_only = 0.500
G_single_delta_x_subject_minus_object = 0.500
G_single_delta_y_subject_minus_object = 0.500
G_single_horizontal_distance = 0.500
```

Intended interaction probes:

```text
TG_exact_interaction = 1.000
TG_signed_rule_interaction = 1.000
```

Interpretation:

- `T_e` alone does not explain the target.
- `G_e_horizontal` alone does not explain the target.
- The target is intentionally solvable only by matching predicate semantics with
  signed horizontal geometry.

## Hidden Probe Results

Low-risk hidden probes:

```text
axis_pair_only = 0.500
class_pair_only = 0.500
scan_only = 0.500
source_predicate_only = 0.500
anchor_predicate_only = 0.500
selected_axis_bucket_only = 0.500
```

High/medium hidden construction proxies:

```text
is_original_gt_anchor = 1.000
selected_frame_compatible = 1.000
source_predicate_x_candidate_predicate = 1.000
selected_axis_bucket_x_candidate_predicate = 1.000
axis_bucket_x_candidate_predicate = 0.849
axis_bucket_y_candidate_predicate = 0.873
```

These are expected construction or discretized rule proxies. They remain hidden
and are not present in the model-safe smoke-ready view.

## Boundary

- Train-only schema/shortcut audit.
- No validation/test source used.
- No learned smoke or training run.
- No H001 artifact modified.
- Not paper-level evidence.

