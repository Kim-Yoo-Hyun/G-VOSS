# Relative-Horizontal Sanitized View Smoke Plan After Schema Audit

## Status

```text
status = h002_compatibility_dataset_v3_relative_horizontal_sanitized_view_smoke_plan_after_schema_audit_ready
validation_errors = 0
learned_smoke_executed = false
next_todo = compatibility_dataset_v3_relative_horizontal_sanitized_view_smoke_runner_after_plan
```

This step freezes the train-only grouped-CV smoke input and comparison contract
for `relative_horizontal`. It does not train a model, use validation/test,
modify H001 artifacts, or promote the result to paper evidence.

## Command

```bash
python hypothesis/CAND-001/H002_factorized-relation-confidence/tools/compatibility_dataset_v3_relative_horizontal_sanitized_view_smoke_plan_after_schema_audit.py
```

## Artifact Root

```text
artifacts/compatibility_dataset_v3_relative_horizontal_sanitized_view_smoke_plan_after_schema_audit/
```

Key outputs:

- `smoke_ready_view.jsonl`
- `smoke_plan.json`
- `model_views.csv`
- `control_plan.csv`
- `gate_plan.csv`
- `feature_paths.csv`
- `input_profile.csv`
- `input_manifest.json`
- `report.md`
- `summary.json`
- `validation_errors.jsonl`

## Input Contract

```text
rows = 2,400
positive / negative = 1,200 / 1,200
cv_groups = 1,200
paired_groups = 1,200
schema = h002_relative_horizontal_runner_ready_view_v1
feature_blocks = G_e_horizontal + T_e
```

Predicate balance:

```text
left = 600
right = 600
front = 600
behind = 600
```

Allowed model input:

```text
T_e.predicate_label
T_e.predicate_text
T_e.relation_family
G_e_horizontal.delta_x_subject_minus_object
G_e_horizontal.delta_y_subject_minus_object
G_e_horizontal.horizontal_distance
```

Forbidden as features:

```text
source score, source predicate, GT provenance, selected-frame compatibility,
axis buckets, scan/object ids, class labels, construction flags, Q_e labels,
in front of alias fields
```

## Planned Models

```text
M0_intercept
M1_semantic_only_T
M2_geometry_only_G_horizontal
M3_TG_concat_no_interaction
M4_TG_horizontal_interaction  # primary
S1_predicate_label_shortcut
S2_geometry_exact_tuple_shortcut
```

## Required Controls

```text
C1_wrong_T_same_G
C2_shuffled_G_global
C3_shuffled_G_within_predicate
C4_axis_sign_flipped_G
C5_wrong_frame_xy_swap
C6_subject_object_swap
no_interaction_concat
```

These controls are required because horizontal relations depend on direction and
reference-frame choice. A high `M4` score is not sufficient unless wrong-T,
shuffled-G, sign-flip, wrong-frame, and endpoint-swap controls degrade or invert.

## Promotion Gates

```text
M1/M2/S1/S2 AUROC <= 0.60
M4 AUROC >= 0.95
M4 gain over single-factor baselines >= 0.30
C1/C2/C3 controls <= 0.60 or invert
C4 sign flip inverts or strongly degrades
C5 wrong-frame degrades unless frame ambiguity is shown
C6 subject-object swap inverts or strongly degrades
paired score margin pass rate >= 0.90
```

## Boundary

- Train-only smoke plan.
- No validation/test source used.
- No learned smoke or training run.
- No source score or `Z_e` used.
- `Q_e` diagnostic rows and `in front of` are excluded from this primary smoke.
- No H001 artifact modified.
- Not paper-level evidence.

