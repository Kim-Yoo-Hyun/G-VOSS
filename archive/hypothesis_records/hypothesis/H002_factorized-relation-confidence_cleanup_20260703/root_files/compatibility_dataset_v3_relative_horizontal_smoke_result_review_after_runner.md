# H002 Relative-Horizontal Smoke Result Review After Runner

Date: 2026-06-29 KST

## Status

```text
artifact_root = artifacts/compatibility_dataset_v3_relative_horizontal_smoke_result_review_after_runner/
status = h002_compatibility_dataset_v3_relative_horizontal_smoke_result_review_after_runner_ready_for_multi_family_synthesis_update
selected_path = promote_relative_horizontal_as_main_compatibility_route_evidence_with_reference_frame_caveat
validation_errors = 0
next_todo = compatibility_dataset_v3_multi_family_claim_synthesis_after_relative_horizontal
```

## Decision

`relative_horizontal`은 H002의 `main compatibility-route mechanism evidence`로
배치한다. 단, 이 family는 `left/right/front/behind`의 의미가 reference-frame
convention에 의존하므로 **frame-aware compatibility route**로만 claim한다.

`in front of`는 현재 train-side source에서 관측되지 않았기 때문에 이번 primary
smoke와 claim boundary에서 제외한다.

## Key Evidence

```text
M1_semantic_only_T AUROC = 0.4558
M2_geometry_only_G_horizontal AUROC = 0.5000
M3_TG_concat_no_interaction AUROC = 0.4558
M4_TG_horizontal_interaction AUROC = 1.0000
```

Controls:

```text
C1_wrong_T_same_G AUROC = 0.0000
C2_shuffled_G_global AUROC = 0.4942
C3_shuffled_G_within_predicate AUROC = 0.5052
C4_axis_sign_flipped_G AUROC = 0.0000
C5_wrong_frame_xy_swap AUROC = 0.2385
C6_subject_object_swap AUROC = 0.0000
```

## Claim Boundary

Allowed:

- `relative_horizontal` is train-only mechanism evidence for
  `C_e = compatibility(T_e, G_e)`.
- Directional horizontal relation compatibility requires predicate-conditioned
  reference-frame geometry.
- Wrong-frame control is part of the claim, not an optional appendix.
- This family can be added to the multi-family relation-aware evidence-routing
  synthesis.

Not allowed:

- calibrated `p_rel` or `p_obs` probability claim
- paper-level performance claim
- geometry-only horizontal reliability claim
- complete horizontal ontology claim including `in front of`
- universal all-relation-family generalization claim

## Next

The next step is to update the multi-family synthesis so that H002's route map
contains:

- `relative_vertical`: clean sign route
- `size_relative`: clean size-comparison route
- `relative_horizontal`: frame-aware directional route
- `support_contact`: challenging compatibility route with caveat
- `proximity`: geometry-easy diagnostic/control route

