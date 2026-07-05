# Compatibility Dataset V2 Failure Analysis

Artifact root:

```text
artifacts/compatibility_dataset_v2_failure_analysis/
```

Status:

```text
status = h002_compatibility_dataset_v2_failure_analysis_ready
rows = 400
compatibility positive / negative = 200 / 200
validation_errors = 0
primary_cause = target_is_geometry_perturbation_detection_not_predicate_conditioned_compatibility
next_todo = compatibility_dataset_v2_target_redesign_plan
```

## Main Diagnosis

The sanitized v2 smoke failed for a principled reason. After construction shortcuts were removed,
the remaining target is still mostly generic geometry perturbation detection. It is not yet a
predicate-conditioned compatibility task.

Key evidence:

```text
geometry-only M4 AUROC = 0.6731
compatibility M5 AUROC = 0.6250
wrong-T same-G AUROC = 0.6250
mean |M5 - wrongT| = 0.0
```

This means changing the predicate does not change the compatibility model prediction. `T_e` is not
controlling which geometry evidence matters.

## What Was Not The Problem

The failure is not mainly source/semantic shortcut leakage:

```text
source-only Z_e_safe = 0.5000
semantic-only T_e = 0.4846
semantic + source = 0.4797
object-pair shortcut = 0.4885
```

These probes are near chance. The input sanitization worked.

## What Is The Problem

The useful signal comes from generic numeric geometry:

| Family | Feature | Positive Mean | Negative Mean | Effect |
| --- | --- | ---: | ---: | ---: |
| `support_contact` | `normalized_distance_xy` | 0.4850 | 1.1687 | -1.0809 |
| `support_contact` | `vertical_gap_subject_on_object` | -1.4428 | -0.2682 | -0.7548 |
| `support_contact` | `distance_xy` | 0.9066 | 1.4835 | -0.6880 |
| `support_contact` | `projected_overlap_max` | 0.4741 | 0.2757 | 0.4865 |
| `support_contact` | `projected_iou_xy` | 0.0773 | 0.0321 | 0.4615 |

These are useful geometry features, but the target can use them without reading predicate
semantics. That is why `G_e` alone beats `T_e + G_e`.

## Counterfactual-Type Diagnosis

Support/contact negative false positive rates under `M5`:

```text
shuffled_geometry = 0.800
wrong_pair_geometry = 0.425
contact_gap_or_overlap_perturbation = 0.025
```

Relative-vertical negative false positive rates:

```text
predicate_flip = 0.650
subject_object_swap = 0.375
```

Interpretation:

- `contact_gap_or_overlap_perturbation` is too easy and is solved by generic geometry.
- `shuffled_geometry` often remains geometrically support-like, so the model treats it as positive.
- `predicate_flip` and `subject_object_swap` do not create a clean predicate-conditioned vertical
  target under the current rows.
- The current negative types are not consistently “same geometry, different predicate validity”
  contrasts.

## Family-Level Diagnosis

Relative vertical:

```text
M4 geometry-only = 0.5000
M5 compatibility = 0.4788
wrong-T same-G = 0.4788
```

Support/contact:

```text
M4 geometry-only = 0.7492
M5 compatibility = 0.7043
wrong-T same-G = 0.7043
```

So support/contact carries the learnable geometry signal, while relative vertical is weak. Neither
family currently shows predicate conditioning.

## Required Redesign

The next dataset should not just create more generated negatives. It must create contrasts where
predicate semantics are necessary.

Required target properties:

1. Same object-pair geometry should be evaluated under multiple predicates.
2. At least one predicate should be valid and another invalid for the same or near-identical
   geometry.
3. Geometry-only `G_e` should not be sufficient to solve the target.
4. Wrong-predicate control must degrade.
5. Shuffled-geometry control must degrade.

Candidate redesign directions:

- `same_geometry_multi_predicate`: same pair geometry with `standing on`, `lying on`, `supported by`
  alternatives where only one support predicate is plausible.
- `directional_vertical_pair`: same pair with `higher than` and `lower than`, requiring subject/object
  order rather than generic vertical spread.
- `hard_support_contact`: near/contact geometry that is close but violates support direction or
  object role.
- keep `contact_gap_or_overlap_perturbation` as a sanity control, not a primary negative.
- keep geometry-only as a main baseline, not just a control.

## Boundary

This analysis:

- is train-only;
- uses hidden construction provenance for diagnosis only;
- does not use hidden fields as model input;
- does not run a new learned smoke;
- does not use validation/test data;
- does not modify H001 artifacts;
- is not paper-level evidence.

## Next

```text
compatibility_dataset_v2_target_redesign_plan
```
