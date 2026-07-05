# H002 Independent Validity Stratum Repair Schema Shortcut Audit

## Status

```text
status = h002_compatibility_dataset_v3_independent_validity_stratum_repair_schema_shortcut_audit_ready_for_sanitized_view_smoke_plan
validation_errors = 0
next_todo = compatibility_dataset_v3_independent_validity_stratum_repair_sanitized_view_smoke_plan
```

## Purpose

이 단계는 repaired independent-validity target이 learned smoke로 넘어갈 수 있을 만큼
schema-safe하고 shortcut-safe한지 확인한다.

이전 independent-validity artifact의 가장 큰 blocker는 다음 probe였다.

```text
predicate_x_class_pair accuracy = 0.976562
subject_object_class_pair accuracy = 0.840000
```

이번 audit은 exact predicate/object-class balancing 이후 같은 계열의 shortcut이
사라졌는지 확인한다.

## Counts

```text
model_safe_rows = 1600
candidate_rows = 1600
hidden_manifest_rows = 1600
label_counts = 800 / 800
retained_exact_strata = 35
```

Family counts:

| Family | Rows | Interpretation |
| --- | ---: | --- |
| `relative_vertical` | 1512 | primary exact-stratum repair slice |
| `support_contact_pose_conditioned` | 88 | diagnostic slice |

Predicate counts:

| Predicate | Rows |
| --- | ---: |
| `higher than` | 760 |
| `lower than` | 752 |
| `lying on` | 64 |
| `standing on` | 24 |

## Shortcut Result

```text
critical_high_or_medium = 0
source_confidence_high_or_medium = 0
raw_geometry_high_or_medium = 0
sanitized_blocked_feature_path_hits = 0
model_feature_blocked_key_hits = 0
validation_errors = 0
```

Important probe results:

| Probe | Accuracy | Risk |
| --- | ---: | --- |
| `predicate_x_class_pair` | 0.500000 | low |
| `subject_object_class_pair` | 0.500000 | low |
| `predicate_label` | 0.500000 | low |
| `rank_band` | 0.553750 | low |
| `semantic_rank` | 0.549375 | low |
| `semantic_score_norm` | 0.525625 | low |

This directly addresses the previous blocker: exact predicate/object-class balancing removes the
semantic-stratum shortcut from the model-safe target.

## Hidden Construction Fields

Hidden construction fields remain predictive, as expected:

```text
blocked_hidden_high_risk = 6
```

Examples include `hidden_geometry_status`, `hidden_label_match_status`, `hidden_target_pool`,
`hidden_target_role`, and `target_label_self`. This is not a schema leak because these fields are
not present in `model_safe_view` feature blocks.

## Artifacts

```text
artifacts/compatibility_dataset_v3_independent_validity_stratum_repair_schema_shortcut_audit/
```

Key outputs:

- `sanitized_primary_view.jsonl`
- `shortcut_probes.csv`
- `shortcut_probe_details.jsonl`
- `distribution_audit.csv`
- `feature_path_audit.csv`
- `blocked_field_audit.csv`
- `smoke_ready_model_view_contract.json`
- `summary.json`
- `validation_errors.jsonl`
- `report.md`

## Interpretation

The repaired target is now safe enough to plan learned smoke. This does not mean the H002 method is
validated yet. It means the previous target-construction shortcut has been controlled well enough to
run the next comparison.

The next smoke should compare at least:

- `T_e` semantic-only
- `Z_e` source-confidence-only
- `G_e_raw` geometry-only
- `T_e + G_e_raw` compatibility-style inputs
- full factorized view
- wrong/shuffled geometry controls if feasible

## Boundary

- Train-only schema/shortcut audit.
- No validation/test usage.
- No learned smoke or model training.
- No H001 artifact modification.
- Not paper evidence.

## Next

```text
compatibility_dataset_v3_independent_validity_stratum_repair_sanitized_view_smoke_plan
```
