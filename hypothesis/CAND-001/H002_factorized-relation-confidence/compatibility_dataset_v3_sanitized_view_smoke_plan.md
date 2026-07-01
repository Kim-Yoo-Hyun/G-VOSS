# Compatibility Dataset V3 Sanitized View Smoke Plan

Date: 2026-06-26 KST

## Status

```text
status = h002_compatibility_dataset_v3_sanitized_view_smoke_plan_ready
artifact_root = artifacts/compatibility_dataset_v3_sanitized_view_smoke_plan/
input_source = artifacts/compatibility_dataset_v3_schema_shortcut_audit/smoke_ready_view.jsonl
rows = 400
positive / negative = 200 / 200
paired_groups = 200
validation_errors = 0
learned_smoke_executed = false
next = compatibility_dataset_v3_sanitized_view_smoke_runner
```

This step does not train or evaluate a learned model. It freezes the allowed model-input source,
feature views, controls, and pass/fail gates for the next v3 train-only learned smoke.

## Input Contract

The only allowed input file for the next runner is:

```text
artifacts/compatibility_dataset_v3_schema_shortcut_audit/smoke_ready_view.jsonl
```

The runner must not read raw candidate rows or intermediate materialization views as model input.

```text
candidate_rows.jsonl = audit/provenance only
sanitized_model_view.jsonl = intermediate view only
smoke_ready_view.jsonl = model input
```

Allowed feature root:

```text
feature_blocks
```

Allowed blocks:

```text
T_e
Z_e_safe
G_e_numeric
Q_e_safe
```

Metadata-only fields:

```text
example_id
cv_group_id
target_y
target_name
schema_version
```

Forbidden model features include identifiers, construction metadata, hidden labels, and geometry
hashes:

```text
geometry_feature_hash
labels
controls_hidden
row_id
geometry_group_id
raw_source_predicate
source_prediction_id
positive_predicate
direction_bucket
visible_pair
endpoint_state
```

The input manifest records the SHA256 for both `smoke_ready_view.jsonl` and
`smoke_ready_model_view_contract.json`.

## Why This Plan Is Needed

The v2 target failed because the learned smoke could solve much of the target as a generic geometry
perturbation problem. Geometry-only outperformed compatibility, and wrong-predicate same-geometry
controls did not degrade.

The v3 target was therefore redesigned so that the same `G_e` is paired with two predicate
alternatives:

```text
same directed object pair + same G_e + higher than = one label
same directed object pair + same G_e + lower than = opposite label
```

Under this construction, `G_e` alone should be near chance. The important smoke question is whether
`T_e` changes the interpretation of the same geometry evidence.

## Planned Model Views

```text
M0_intercept
M1_source_only_Z_safe
M2_semantic_only_T
M3_semantic_source_TZ_safe
M4_geometry_only_G
M5a_compatibility_TG_concat
M5b_compatibility_TG_interaction
M6_factorized_sanitized_TZGQ_interaction
S1_predicate_label_shortcut
S2_object_pair_shortcut
S3_source_score_rank_shortcut
C1_wrong_T_same_G_control
C2_shuffled_G_global_control
C3_shuffled_G_within_predicate_control
```

`M5b_compatibility_TG_interaction` is the primary smoke view. It should use predicate-conditioned
vertical interaction features such as:

```text
expected_z_sign(predicate) * center_delta_z_m
expected_z_sign(predicate) * normalized_center_delta_z
```

`M5a_compatibility_TG_concat` is kept as a no-interaction comparison. If plain concatenation is
sufficient, the method claim is weaker. If interaction passes while plain concatenation and
shortcut baselines remain weak, the evidence supports predicate-geometry compatibility rather than
generic feature aggregation.

## Split And Metrics

Split:

```text
train-only grouped CV by cv_group_id
```

Both rows from the same geometry group must stay in the same fold. No validation or test split is
used in this hypothesis-stage smoke.

Metrics:

```text
AUROC
AUPRC
accuracy
balanced_accuracy
Brier
ECE
paired compatible-minus-incompatible score difference
fold mean/std
```

## Promotion Gates

Runner-blocking gates:

```text
rows = 400
positive / negative = 200 / 200
groups = 200
each cv_group_id has one positive and one negative row
runner reads only smoke_ready_view.jsonl feature_blocks
metadata fields are never features
```

Promotion gates after learned smoke:

```text
M1/M2/M3/M4/S1/S2/S3 AUROC <= 0.60
M5b AUROC >= 0.90
M5b AUROC >= best(M1, M2, M3, M4) + 0.30
wrong-T same-G control must degrade or invert
shuffled-G controls should approach chance, preferably AUROC <= 0.60
paired compatible-minus-incompatible score should be positive
```

Failure of these gates does not prove the research idea is false. It means the current v3 row
construction or feature encoding is still not a clean compatibility target.

## Artifacts

```text
artifacts/compatibility_dataset_v3_sanitized_view_smoke_plan/summary.json
artifacts/compatibility_dataset_v3_sanitized_view_smoke_plan/input_manifest.json
artifacts/compatibility_dataset_v3_sanitized_view_smoke_plan/smoke_plan.json
artifacts/compatibility_dataset_v3_sanitized_view_smoke_plan/model_views.csv
artifacts/compatibility_dataset_v3_sanitized_view_smoke_plan/gates.csv
artifacts/compatibility_dataset_v3_sanitized_view_smoke_plan/controls.csv
artifacts/compatibility_dataset_v3_sanitized_view_smoke_plan/input_profile.csv
artifacts/compatibility_dataset_v3_sanitized_view_smoke_plan/report.md
artifacts/compatibility_dataset_v3_sanitized_view_smoke_plan/validation_errors.jsonl
```

## Boundary

```text
paper_evidence_allowed = false
learned_smoke_executed = false
validation_or_test_used = false
h001_artifacts_modified = false
raw_candidate_rows_promoted_as_model_input = false
```

The next step is to implement the train-only smoke runner against this frozen contract.
