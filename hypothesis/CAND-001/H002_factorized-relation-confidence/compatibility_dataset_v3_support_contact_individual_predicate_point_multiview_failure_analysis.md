# H002 Support/Contact Point/Multiview Failure Analysis

## Status

```text
artifact_root = artifacts/compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_failure_analysis/
status = h002_compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_failure_analysis_ready_for_result_review
selected_path = keep_internal_near_threshold_diagnostic_use_as_paper_compatibility_route_evidence
rows = 640
errors = 227
false_positive / false_negative = 108 / 119
validation_errors = 0
next_todo = compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_result_review_and_claim_position
```

## Main Finding

The internal H002 gate should remain conservative:

```text
M8_TG_point_contact_interaction = 0.699375
internal gate = 0.70
internal status = near-threshold diagnostic
```

However, this should not be interpreted as a paper-facing failure. The paper-facing
role is:

```text
support/contact = main compatibility-route evidence with caveat
support/contact != fully solved relation family
```

The reason is the baseline/control pattern:

```text
semantic-only T = 0.442480
point/contact geometry-only = 0.470249
plain point/contact T+G concat = 0.434658
predicate-geometry interaction M8 = 0.699375
wrong-T same-G = 0.273125
shuffled-G = 0.506240 / 0.463857
```

This supports the claim that support/contact needs predicate-geometry compatibility,
not fixed semantic-geometry fusion.

## Predicate Slices

| Predicate | Rows | AUROC | Error Rate | FP | FN |
| --- | ---: | ---: | ---: | ---: | ---: |
| `lying on` | 320 | 0.692578 | 0.362500 | 54 | 62 |
| `standing on` | 320 | 0.707930 | 0.346875 | 54 | 57 |

The aggregate miss is mostly a near-threshold issue, not a collapse. `standing on`
passes the heuristic gate; `lying on` is the weaker slice.

## Q_e Slices

| Q_e state | Rows | AUROC | Error Rate | FP | FN |
| --- | ---: | ---: | ---: | ---: | ---: |
| `sufficient` | 280 | 0.772590 | 0.310714 | 40 | 47 |
| `limited` | 352 | 0.638494 | 0.389205 | 66 | 71 |
| `uncertain` | 8 | 0.600000 | 0.375000 | 2 | 1 |

This is important. `Q_e` should not be used as relation truth, because `M9` does not
improve over `M8` and shuffled-Q is almost identical. But `Q_e` is meaningful as an
observability/selective-decision axis: sufficient evidence rows are much cleaner than
limited evidence rows.

## Failure Concentration

The hardest class-pair slices are:

```text
item->floor: error_rate 0.477778
shoes->floor: error_rate 0.437500
picture->floor: error_rate 0.428571
object->floor: error_rate 0.413333
```

Cleaner slices include:

```text
box->floor: error_rate 0.318519
box->table: error_rate 0.254545
bag->chair: error_rate 0.214286
box->box: error_rate 0.212121
```

This suggests the remaining issue is not simply relation family failure. It is tied to
object category and observability: generic/small/thin floor objects are much harder to
separate into `standing on` vs `lying on`.

## Feature Diagnosis

Top error-correlated features are weak-to-moderate:

```text
contact.point_center_distance_xy error AUC = 0.575557
point.object_box_volume_proxy error AUC = 0.572890
obb.center_distance_xy error AUC = 0.567055
contact.point_xy_overlap_object_ratio error AUC = 0.564869
contact.point_support_contact_likelihood_proxy error AUC = 0.563695
```

No single numeric feature explains the failures. This supports the current route:
support/contact should be presented as a compatibility-route case, not a simple
geometry-rule case.

## Decision

Selected interpretation:

```text
keep_internal_near_threshold_diagnostic_use_as_paper_compatibility_route_evidence
```

Meaning:

- keep internal status as near-threshold diagnostic;
- do not rewrite the frozen internal gate as passed;
- use support/contact as paper-facing compatibility-route evidence with explicit caveat;
- do not claim support/contact is fully solved;
- do not move directly to a stronger combiner before result review;
- use `Q_e` as observability/selective-decision evidence, not truth.

## Next

```text
compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_result_review_and_claim_position
```
