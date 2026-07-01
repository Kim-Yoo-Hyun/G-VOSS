# H002 Relative-Horizontal Sanitized View Smoke Runner After Plan

Date: 2026-06-29 KST

## Status

```text
artifact_root = artifacts/compatibility_dataset_v3_relative_horizontal_sanitized_view_smoke_runner_after_plan/
status = h002_compatibility_dataset_v3_relative_horizontal_sanitized_view_smoke_runner_after_plan_passed_controls
validation_errors = 0
learned_smoke_executed = true
paper_evidence_allowed = false
next_todo = compatibility_dataset_v3_relative_horizontal_smoke_result_review_after_runner
```

This stage executes the frozen train-only grouped-CV smoke for the
`relative_horizontal` route. It reads only the runner-ready
`feature_blocks = T_e + G_e_horizontal` view and keeps row IDs, group IDs,
targets, construction metadata, source fields, and hidden frame/proxy fields
outside model input.

## Input

```text
rows = 2,400
positive / negative = 1,200 / 1,200
cv_groups = 1,200
paired_groups = 1,200
predicate_counts = left/right/front/behind each 600
split = train-only grouped CV
```

`in front of` is still absent in the current train-side source and is not part
of this primary smoke.

## Main Metrics

| Model | AUROC | Interpretation |
| --- | ---: | --- |
| `M1_semantic_only_T` | 0.4558 | predicate prior alone does not solve the target |
| `M2_geometry_only_G_horizontal` | 0.5000 | geometry vector alone does not solve same-G predicate flip |
| `M3_TG_concat_no_interaction` | 0.4558 | additive T+G concat does not solve the target |
| `M4_TG_horizontal_interaction` | 1.0000 | predicate-conditioned signed projection solves the target |
| `S1_predicate_label_shortcut` | 0.4558 | predicate label shortcut near chance |
| `S2_geometry_exact_tuple_shortcut` | 0.5000 | exact geometry tuple shortcut near chance under grouped CV |

Primary paired-margin audit:

```text
mean_positive_minus_negative = 0.857145
positive_margin_fraction = 1.000000
```

## Controls

| Control | AUROC | Gate |
| --- | ---: | --- |
| `C1_wrong_T_same_G` | 0.0000 | pass, predicate swap inverts compatibility |
| `C2_shuffled_G_global` | 0.4942 | pass, global geometry shuffle near chance |
| `C3_shuffled_G_within_predicate` | 0.5052 | pass, within-predicate geometry shuffle near chance |
| `C4_axis_sign_flipped_G` | 0.0000 | pass, selected-axis sign flip inverts compatibility |
| `C5_wrong_frame_xy_swap` | 0.2385 | pass, wrong-frame axis swap strongly degrades |
| `C6_subject_object_swap` | 0.0000 | pass, endpoint swap inverts compatibility |

## Interpretation

The result supports `relative_horizontal` as a clean train-only
predicate-geometry compatibility route under the frozen reference-frame
protocol:

- `T_e` alone is insufficient.
- `G_e_horizontal` alone is insufficient because the same geometry is paired
  with opposite predicates.
- Plain additive `T_e + G_e` is insufficient.
- Explicit predicate-conditioned interaction is necessary in this constructed
  smoke.
- Wrong predicate, shuffled geometry, wrong frame, sign flip, and endpoint swap
  controls collapse or invert the score.

This is not paper evidence yet. It is a hypothesis-stage mechanism diagnostic.
The next step is a result review that decides how to position
`relative_horizontal`: main compatibility-route evidence, reference-frame
diagnostic evidence, or control/future route.

