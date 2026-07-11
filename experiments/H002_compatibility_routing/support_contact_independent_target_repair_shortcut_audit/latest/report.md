# Support/Contact Independent Target Shortcut Audit

## Status

```text
status = h002_support_contact_independent_target_repair_shortcut_audit_ready_with_warnings
validation_errors = 0
shortcut_probe_rows = 69
target_quality_warnings = 4
blocking_shortcut_warnings = 15
metric_rerun_allowed = false
next_todo = h002_support_contact_independent_target_repair_path_decision_after_shortcut_audit_when_requested
```

## Interpretation

This audit checks whether the support/contact independent target is safe
enough for later metric/training protocol planning.

Target-quality warnings:

- `positive_sparse_binary_target` severity `high`
- `majority_negative_baseline_too_high` severity `high`
- `mixed_predicate_class_pair_mass_too_small` severity `high`
- `supported_by_positive_boundary_too_small` severity `medium`

Blocking shortcut warnings:

- `multiclass` / `endpoint_id`: LOO acc `0.722917`, LOO macro `0.166667`, baseline `0.722917`, risk `high`
- `multiclass` / `geometry_rule_state`: LOO acc `0.997917`, LOO macro `0.833333`, baseline `0.722917`, risk `high`
- `multiclass` / `geometry_core_signature`: LOO acc `0.83125`, LOO macro `0.461159`, baseline `0.722917`, risk `high`
- `binary` / `predicate_x_class_pair`: LOO acc `0.929319`, LOO macro `0.704199`, baseline `0.908377`, risk `high`
- `binary` / `class_pair_x_token_tier`: LOO acc `0.884817`, LOO macro `0.576945`, baseline `0.908377`, risk `high`
- `binary` / `endpoint_id`: LOO acc `0.908377`, LOO macro `0.5`, baseline `0.908377`, risk `high`
- `binary` / `scan_id`: LOO acc `0.900524`, LOO macro `0.547056`, baseline `0.908377`, risk `medium`
- `binary` / `geometry_gap_bin`: LOO acc `0.884817`, LOO macro `0.576945`, baseline `0.908377`, risk `high`
- `binary` / `geometry_rule_state`: LOO acc `1.0`, LOO macro `1.0`, baseline `0.908377`, risk `high`
- `binary` / `geometry_core_signature`: LOO acc `0.95288`, LOO macro `0.742857`, baseline `0.908377`, risk `high`

Decision: do not open metric rerun, training, or solved-route wording from this target.
