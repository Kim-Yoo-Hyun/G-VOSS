# H002 Support/Contact Individual Predicate Point/Multiview Smoke Plan

Date: 2026-06-29 KST

## Purpose

이 단계는 point/contact/observability branch의 learned smoke를 바로 실행하지 않고,
어떤 model view, control, gate로 검증할지 먼저 고정한다. 입력은 직전
schema/shortcut audit에서 통과한 `640`개 train-only main rows이며, `supported by`
diagnostic rows는 smoke target에서 제외했다.

## Status

```text
artifact_root = artifacts/compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_smoke_plan/
status = h002_compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_smoke_plan_ready
rows = 640
positive / negative = 320 / 320
predicate_counts = lying on 320 / standing on 320
cv_groups = 258
mixed_label_cv_groups = 155
validation_errors = 0
learned_smoke_executed = false
next_todo = compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_smoke_runner
```

## Planned Model Views

```text
M0_intercept
M1_semantic_only_T
M2_obb_geometry_only
M3_point_pose_only
M4_contact_patch_only
M5_point_contact_geometry
M6_TG_obb_concat
M7_TG_point_contact_concat
M8_TG_point_contact_interaction
M9_TGQ_factorized_observability
```

Primary model:

```text
M8_TG_point_contact_interaction
```

This is the main compatibility smoke. It tests whether predicate semantics can
condition how point/contact geometry evidence is interpreted for `standing on`
versus `lying on`.

## Required Controls

```text
S1_predicate_label_shortcut
S2_class_pair_shortcut
S3_quality_only_shortcut
C1_wrong_T_same_G
C2_shuffled_G_global
C3_shuffled_G_within_predicate
C4_shuffled_Q
```

Additional comparison:

```text
M6_TG_obb_concat vs M8_TG_point_contact_interaction
```

This tests whether the new point/contact `G_e` expansion actually improves over
the previous OBB-only support/contact representation.

## Gates

The runner result can only be interpreted positively if:

- data integrity remains `640` rows with `320/320` labels;
- semantic and quality shortcut baselines stay below `0.70` AUROC;
- primary `M8` reaches at least `0.70` AUROC;
- `M8` beats the best single-factor baseline by at least `0.05` AUROC;
- `M8` beats old OBB `T+G` by at least `0.03` AUROC;
- shuffled geometry and wrong-T controls degrade;
- if geometry-only `M5` is within `0.02` AUROC of `M8`, the result is geometry-dominance diagnostic, not a compatibility claim.

## Boundary

- No validation/test row is used.
- No learned smoke is executed in this step.
- No paper-level evidence is produced.
- No visual crop/image feature is used as model input.
- `Z_e`, source score/rank, H001 `p_geom_valid`, scan/object ids, visual paths, and hidden construction fields remain outside model input.

## Output Files

- `smoke_ready_view.jsonl`: normalized 640-row runner input.
- `model_views.csv`: model/baseline/control list.
- `control_plan.csv`: control definitions.
- `gate_plan.csv`: pass/fail interpretation gates.
- `input_profile.csv`: selected feature availability profile.
- `feature_paths.csv`: allowed feature path manifest.
- `smoke_plan.json`: machine-readable plan.
- `validation_errors.jsonl`: empty.
