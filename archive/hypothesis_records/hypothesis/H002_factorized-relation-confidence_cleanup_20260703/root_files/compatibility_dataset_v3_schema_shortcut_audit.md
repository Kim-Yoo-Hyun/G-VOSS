# Compatibility Dataset V3 Schema Shortcut Audit

Artifact root:

```text
artifacts/compatibility_dataset_v3_schema_shortcut_audit/
```

Status:

```text
status = h002_compatibility_dataset_v3_schema_shortcut_audit_ready_for_sanitized_view_smoke_plan
candidate_rows = 400
smoke_ready_rows = 400
allowed_feature_high_or_medium_risk = 0
blocked_raw_high_risk_probes = 2
validation_errors = 0
next_todo = compatibility_dataset_v3_sanitized_view_smoke_plan
```

## Decision

`candidate_rows.jsonl` is the full audit artifact, not the model input. It intentionally contains:

- labels;
- hidden controls;
- source prediction provenance;
- group/integrity identifiers.

The audit produced a stricter model-input artifact:

```text
smoke_ready_view.jsonl
```

This file keeps only:

```text
T_e
Z_e_safe
G_e_numeric
Q_e_safe
target_y
cv_group_id
```

`target_y` and `cv_group_id` are target/CV metadata, not model features. The model feature root is
only:

```text
feature_blocks
```

## Important Fix

The previous materialization-level `sanitized_model_view.jsonl` still contained:

```text
G_e_numeric.geometry_feature_hash
```

This is useful for group integrity, but it must not be a model feature. The schema audit removed it
from `smoke_ready_view.jsonl`.

Therefore:

```text
candidate_rows.jsonl = audit/provenance artifact
sanitized_model_view.jsonl = intermediate view, not final smoke input
smoke_ready_view.jsonl = only allowed input source for next smoke plan
```

## Shortcut Probes

Allowed feature probes are all low risk:

```text
predicate_label = 0.500
subject_label = 0.500
object_label = 0.500
subject_object_text = 0.500
source_rank_band = 0.5375
source_score_normalized = 0.5175
source_rank = 0.5375
all single G_e numeric threshold probes = 0.500
```

Blocked raw high-risk probes:

```text
raw_row_id = 1.000
hidden_source_prediction_id = 1.000
```

These are expected identifier shortcuts and remain blocked from model features.

## Group Integrity

The audit verified:

```text
groups = 200
rows per group = 2
predicates per group = higher than + lower than
labels per group = one positive + one negative
geometry hashes per group = 1
```

## Outputs

```text
smoke_ready_view.jsonl
smoke_ready_model_view_contract.json
shortcut_probes.csv
shortcut_probe_details.jsonl
blocked_field_audit.csv
feature_path_audit.csv
group_integrity_audit.csv
summary.json
validation_errors.jsonl
report.md
```

## Boundary

This step:

- is train-only;
- performs schema/shortcut audit only;
- does not run learned smoke;
- does not use validation/test data;
- does not create paper-level evidence;
- does not modify H001 artifacts.

## Next

```text
compatibility_dataset_v3_sanitized_view_smoke_plan
```
