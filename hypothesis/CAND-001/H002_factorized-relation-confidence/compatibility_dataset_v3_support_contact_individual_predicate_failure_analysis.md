# H002 Support/Contact Individual Predicate Failure Analysis

## Status

```text
artifact_root = artifacts/compatibility_dataset_v3_support_contact_individual_predicate_failure_analysis/
status = h002_compatibility_dataset_v3_support_contact_individual_predicate_failure_analysis_ready_select_point_multiview_evidence_plan
selected_path = freeze_obb_only_diagnostic_select_point_multiview_evidence_plan
rows = 640
errors = 267
false_positive / false_negative = 144 / 123
high_confidence_errors = 12
validation_errors = 0
next_todo = compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_evidence_plan
```

## Main Finding

The current support/contact individual-predicate branch is not blocked by semantic
shortcut or geometry-only dominance. It has real predicate-geometry interaction signal,
but semseg OBB-only geometry is not strong enough to separate `standing on` from
`lying on` as a main result.

```text
primary M4 AUROC = 0.6316
geometry-only M2 AUROC = 0.5092
semantic-only M1 AUROC = 0.4108
plain concat M3 AUROC = 0.4538
wrong-T AUROC = 0.3589
shuffled-G global AUROC = 0.5223
```

## Failure Shape

The false positives and false negatives are both substantial:

```text
false_positive = 144
false_negative = 123
```

The construction axis reveals the current target structure:

```text
label_match_status = family_match: rows 320, error_rate 0.4500
label_match_status = exact_match:  rows 320, error_rate 0.3844
```

This means many negatives are not physically impossible support/contact cases. They are
fine-grained predicate mismatch cases, such as a candidate `standing on` when GT contains
`lying on`, or vice versa. That is a harder compatibility problem than generic support
validity.

## Class-Pair Concentration

Worst slices:

```text
shoes->floor: error_rate 0.6250
item->floor:  error_rate 0.5111
picture->floor: error_rate 0.5000
box->table: error_rate 0.4727
```

Better slices:

```text
backpack->floor: error_rate 0.1375
bag->chair: error_rate 0.2143
box->box: error_rate 0.3636
```

This suggests the model can use pose/contact evidence for some object categories, but
the current OBB features are unreliable for thin, small, ambiguous, or generic object
classes such as `shoes`, `item`, and `picture`.

## Geometry Diagnosis

The strongest geometry features for explaining errors are still weak:

```text
subject_major_axis_upness error AUC = 0.5705
normal_alignment error AUC = 0.5666
subject_vertical_extent_ratio error AUC = 0.5472
subject_minor_axis_upness error AUC = 0.5429
obb_contact_likelihood_proxy error AUC = 0.5375
```

The label-oriented AUCs are also near chance. This confirms that OBB-level pose/contact
features alone do not carry enough information for the standing-vs-lying decision.

## Observability Problem

All rows share the same evidence profile:

```text
mesh=True|point=False|view=False: 640
```

So `Q_e` cannot actually model observability or evidence quality in this branch. This
explains why `M5_TGQ_factorized_observability` is identical to `M4`.

## Decision

Selected path:

```text
freeze_obb_only_diagnostic_select_point_multiview_evidence_plan
```

Meaning:

- keep current semseg OBB-only result as diagnostic;
- do not lower the predeclared `0.70` gate;
- do not switch to a stronger combiner first;
- next, plan point/multiview evidence for this support/contact branch;
- label tightening should be considered together with visual/mesh packet review.

## Next

```text
compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_evidence_plan
```
