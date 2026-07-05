# H002 Independent Validity Schema Shortcut Audit

## Status

```text
status = h002_compatibility_dataset_v3_independent_validity_schema_shortcut_audit_blocked_shortcut_risk
validation_errors = 1
next_todo = compatibility_dataset_v3_independent_validity_path_decision_after_schema_shortcut_audit
```

`validation_errors = 1`은 input/schema 오류가 아니라 allowed feature shortcut risk를
명시적으로 blocking error로 기록한 것이다.

## Artifact

```text
artifact_root = artifacts/compatibility_dataset_v3_independent_validity_schema_shortcut_audit/
sanitized_primary_view = sanitized_primary_view.jsonl
shortcut_probes = shortcut_probes.csv
shortcut_probe_details = shortcut_probe_details.jsonl
distribution_audit = distribution_audit.csv
summary = summary.json
```

## Counts

```text
candidate_rows = 4027
primary_binary_rows = 3200
sanitized_primary_rows = 3200
primary_positive / primary_negative = 1600 / 1600
relative_vertical = 1600
support_contact_pose_conditioned = 1600
```

## Result

The schema cleanup itself works:

```text
sanitized_blocked_feature_path_hits = 0
sanitized_blocked_field_leakage_hits = 0
```

However, shortcut risk remains:

```text
allowed_feature_high_or_medium_risk = 2
allowed_feature_high_risk = 1
allowed_feature_medium_risk = 1
```

Blocking allowed probes:

| Probe | Accuracy | Risk |
| --- | ---: | --- |
| `predicate_x_class_pair` | 0.976562 | high |
| `subject_object_class_pair` | 0.840000 | medium |

Construction-derived geometry summaries were also confirmed as blocked fields:

| Probe | Accuracy | Risk |
| --- | ---: | --- |
| `blocked_G_e_summary.geometry_status` | 1.000000 | high |
| `blocked_G_e_summary.consistency_score` | 1.000000 | high |
| `blocked_G_e_summary.geometry_residual_proxy` | 1.000000 | high |
| `blocked_G_e_summary.geometry_axis` | 1.000000 | high |
| `blocked_G_e_summary.p_geom_valid` | 0.750625 | medium |

These fields are removed from `sanitized_primary_view.jsonl`; they should not be used as learned
model input for this target.

## Interpretation

The independent validity target fixed the previous class-mass issue, but it did not yet fix target
identifiability. The primary label is still highly predictable from semantic object-pair and
predicate-object-pair strata. This means a learned smoke result could improve by memorizing which
object pairs tend to appear in positive or negative pools, rather than learning `C_e =
compatibility(T_e, G_e)`.

Therefore the next step should be a path decision, not learned smoke.

## Next

```text
compatibility_dataset_v3_independent_validity_path_decision_after_schema_shortcut_audit
```
