# H002 Support/Contact Harder Route Schema Shortcut Audit

## Status

```text
status = h002_support_contact_harder_schema_shortcut_audit_ready_with_warnings
selected_path = schema_shortcut_audit_ready_select_metric_protocol_freeze
validation_errors = 0
shortcut_warnings = 3
next_todo = compatibility_dataset_v3_support_contact_harder_route_metric_protocol_freeze_after_schema_shortcut_audit
```

## Judgment

The richer support/contact materialization passes schema and control-readiness checks.
Shortcut warnings remain and must be handled in the metric protocol.

## Warnings

- `primary_predicate_only`: majority accuracy `0.853996`, risk `medium`
- `hidden_predicate_x_class_pair`: majority accuracy `0.993707`, risk `high`
- `class_ablation_predicate_x_class_pair`: majority accuracy `0.993707`, risk `high`

## Boundary

- No metric was run.
- Official test was not used.
- `support_contact` remains challenging, not solved.
