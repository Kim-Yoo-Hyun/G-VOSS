# Verifier v2

Last updated: 2026-04-30

## Role

This document fixes the implementation contract for the next H001 verifier.

`h001-verifier-v2` is a subtype-aware support/contact verifier. It is still a hypothesis-stage smoke test, not a benchmark method.

## Version

```text
h001-verifier-v2
```

Main change from `h001-rules-v1`:

```text
support_contact:
  one hard point/local-surface rule
  -> subtype assignment + subtype-specific evidence + soft consistency score
```

Unchanged from v1:

- preserve every input edge;
- keep non-support/contact families carried from the previous verifier;
- keep `uncertain` distinct from `violated`;
- report provenance and thresholds with every decision.

## Inputs

Required artifact inputs:

```text
artifacts/one_scan/<scan-id>/v1_decisions.jsonl
artifacts/one_scan/<scan-id>/point_evidence.jsonl
artifacts/one_scan/<scan-id>/thresholds.json
artifacts/one_scan/<scan-id>/visual_inspection/labels.jsonl
```

Required dataset input for plane/contact features:

```text
local_dataset/3RScan/scans/<scan-id>/labels.instances.annotated.v2.ply
```

Optional inputs:

```text
artifacts/one_scan/<scan-id>/visual_inspection/report.md
artifacts/one_scan/<scan-id>/v1_review_queue.jsonl
```

## Outputs

Write outputs into a short subfolder:

```text
artifacts/one_scan/<scan-id>/v2/
```

Required output files:

```text
decisions.jsonl
support.jsonl
transitions.jsonl
review.jsonl
summary.json
report.md
```

Output meaning:

| File | Meaning |
| --- | --- |
| `decisions.jsonl` | All relation edges with v2 verification objects. |
| `support.jsonl` | Support/contact-only subtype evidence and scores. |
| `transitions.jsonl` | v1 -> v2 status and score transitions for support/contact. |
| `review.jsonl` | Remaining support/contact uncertain/violated/geometry-quality cases. |
| `summary.json` | Counts, thresholds, validation, output paths. |
| `report.md` | Human-readable v2 summary. |

## Status Vocabulary

Keep the standard verifier status set:

| Status | Meaning |
| --- | --- |
| `satisfied` | Evidence supports the relation under the subtype rule. |
| `uncertain` | Evidence is weak, ambiguous, sparse, or geometry-source quality is insufficient. |
| `violated` | Evidence contradicts the relation under the subtype rule with enough confidence. |
| `unsupported` | Predicate is outside the verifier scope. |

Important policy:

- `violated` is a verifier decision, not a final annotation-error claim.
- `uncertain` must be used for scan/instance ambiguity.
- Visual labels are diagnostic evidence, not training labels for a final model.

## Subtypes

For `support_contact`, assign exactly one v2 subtype:

| Subtype | Trigger | Default status bias |
| --- | --- | --- |
| `legged_floor_support` | support object is `floor`, predicate is support/contact, subject is furniture-like or has sparse low contact | avoid false violation from p05/p95 gap |
| `soft_support_contact` | predicate is `lying on` or subject/object is soft/deformable | allow bounded negative penetration |
| `rigid_object_on_furniture` | support object is not floor and relation is rigid support on furniture | require local horizontal support-plane evidence |
| `geometry_quality_uncertain` | visual label or evidence indicates instance/scan ambiguity | prefer `uncertain` over `violated` |

Subtype priority:

```text
if visual label indicates segmentation_or_instance_issue:
    geometry_quality_uncertain
elif predicate is lying on or subject/object is soft:
    soft_support_contact
elif object label is floor:
    legged_floor_support
elif support object is furniture-like:
    rigid_object_on_furniture
else:
    rigid_object_on_furniture
```

Initial soft object labels:

```text
pillow
cushion
blanket
clothes
towel
```

Initial furniture support labels:

```text
table
desk
kitchen counter
counter
cabinet
shelf
sofa
chair
bed
stool
bench
```

These lists are smoke-test heuristics. They should be reported as implementation assumptions.

## Evidence Fields

Every support/contact v2 record must include:

```text
edge_id
subject_id
object_id
subject_label
predicate_label
object_label
previous_status
subtype
subtype_reason_codes
point_evidence_available
visual_label
geometry_quality_flags
consistency_score
status
reason_codes
```

Carry from point evidence when available:

```text
support_points_under_subject_count
xy_expansion_m
local_vertical_gap_p05_p95
local_vertical_gap_p01_p99
subject_point_stats
object_point_stats
```

Add subtype-specific fields.

For `legged_floor_support`:

```text
low_percentile_gap_m
robust_gap_m
support_density_score
contact_fraction_score
leg_contact_score
```

For `soft_support_contact`:

```text
signed_gap_m
penetration_depth_m
positive_float_gap_m
soft_prior
soft_gap_score
support_density_score
```

For `rigid_object_on_furniture`:

```text
plane_available
plane_z_m
plane_inlier_count
plane_inlier_ratio
plane_residual_m
plane_normal_z_abs
plane_gap_m
plane_confidence
```

For `geometry_quality_uncertain`:

```text
geometry_issue_source
point_density_flag
instance_completeness_flag
visual_ambiguity_flag
```

If a subtype-specific field cannot be computed, set it to `null` and add a reason code. Do not silently omit expected fields.

## Score Contract

Each support/contact edge must emit:

```text
consistency_score: float in [0, 1]
score_components: object
```

Interpretation:

| Score range | Status |
| --- | --- |
| `>= 0.70` | `satisfied` |
| `>= 0.40` and `< 0.70` | `uncertain` |
| `< 0.40` | `violated` |

Override:

```text
if subtype == geometry_quality_uncertain:
    status = uncertain
```

The score is not a calibrated probability yet. It is a soft geometry consistency score designed so that later prediction-level work can calibrate it.

## Score Components

### Legged Floor Support

Use signed low-percentile contact more heavily than robust p05/p95 gap.

Required signals:

```text
low_percentile_gap_m = local_vertical_gap_p01_p99
robust_gap_m = local_vertical_gap_p05_p95
support_points_under_subject_count
```

Initial score:

```text
leg_contact_score = high when abs(low_percentile_gap_m) <= 0.08
support_density_score = high when support point count is sufficient
consistency_score = 0.70 * leg_contact_score + 0.30 * support_density_score
```

Policy:

- Do not directly violate a case only because `robust_gap_m` is high.
- If low-percentile and robust gaps are both high, return `uncertain` unless visual or multi-scan evidence supports a violation.

### Soft Support Contact

Use signed gap asymmetrically.

Required signals:

```text
signed_gap_m = local_vertical_gap_p05_p95
penetration_depth_m = max(0, -signed_gap_m)
positive_float_gap_m = max(0, signed_gap_m)
support_points_under_subject_count
soft_prior
```

Initial score:

```text
soft_gap_score = high for bounded negative gap and small positive gap
support_density_score = high when local support points exist
consistency_score = 0.55 * soft_gap_score + 0.30 * support_density_score + 0.15 * soft_prior
```

Policy:

- Bounded negative penetration is not a violation by itself.
- Positive floating gap should be penalized more strongly than negative soft penetration.

### Rigid Object On Furniture

Estimate a local horizontal support plane before judging support gap.

Required signals:

```text
local support points near subject footprint
horizontal plane candidate
plane residual
plane normal alignment
subject bottom to plane gap
```

Initial score:

```text
plane_confidence = function(inlier_count, inlier_ratio, normal_z_abs, residual)
plane_gap_score = high when abs(plane_gap_m) <= 0.08
consistency_score = 0.55 * plane_gap_score + 0.35 * plane_confidence + 0.10 * support_density_score
```

Policy:

- If no reliable horizontal plane is found, return `uncertain`.
- Raw support z percentiles alone are not enough to call a counter/table support relation violated.

### Geometry Quality Uncertain

This subtype does not use the normal score-to-status mapping.

Required signals:

```text
visual label
point density
object bottom/support mismatch
missing or sparse object points
```

Policy:

- Set `status = uncertain`.
- Set `consistency_score = null` if a meaningful score cannot be computed.
- Keep the edge in `review.jsonl`.

## Reason Codes

Allowed v2 reason codes:

```text
subtype_legged_floor_support
subtype_soft_support_contact
subtype_rigid_object_on_furniture
subtype_geometry_quality_uncertain
leg_contact_low_percentile_supported
robust_gap_too_strict_for_legs
soft_penetration_allowed
positive_float_gap_large
horizontal_plane_found
horizontal_plane_missing
plane_gap_supported
plane_gap_large
surface_estimator_uncertain
visual_rule_too_strict
visual_local_surface_issue
visual_geometry_quality_issue
carried_from_v1
```

## Decision Record Schema

Each `decisions.jsonl` record should preserve the original v1 edge fields and write a v2 `verification` object.

Required verification fields:

```text
rule_version
previous_rule_version
previous_status
status
predicate_family
support_subtype
consistency_score
score_components
checked_constraints
passed_constraints
failed_constraints
uncertain_constraints
reason_codes
threshold_config
visual_label
geometry_quality_flags
```

For non-support/contact families:

```text
support_subtype = null
consistency_score = previous geometry_score
reason_codes include carried_from_v1
```

## Metrics

Report:

```text
all_edge_count
support_contact_edge_count
support_subtype_counts
support_subtype_status_counts
v1_to_v2_status_transitions
visual_label_to_v2_status_counts
mean_consistency_score_by_subtype
review_count
geometry_quality_uncertain_count
```

Evaluation-oriented diagnostic metrics:

```text
violation_rate_on_support_contact
uncertain_rate_on_support_contact
visually_plausible_violation_count
```

These are still one-scan diagnostics. Prediction-level metrics such as R@K, mR@K, and consistency-filtered recall require model predictions.

## Validation

Validation errors:

- missing required input file;
- missing `point_evidence.jsonl` for any support/contact edge;
- support/contact edge without subtype assignment;
- support/contact edge without status;
- non-null consistency score outside `[0, 1]`;
- missing output path;
- output edge count differs from input edge count.

Validation warnings:

- geometry-quality uncertain cases remain;
- horizontal plane unavailable for rigid furniture support;
- visual labels not available for some review cases;
- v2 still has visually plausible edges marked `violated`.

Pass condition for the one-scan smoke test:

```text
all 772 edges preserved
all 32 support/contact edges assigned a subtype
visual geometry-quality case remains uncertain
v2 does not increase visually plausible violations over v1
summary/report/review artifacts written
```

## Implementation Scope

Implement as a hypothesis-internal script:

```text
tools/apply_verifier_v2.py
```

Scope:

- read existing v1 decisions and point evidence;
- parse PLY only for support/contact point subsets needed by subtype evidence;
- assign support/contact subtypes;
- compute soft consistency score;
- emit v2 artifacts under `artifacts/one_scan/<scan-id>/v2/`;
- preserve non-support/contact edges by carrying v1 decisions forward.

Out of scope:

- training a learned probability model;
- baseline model reproduction;
- multi-scan benchmark claims;
- open-vocabulary prediction-level evaluation.

## One-Scan Result

Implemented script:

```text
tools/apply_verifier_v2.py
```

Execution artifact:

```text
artifacts/one_scan/f62fd5fd-9a3f-2f44-883a-1e5cf819608e/v2/
```

Result:

| Metric | Value |
| --- | ---: |
| all edges | 772 |
| support/contact edges | 32 |
| satisfied | 31 |
| uncertain | 1 |
| violated | 0 |
| review count | 1 |
| visually plausible violations | 0 |

Validation:

```text
passed: true
errors: 0
warnings: 1
```

The one warning is expected: this remains a hypothesis-stage smoke test, not benchmark evidence.

Inference:

- The v2 contract is implementable on the current one-scan artifact.
- Subtype-aware support/contact logic is sufficient to remove the v1 visually plausible false violations in this scan.
- The remaining uncertain case is a geometry-quality case, not a rule failure.
- The next research step should turn the soft consistency score into a calibrated evaluation design instead of adding more hard-coded rules.

## Next Step

After this one-scan smoke test, decide whether to:

```text
run multi-scan replication
design prediction-level evaluation
calibrate geometry consistency score against model predictions
```
