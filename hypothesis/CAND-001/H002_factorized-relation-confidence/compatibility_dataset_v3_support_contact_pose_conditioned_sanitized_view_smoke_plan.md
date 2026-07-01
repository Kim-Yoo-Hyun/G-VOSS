# Compatibility Dataset V3 Support/Contact Pose-Conditioned Sanitized View Smoke Plan

## Status

```text
status = h002_compatibility_dataset_v3_support_contact_pose_conditioned_sanitized_view_smoke_plan_ready
artifact_root = artifacts/compatibility_dataset_v3_support_contact_pose_conditioned_sanitized_view_smoke_plan/
input_source = artifacts/compatibility_dataset_v3_support_contact_pose_conditioned_schema_shortcut_audit/smoke_ready_view.jsonl
rows = 400
positive / negative = 200 / 200
paired_groups = 200
validation_errors = 0
learned_smoke_executed = false
next = compatibility_dataset_v3_support_contact_pose_conditioned_sanitized_view_smoke_runner
```

This step does not train or evaluate a learned model. It freezes the allowed model-input source,
feature views, controls, and pass/fail gates for the next train-only learned smoke.

## Input Contract

The only allowed model-input file for the next runner is:

```text
artifacts/compatibility_dataset_v3_support_contact_pose_conditioned_schema_shortcut_audit/smoke_ready_view.jsonl
```

Allowed feature root:

```text
feature_blocks
```

Allowed blocks:

```text
T_e
Z_e_safe
G_e_mesh_pose_contact
Q_e_safe
```

Metadata-only fields:

```text
example_id
cv_group_id
target_y
schema_version
```

Forbidden model features include:

```text
labels
controls_hidden
row_id
anchor_id
scan_id
subject_id
object_id
visible_pair
queue kind
source predicates
hidden pose state
G_e_hash
p_geom_valid
label_source
```

The input manifest records SHA256 checksums for both `smoke_ready_view.jsonl` and
`smoke_ready_model_view_contract.json`.

## Why This Plan Is Needed

The schema audit showed that single allowed features do not solve the target. The next question is
not whether `lying on` or geometry alone is predictive. The question is whether `T_e` changes how
the same `G_e` should be interpreted:

```text
same support/contact G_e + lying on
same support/contact G_e + standing on
```

Under this construction, geometry-only should remain near chance. The primary smoke should succeed
only if the model learns predicate-conditioned pose compatibility.

## Planned Model Views

```text
M0_intercept
M1_source_only_Z_safe
M2_semantic_only_T
M3_semantic_source_TZ_safe
M4_geometry_only_G
M5a_compatibility_TG_concat
M5b_compatibility_TG_pose_interaction
M6_factorized_sanitized_TZGQ_pose_interaction
S1_predicate_label_shortcut
S2_object_pair_shortcut
S3_quality_shortcut
C1_wrong_T_same_G_control
C2_shuffled_G_global_control
C3_shuffled_G_within_predicate_control
```

`M5b_compatibility_TG_pose_interaction` is the primary smoke view. It should include
predicate-conditioned support/contact features such as:

```text
is_lying(predicate) * lying_pose_features
is_standing(predicate) * upright_pose_features
is_lying(predicate) * low_major_axis_upness_or_flatness_features
is_standing(predicate) * high_major_axis_upness_and_vertical_extent_features
predicate-conditioned contact / overlap / gap features
```

`M5a_compatibility_TG_concat` is the no-interaction comparison. If plain concatenation is already
sufficient, the interaction-specific claim is weaker.

## Split And Metrics

Split:

```text
train-only grouped CV by cv_group_id
```

Both rows from the same geometry anchor must stay in the same fold. No validation or test split is
used in this hypothesis-stage smoke.

Metrics:

```text
AUROC
AUPRC
accuracy
balanced_accuracy
Brier
ECE
paired compatible-minus-incompatible score margin
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
M5b should beat M5a by at least 0.10 AUROC or show stronger paired/control behavior
wrong-T same-G control must degrade or invert
shuffled-G controls should approach chance, preferably AUROC <= 0.60
paired compatible-minus-incompatible score margin should be positive
```

## Boundary

```text
paper_evidence_allowed = false
learned_smoke_executed = false
validation_or_test_used = false
h001_artifacts_modified = false
raw_candidate_rows_promoted_as_model_input = false
```

The next step is to implement and run the train-only smoke runner against this frozen contract.
