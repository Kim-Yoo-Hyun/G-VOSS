# Compatibility Dataset V2 Schema Shortcut Audit

Artifact root:

```text
artifacts/compatibility_dataset_v2_schema_shortcut_audit/
```

Status:

```text
status = h002_compatibility_dataset_v2_schema_shortcut_audit_requires_sanitized_view
rows = 400
compatibility positive / negative = 200 / 200
schema_errors = 0
leakage_high_risk_probes = 7
full_factorized_view_allowed = false
sanitized_view_written = true
learned_smoke_allowed = false
next_todo = compatibility_dataset_v2_sanitized_view_smoke_plan
```

## What Was Checked

The audit checked whether the v2 candidate rows can be used for learned compatibility smoke
without leaking target construction fields.

Inputs:

```text
artifacts/compatibility_dataset_v2_candidate_materialization/compatibility_rows.jsonl
artifacts/compatibility_dataset_v2_candidate_materialization/baseline_view.jsonl
artifacts/compatibility_dataset_v2_candidate_materialization/audit_view.jsonl
artifacts/compatibility_dataset_v2_candidate_materialization/schema.json
```

Outputs:

```text
summary.json
schema_audit.json
shortcut_probe.csv
shortcut_probe_details.json
sanitized_model_view.jsonl
blocked_fields.json
validation_errors.jsonl
report.md
```

## Result

The dataset is balanced at the intended visible axes:

```text
support_contact positive / negative = 120 / 120
relative_vertical positive / negative = 80 / 80
predicate-level counts = balanced
predicate-only accuracy = 0.500
family-only accuracy = 0.500
source-rank-band accuracy = 0.500
source-score-bin accuracy = 0.500
```

However, the raw unsanitized views contain perfect construction shortcuts:

```text
row_role accuracy = 1.000
counterfactual_type accuracy = 1.000
G_e.geometry_source accuracy = 1.000
Q_e.generated_counterfactual accuracy = 1.000
Q_e.evidence_conflict_flag accuracy = 1.000
geometry_status_baseline accuracy = 1.000
relation_source accuracy = 1.000
```

These fields expose whether a row is an anchor positive or generated counterfactual negative.
They are not semantic-geometry compatibility evidence.

## Decision

Do not run learned smoke on:

```text
raw compatibility_rows.jsonl model_views.full_factorized
raw compatibility_rows.jsonl model_views.obs_head
baseline_view.jsonl
audit_view.jsonl
```

Use only the sanitized model view for the next smoke plan:

```text
artifacts/compatibility_dataset_v2_schema_shortcut_audit/sanitized_model_view.jsonl
```

The sanitized view keeps:

```text
T_e
Z_e
numeric G_e
Q_e_sanitized
```

and removes:

```text
row_role
counterfactual_type
G_e.geometry_source
Q_e.generated_counterfactual
Q_e.evidence_conflict_flag
geometry_status_baseline
relation_source
hidden_control fields
```

## Interpretation

This is not a failure of the compatibility-learning direction. It shows that generated
counterfactual datasets need a strict input contract. The semantic and source axes are balanced,
and numeric geometry features do not individually solve the target with high accuracy. The blocker
is the unsanitized construction metadata.

The next step should define the smoke plan over `sanitized_model_view.jsonl`, including explicit
controls for:

- source-only `Z_e`;
- semantic-only `T_e`;
- numeric geometry-only `G_e`;
- compatibility `T_e + G_e`;
- sanitized factorized `T_e + Z_e + G_e + Q_e_sanitized`;
- shuffled or wrong-pair geometry controls using only numeric geometry fields;
- grouped split by counterfactual group without exposing group construction metadata.

## Next

```text
compatibility_dataset_v2_sanitized_view_smoke_plan
```
