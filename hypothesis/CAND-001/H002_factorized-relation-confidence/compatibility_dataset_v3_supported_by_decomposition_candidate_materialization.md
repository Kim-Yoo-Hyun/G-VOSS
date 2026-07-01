# H002 R6 Supported-By Decomposition Candidate Materialization

## Status

```text
artifact_root = artifacts/route_specific_targets/r6_superordinate_support/
status = h002_compatibility_dataset_v3_supported_by_decomposition_candidate_materialization_ready_for_schema_shortcut_audit
selected_path = materialized_preferred_320row_target
validation_errors = 0
next_todo = compatibility_dataset_v3_supported_by_decomposition_schema_shortcut_audit
```

## Materialized Rows

R6 `supported by`를 four-way decomposition target으로 materialize했다.

```text
total_rows = 320
accept_broad_support = 80
relabel_to_subtype = 80
reject_no_support = 80
abstain = 80
```

Selection quality:

```text
unique_scans = 257
unique_class_pairs = 173
mixed_class_pair_cells = 80
max_rows_per_scan = 5 / 12
max_rows_per_directed_pair = 1 / 1
max_rows_per_subject_object_class_pair = 4 / 16
hard_surface_share = 0.278125 / 0.55
generic_endpoint_abstain_share = 0.175 / 0.50
finite_G_e_rows = 320 / 320
blocked_fields_in_model_safe = 0
```

Subtype relabel split:

```text
standing on = 42
lying on = 38
none = 240
```

## Outputs

```text
model_safe_rows = artifacts/route_specific_targets/r6_superordinate_support/model_safe_rows.jsonl
hidden_manifest = artifacts/route_specific_targets/r6_superordinate_support/hidden_manifest.jsonl
audit_view = artifacts/route_specific_targets/r6_superordinate_support/audit_view.jsonl
schema = artifacts/route_specific_targets/r6_superordinate_support/schema.json
quota_audit = artifacts/route_specific_targets/r6_superordinate_support/quota_audit.csv
cell_balance_audit = artifacts/route_specific_targets/r6_superordinate_support/cell_balance_audit.csv
control_manifest = artifacts/route_specific_targets/r6_superordinate_support/control_manifest.json
schema_precheck = artifacts/route_specific_targets/r6_superordinate_support/schema_precheck.csv
summary = artifacts/route_specific_targets/r6_superordinate_support/summary.json
report = artifacts/route_specific_targets/r6_superordinate_support/report.md
```

## Interpretation

- R6 preferred 320-row target was achieved; no fallback was needed.
- `supported by` remains superordinate decomposition, not binary compatibility.
- Same-class-pair mixed labels are strong enough for the next shortcut audit.
- Hard-surface and generic-abstain shortcuts are controlled at materialization time.
- Learned smoke remains blocked until schema/shortcut audit passes.

## Boundary

- Train-only candidate materialization.
- No learned smoke/model training.
- No validation/test usage.
- H001 artifacts were not modified.
- No paper-level evidence is claimed.

## Next

```text
compatibility_dataset_v3_supported_by_decomposition_schema_shortcut_audit
```
