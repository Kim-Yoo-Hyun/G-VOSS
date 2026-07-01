# Compatibility Dataset V3 Official Candidate Materialization Schema Audit After Docker Implementation

## Status

```text
runtime_root = experiments/H002_compatibility_routing/official_schema_audit/latest/
artifact_root = artifacts/compatibility_dataset_v3_official_candidate_materialization_schema_audit_after_docker_implementation/
status = h002_compatibility_dataset_v3_official_candidate_materialization_schema_audit_after_docker_implementation_ready_with_caveats
selected_path = schema_audit_ready_select_official_metric_protocol_freeze
validation_errors = 0
shortcut_warnings = 1
next_todo = compatibility_dataset_v3_official_metric_protocol_freeze_after_schema_audit
```

## Result

Official materialized rows passed schema and separation checks.

| Check | Result |
| --- | ---: |
| schema violations | 0 |
| blocked field hits | 0 |
| runtime validation errors | 0 |
| model-safe rows | 23062 |
| hidden rows | 23062 |
| model-safe missing hidden | 0 |
| hidden missing model-safe | 0 |

## Label Balance

| Family | Rows | Label 0 | Label 1 | Majority | Dataset Weight |
| --- | ---: | ---: | ---: | ---: | ---: |
| `ALL` | 23062 | 15439 | 7623 | 0.669456 | 1.000000 |
| `relative_horizontal` | 18764 | 13290 | 5474 | 0.708271 | 0.813633 |
| `relative_vertical` | 780 | 390 | 390 | 0.500000 | 0.033822 |
| `size_relative` | 340 | 170 | 170 | 0.500000 | 0.014743 |
| `support_contact` | 3178 | 1589 | 1589 | 0.500000 | 0.137802 |

## Shortcut Caveat

One high shortcut warning remains:

| Family | Probe | Majority accuracy | Interpretation |
| --- | --- | ---: | --- |
| `support_contact` | `predicate_x_class_pair` | 0.993707 | blocks solved/main support-contact claim |

This warning does not block the next metric protocol freeze, but it constrains claim wording.
`support_contact` must remain a challenging/diagnostic route unless a stricter controlled protocol
is created later.

## Required Next Protocol

The next official metric protocol must require:

- per-family AUROC,
- macro-family AUROC,
- weighted-family AUROC,
- overall AUROC as secondary only,
- wrong-`T` control,
- shuffled-`G` control,
- family-specific controls,
- `Z_e` exclusion from main `C_e`,
- `support_contact` challenging-route wording.

## Boundary

- No official validation metric was computed.
- Official test was not used.
- No paper-level result was promoted.
- `p_rel` / `p_obs` remain disabled.

