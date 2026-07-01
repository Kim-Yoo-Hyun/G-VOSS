# H002 Official Materialization Schema Audit

## Status

```text
status = h002_official_materialization_schema_audit_ready_with_shortcut_warnings
selected_path = schema_audit_ready_select_metric_protocol_freeze_with_caveats
validation_errors = 0
shortcut_warnings = 1
next_todo = compatibility_dataset_v3_official_metric_protocol_freeze_after_schema_audit
```

## Runtime Boundary

- materialized rows: `23062`
- official validation metric: `false`
- paper metric: `false`
- official test usage: `false`

## Label Balance

| Family | Rows | Label 0 | Label 1 | Majority | Dataset Weight |
| --- | ---: | ---: | ---: | ---: | ---: |
| `ALL` | 23062 | 15439 | 7623 | 0.669456 | 1.000000 |
| `relative_horizontal` | 18764 | 13290 | 5474 | 0.708271 | 0.813633 |
| `relative_vertical` | 780 | 390 | 390 | 0.500000 | 0.033822 |
| `size_relative` | 340 | 170 | 170 | 0.500000 | 0.014743 |
| `support_contact` | 3178 | 1589 | 1589 | 0.500000 | 0.137802 |

## Shortcut Summary

- high shortcut rows: `1`
- blocking controls: `0`
- metric protocol must report family-wise, macro-average, weighted-average, and route controls.

## Boundary

- This stage audits inputs only; no AUROC/F1 metric was computed.
- `Z_e` remains excluded from the main `C_e` compatibility metric.
- `support_contact` remains a challenging route, not a solved claim.
