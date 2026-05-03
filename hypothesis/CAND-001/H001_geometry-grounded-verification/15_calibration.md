# Calibration

Last updated: 2026-05-03

## Role

This document defines how H001 should move from rule-based geometry consistency scores to probabilistic calibration.

The current `h001-verifier-v2` score is not a probability. It is a smoke-test consistency score used to check whether explicit geometry evidence can support, weaken, or reject a candidate relation.

## Decision

Do not claim that `consistency_score` is calibrated.

Use the v2 score and its components as inputs to a later calibrator:

```text
relation candidate + semantic score + geometry evidence + subtype
-> p_geom_valid
```

Where:

```text
p_geom_valid = P(relation is geometrically valid | relation candidate, geometry evidence, subtype)
```

This is not the same as:

```text
P(relation is semantically true)
```

For final prediction ranking, use a separate combined score:

```text
p_final = combine(p_semantic, p_geom_valid)
```

The simplest first combination can be:

```text
p_final = p_semantic * p_geom_valid
```

Later work can replace this with a learned fusion model.

## Current Status

Completed:

```text
calibration target design
label source design
negative construction policy
feature set design
calibration metric design
scan-level split requirement
```

Not completed:

```text
calibration table export
counterfactual negative generation
p_geom_valid model fitting
calibration metric computation
held-out scan validation
```

Reason:

Calibration cannot be implemented meaningfully on the current one-scan v2 artifact alone. The current one-scan result has almost all support/contact scores near the satisfied range and no real held-out negatives. A calibrator fitted here would only overfit the smoke test.

Therefore calibration should wait until the subset strategy is fixed and the next implementation inputs exist. As of 2026-05-03, the official `3DSSG_subset` strategy is fixed in `17_subset.md`, and the `VL-SAT` layout checker is implemented in `tools/check_layout.py`; the remaining gates are:

```text
faithful VL-SAT staged-root prep
calibration table schema
counterfactual negative generation
additional scan payloads
```

After these gates, calibration implementation should resume with calibration table export and `p_geom_valid` fitting/evaluation.

## One-Scan Diagnosis

Current v2 artifact:

```text
artifacts/one_scan/f62fd5fd-9a3f-2f44-883a-1e5cf819608e/v2/
```

Result:

| Metric | Value |
| --- | ---: |
| all edges | 772 |
| support/contact edges | 32 |
| v2 satisfied | 31 |
| v2 uncertain | 1 |
| v2 violated | 0 |
| visually plausible v2 violations | 0 |

Subtype score ranges:

| Subtype | Count | Score range |
| --- | ---: | --- |
| `legged_floor_support` | 15 | 0.823 - 1.000 |
| `soft_support_contact` | 11 | 0.798 - 1.000 |
| `rigid_object_on_furniture` | 5 | 0.960 - 1.000 |
| `geometry_quality_uncertain` | 1 | null |

Inference:

- The current one-scan result confirms that the evidence path and subtype logic are executable.
- The one-scan result is not enough to learn calibration because scores are saturated near 1.0 and there are no true negative support/contact examples.
- Calibration requires multi-scan evidence and deliberately constructed invalid or counterfactual candidate relations.

## Calibration Target

Primary calibrated output:

```text
p_geom_valid
```

Required auxiliary outputs:

```text
calibration_family
support_subtype
abstain_reason
calibration_features
label_source
```

Decision policy after calibration:

| Output | Meaning |
| --- | --- |
| high `p_geom_valid` | geometry supports keeping or ranking up the relation |
| low `p_geom_valid` | geometry supports filtering or ranking down the relation |
| abstain | geometry source is ambiguous, sparse, or outside calibrated scope |

Do not force `geometry_quality_uncertain` into a probability unless the geometry source quality can be modeled explicitly.

## Labels

Calibration labels should be:

```text
geom_valid in {1, 0, uncertain}
```

Positive labels:

- ground-truth 3DSSG relation edges in geometry-checkable families;
- visual/manual labels that mark the relation as geometrically plausible;
- generated positives only if they preserve the same relation and pass strict geometry checks.

Negative labels:

- counterfactual relation candidates generated to contradict geometry;
- model-predicted relations manually or automatically judged as geometry-invalid;
- predicate swaps that create a geometry contradiction with high margin.

Uncertain labels:

- scan/instance ambiguity;
- sparse or partial point evidence;
- coordinate-frame ambiguity;
- semantic relations whose geometry validity is not well defined.

Policy:

- Do not use the verifier status itself as the training label.
- Do not treat all absent 3DSSG edges as negatives.
- Do not train calibration on labels generated from the same exact rule threshold being calibrated.

## Counterfactual Negatives

Use high-margin negatives to avoid false negative labels.

Support/contact:

- keep the subject and predicate, replace the support object with a far or vertically incompatible object;
- keep the object and predicate, replace the subject with an object whose bottom is clearly far from the support plane;
- generate `standing on` or `lying on` candidates where local support evidence has large positive floating gap or impossible horizontal support.

Proximity:

- generate `close by` candidates from object pairs with large normalized XY distance;
- exclude pairs whose bounding boxes or point footprints overlap.

Relative vertical:

- invert `higher than` / `lower than` for pairs with large signed z margin;
- exclude near-tie vertical pairs.

Relative horizontal:

- do not use for calibration until coordinate-frame validation is complete.

## Feature Set

Common features:

```text
predicate_family
predicate_label
subject_label
object_label
geometry_available
geometry_quality_flags
consistency_score
status_before_calibration
```

Optional semantic feature:

```text
p_semantic or model_relation_score
```

Support/contact subtype features:

```text
support_subtype
support_points_under_subject_count
local_vertical_gap_p05_p95
local_vertical_gap_p01_p99
support_density_score
```

For `legged_floor_support`:

```text
low_percentile_gap_m
robust_gap_m
leg_contact_score
```

For `soft_support_contact`:

```text
signed_gap_m
penetration_depth_m
positive_float_gap_m
soft_gap_score
```

For `rigid_object_on_furniture`:

```text
plane_available
plane_inlier_count
plane_inlier_ratio
plane_residual_m
plane_gap_m
plane_confidence
```

## Calibration Models

Stage 0: score binning sanity check.

- Bin uncalibrated `consistency_score`.
- Report empirical validity per bin.
- This only diagnoses whether scores are monotonic.

Stage 1: simple calibrator.

- Use logistic regression or Platt scaling over `consistency_score` plus subtype/family indicators.
- Use isotonic regression only if validation data is large enough.
- Train and validate by scan split, not by random edge split.

Stage 2: hierarchical subtype calibrator.

- Share a global family-level calibrator.
- Add subtype-specific offsets only when each subtype has enough examples.
- Fall back to family-level calibration for sparse subtypes.

Stage 3: semantic-geometry fusion.

- Add baseline prediction confidence as `p_semantic`.
- Learn or define `p_final = combine(p_semantic, p_geom_valid)`.
- Evaluate whether geometry improves reliability without destroying recall.

## Metrics

Calibration metrics:

```text
Brier score
NLL
ECE
MCE
reliability diagram
```

Invalid-relation detection metrics:

```text
AUROC
AUPRC
precision at low p_geom_valid
coverage at fixed violation budget
```

Abstention metrics:

```text
abstain_rate
uncertain_rate_by_family
uncertain_rate_by_subtype
manual_review_rate
```

Downstream metrics are defined in the next protocol, not here:

```text
violation rate
consistency-filtered R@K
consistency-filtered mR@K
recall-violation tradeoff curve
```

## Data Split

Calibration must split by scan:

```text
train scans
validation scans
test scans
```

Do not place edges from the same scan in both train and validation/test. Object co-occurrence, room layout, and scan-specific geometry quality can leak if edge-level random splitting is used.

Minimum practical target before fitting:

| Family | Minimum target |
| --- | ---: |
| support/contact positives | 100+ |
| support/contact counterfactual negatives | 100+ |
| proximity positives/negatives | 100+ each |
| relative vertical positives/negatives | 100+ each |

These numbers are working thresholds, not final statistical guarantees.

## Acceptance Criteria

The calibration direction is useful if:

- `p_geom_valid` is monotonic with empirical geometry validity;
- ECE and Brier score improve over raw `consistency_score`;
- invalid counterfactual relations receive low probability;
- abstention catches geometry-quality cases instead of forcing false precision;
- downstream filtering reduces violation rate without collapsing recall.

The direction is weak if:

- calibration only learns trivial distance thresholds;
- one subtype dominates the learned model;
- generated negatives are too easy and do not transfer to model predictions;
- `p_geom_valid` is not better than the uncalibrated v2 score;
- recall improvement depends on removing most relation candidates.

## Smoke-Test Boundary

Completed smoke-test evidence proves:

```text
explicit geometry evidence can be exported;
support/contact needs point/local surface evidence;
subtype-aware support/contact verification removes v1 false violations in one scan;
calibration features can be emitted from v2 artifacts.
```

It does not prove:

```text
prediction-level reliability improvement;
calibrated probability correctness;
multi-scan generalization;
open-vocabulary relation performance.
```

## Next

Before implementing a calibrator:

1. Use `16_evaluation.md` as the evaluation protocol.
2. Use `17_subset.md` as the subset strategy.
3. Use `artifacts/layout/vlsat/report.md` as the current layout blocker record.
4. Use `21_eval_path.md` as the faithful eval path decision.
5. Use `22_prep.md` as the faithful layout prep policy.
6. Use `23_mini.md` as the selected validation scan set.
7. Implement faithful staged-root prep for selected scans.
8. Define a calibration table schema.
9. Export a calibration table from v2-style artifacts.
10. Generate high-margin counterfactual negatives.
