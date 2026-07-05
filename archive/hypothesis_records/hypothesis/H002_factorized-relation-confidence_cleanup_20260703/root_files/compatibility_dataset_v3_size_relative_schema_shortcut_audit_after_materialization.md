# H002 Size-Relative Schema Shortcut Audit After Materialization

## Result

```text
artifact_root = artifacts/compatibility_dataset_v3_size_relative_schema_shortcut_audit_after_materialization/
status = h002_compatibility_dataset_v3_size_relative_schema_shortcut_audit_after_materialization_ready_for_smoke_plan
selected_path = size_relative_smoke_ready_view_ready
validation_errors = 0
next_todo = compatibility_dataset_v3_size_relative_sanitized_view_smoke_plan_after_schema_audit
```

This stage audited the materialized `size_relative` same-G predicate-flip rows before
any learned smoke runner. It did not train a model, did not use validation/test data,
and did not modify H001 artifacts.

## Inputs

```text
input_artifact = artifacts/compatibility_dataset_v3_size_relative_candidate_materialization_after_plan/
input_status = h002_compatibility_dataset_v3_size_relative_candidate_materialization_after_plan_ready_for_schema_shortcut_audit
input_rows = 2400 primary model-safe rows
```

## Outputs

```text
feature_path_audit.csv
feature_path_violations.jsonl
shortcut_probe_results.csv
hidden_shortcut_probe_results.csv
group_integrity_audit.csv
group_integrity_errors.jsonl
smoke_ready_view.jsonl
summary.json
report.md
validation_errors.jsonl
```

## Counts

```text
primary_rows = 2400
primary C_e positive / negative = 1200 / 1200
group_integrity_rows = 1200
group_integrity_errors = 0
feature_path_violations = 0
smoke_ready_rows = 2400
```

## Main Shortcut Probes

```text
T_predicate_label_only = 0.500
T_relation_family_only = 0.500
G_exact_tuple_only = 0.500
G_single_log_volume_ratio_s_over_o = 0.500 AUROC
G_single_log_max_extent_ratio_s_over_o = 0.500 AUROC
G_single_log_footprint_area_ratio_s_over_o = 0.500 AUROC
G_single_log_vertical_extent_ratio_s_over_o = 0.500 AUROC
TG_exact_interaction = 1.000
```

Interpretation:

- `T_e` alone cannot solve the target.
- `G_e_size` alone cannot solve the target because each same-G group contains one
  compatible and one incompatible predicate row.
- `T_e x G_e_size` is intentionally perfect at the schema level. This is the target
  construction property that the later learned smoke must test with wrong-T and
  shuffled-G controls.

## Hidden Probe Results

```text
hidden_class_pair_only = 0.500
hidden_source_predicate_only = 0.500
hidden_anchor_predicate_only = 0.500
hidden_direction_only = 0.500
hidden_scan_only = 0.500
hidden_volume_band_only = 0.500
hidden_original_gt_anchor_flag = 1.000
hidden_direction_x_candidate_predicate = 1.000
```

The two high hidden probes are expected construction metadata. They are not present
in the model-safe feature blocks and therefore do not block the next smoke plan.

## Gate Decision

The schema/shortcut gate passed.

```text
schema_leakage_pass = true
allowed_single_feature_pass = true
group_integrity_pass = true
smoke_ready = true
```

The next stage should freeze the sanitized smoke-view plan and specify the learned
smoke runner, controls, and promotion gates. This audit still does not make
`size_relative` a solved relation family or a paper-level claim.
