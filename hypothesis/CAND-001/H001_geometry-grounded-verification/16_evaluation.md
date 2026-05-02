# Evaluation

Last updated: 2026-05-03

## Role

This document defines the prediction-level evaluation protocol for H001.

The goal is to test whether explicit geometry evidence, relation-subtype-aware verification, and later probabilistic calibration reduce geometry-inconsistent relation predictions while preserving useful predicate/triplet recall.

This protocol is the bridge from smoke test to thesis-level evidence.

## Evaluation Claim

Primary claim:

```text
geometry-aware verification/recalibration reduces violation rate under comparable recall.
```

Secondary claim:

```text
subtype-aware geometry evidence produces interpretable failure modes and can be evaluated as a reusable benchmark component.
```

Do not claim success only because filtered predictions have fewer violations. If recall collapses, the method is not useful.

## Compared Conditions

Evaluate the same prediction set under four conditions:

| Condition | Description |
| --- | --- |
| `semantic_only` | Baseline relation predictions ranked by model score only. |
| `semantic_plus_evidence` | Predictions with geometry evidence attached but not filtered or reranked. |
| `rule_verified` | Predictions filtered or reranked by rule/subtype verifier status and score. |
| `probabilistic_recalibrated` | Predictions reranked by calibrated `p_geom_valid` and combined `p_final`. |

Minimal first comparison:

```text
semantic_only vs rule_verified
```

Full thesis comparison:

```text
semantic_only vs rule_verified vs probabilistic_recalibrated
```

## Prediction-Level Inputs

Required baseline prediction format:

```text
scan_id
subset_split_id
subject_id
object_id
subject_label
object_label
predicate_label
predicate_family
predicate_score
rank
baseline_name
```

Required ground-truth format:

```text
scan_id
subject_id
object_id
predicate_label
predicate_family
```

Required geometry inputs:

```text
semseg.v2.json
labels.instances.annotated.v2.ply
3DSSG object/relation annotations
```

Optional inputs:

```text
object detection confidence
instance mask confidence
open-vocabulary text score
p_geom_valid
```

## Predicate Scope

Primary benchmark subset:

| Family | Use |
| --- | --- |
| `support_contact` | Primary target; evaluate subtype-aware verifier. |
| `proximity` | Primary geometry-checkable relation family. |
| `relative_vertical` | Secondary geometry-checkable family. |

Deferred:

| Family | Reason |
| --- | --- |
| `relative_horizontal` | Coordinate-frame validation is unresolved. |
| `attachment_deferred` | Needs surface contact and orientation evidence. |
| `unsupported_first_pass` | Not reliably geometry-checkable in first protocol. |

Report all unsupported/deferred predictions as out of scope, not as failures.

## Evaluation Levels

### Level 0: Ground-Truth Smoke Test

Status:

```text
completed for one scan
```

Purpose:

- verify geometry joins;
- verify rule execution;
- verify support/contact subtype logic;
- identify geometry-source ambiguity.

This level is not prediction-level evidence.

### Level 1: Counterfactual Geometry Validity

Purpose:

```text
test whether geometry verifier rejects high-margin invalid relations
```

Use:

- ground-truth positives in geometry-checkable families;
- counterfactual negatives generated with high-margin geometric contradiction;
- uncertain cases excluded or reported separately.

Metrics:

```text
AUROC
AUPRC
precision at low p_geom_valid
false positive rate at fixed recall
```

This level supports verifier validity but still does not test model prediction recall.

### Level 2: Baseline Prediction Filtering/Reranking

Purpose:

```text
test whether verifier improves actual relation predictions
```

Input:

- predictions from at least one closed-set or open-vocabulary 3DSG baseline;
- same candidate predictions reused across all compared conditions.

Evaluate:

- original prediction rank;
- rule-filtered rank;
- rule-reranked rank;
- probabilistic reranked rank if calibration exists.

This is the minimum level required for H001 prediction-level validation.

### Level 3: Multi-Scan Generalization

Purpose:

```text
show that verifier and calibration behavior generalizes beyond one scan
```

Rules:

- split by scan, not by edge;
- tune thresholds only on train/validation scans;
- report held-out test scans once;
- report family and subtype breakdowns.

This level is required before making a strong thesis contribution claim.

## Ranking Policies

Hard filter:

```text
keep satisfied
drop violated
abstain or keep uncertain depending on the reported variant
```

Recommended variants:

| Variant | Policy |
| --- | --- |
| `filter_strict` | keep `satisfied`, drop `uncertain` and `violated` |
| `filter_safe` | keep `satisfied` and `uncertain`, drop `violated` |
| `rerank_rule` | multiply baseline score by rule consistency score |
| `rerank_prob` | multiply baseline score by calibrated `p_geom_valid` |

Default for first prediction-level run:

```text
filter_safe
```

Reason:

- `uncertain` often means geometry-source ambiguity, not relation falsehood;
- dropping uncertain cases can inflate violation reduction by harming recall.

## Core Metrics

### Standard Recall

Report standard relation metrics on the selected predicate subset:

```text
Predicate R@K
Predicate mR@K
Triplet R@K
Triplet mR@K
```

Use the same K values as the selected baseline when possible.

### Violation Rate

For top-K predictions within geometry-checkable scope:

```text
violation_rate@K =
  count(predictions judged violated by geometry verifier) /
  count(predictions judged satisfied, uncertain, or violated)
```

Also report coverage:

```text
geometry_coverage@K =
  count(predictions judged satisfied, uncertain, or violated) /
  count(geometry-checkable predictions)
```

Do not hide low coverage. A method that abstains on most edges has not solved the problem.

### Consistency-Filtered Recall

For top-K predictions after applying a geometry policy:

```text
consistency_filtered_R@K =
  correct predictions after geometry filtering or reranking /
  ground-truth positives in evaluated family
```

Report beside baseline recall:

```text
recall_retention@K =
  consistency_filtered_R@K /
  semantic_only_R@K
```

### Violation Reduction

```text
violation_reduction@K =
  (semantic_only_violation_rate@K - verified_violation_rate@K) /
  semantic_only_violation_rate@K
```

If the baseline violation rate is near zero, report absolute violation count and avoid percentage claims.

### Tradeoff Curve

Report a recall-violation tradeoff curve by sweeping:

```text
consistency_score threshold
p_geom_valid threshold
top-K cutoff
```

Useful scalar summaries:

```text
area under recall-violation curve
minimum violation rate at >= 90% recall retention
recall retention at 50% violation reduction
```

The 90% and 50% values are working thresholds for early comparison, not final statistical claims.

## Calibration Metrics

If `p_geom_valid` is available, include:

```text
Brier score
NLL
ECE
MCE
reliability diagram
```

These metrics evaluate probability quality, not relation recall.

Calibration evaluation must use held-out scans.

## Reporting Slices

Always report aggregate and sliced metrics:

```text
by predicate_family
by predicate_label
by support_subtype
by scan
by object class pair
by relation frequency bucket
```

Minimum required slices:

- `support_contact`;
- `proximity`;
- `relative_vertical`;
- support/contact subtype breakdown;
- head vs tail predicates if baseline predictions support it.

## Baseline Choices

First closed-set baseline decision:

```text
VL-SAT
```

Baseline id:

```text
vlsat_closed_set
```

Selection rationale:

- `VL-SAT` can produce prediction scores on 3DSSG/3RScan with the smallest credible reproducibility burden among the checked learned baselines;
- it is semantically stronger than an edge-only baseline, so geometry verification has a meaningful semantic prediction target;
- preserve its original evaluation protocol where possible;
- add geometry evaluation as an extra diagnostic, not as a replacement for standard metrics.

Use `SGGpoint` as edge-reasoning reference and `Open3DSG` as a later open-vocabulary baseline after prediction output format is stable.

## Benchmark Contribution

H001 can become a benchmark contribution if the project releases a reusable evaluation layer:

```text
geometry evidence export
relation verifier outputs
counterfactual negative generation
violation/recall metrics
calibration table schema
report templates
```

Benchmark artifact should include:

```text
scan split
predicate family mapping
geometry-checkable predicate subset
counterfactual generation policy
evaluation scripts
metric definitions
manual inspection protocol for uncertain cases
```

Claim boundary:

- This is not a new 3DSG dataset unless new annotations are released.
- It can be a geometry-consistency benchmark layer on top of 3DSSG/3RScan.
- The benchmark contribution is stronger if it evaluates both existing baseline predictions and generated counterfactual candidates.

## Generalization Evidence

Rule verifier generalization:

- thresholds fixed before test;
- held-out scan metrics;
- family/subtype breakdown;
- no manual retuning on failed test scans.

Probabilistic verifier generalization:

- calibrator trained only on train scans;
- hyperparameters selected on validation scans;
- calibration metrics reported on test scans;
- test performance compared against raw `consistency_score`.

Subtype generalization:

- each subtype reports coverage, violation rate, recall retention, and uncertainty rate;
- sparse subtypes fall back to family-level reporting;
- do not claim subtype-level improvement when subtype support is too small.

## Acceptance Criteria

Minimum useful result:

- prediction-level run exists for at least one baseline;
- violation rate decreases for at least one geometry-checkable family;
- recall retention is reported and remains usable;
- geometry coverage and uncertainty rate are reported.

Strong result:

- held-out scans show lower violation rate at comparable recall;
- support/contact subtype-aware verification improves over one hard support/contact rule;
- calibrated `p_geom_valid` improves reliability over raw `consistency_score`;
- gains are visible in both aggregate and family/subtype slices.

Weak or failed result:

- violation reduction is mostly caused by removing many correct predictions;
- verifier only catches trivial distance errors;
- generated negatives are too easy and do not match baseline prediction errors;
- performance disappears on held-out scans;
- calibration is not better than raw rule score.

## Required Output Files

When implemented, prediction-level evaluation should write:

```text
predictions.jsonl
geometry_evidence.jsonl
verification.jsonl
ranked_semantic_only.jsonl
ranked_rule_verified.jsonl
ranked_probabilistic.jsonl
metrics.json
report.md
```

Recommended artifact root:

```text
artifacts/evaluation/<baseline-name>/<split-name>/
```

Do not create this artifact directory until the first prediction-level run is actually implemented.

## Next

Before implementation:

1. Use `17_subset.md` as the subset strategy.
2. Use `18_baseline.md` as the baseline decision.
3. Use `19_schema.md` as the prediction JSONL contract.
4. Use `20_layout.md` and `artifacts/layout/vlsat/report.md` as the local `VL-SAT` layout compatibility result.
5. Use `21_eval_path.md` as the faithful `VL-SAT` eval path decision.
6. Use `22_prep.md` as the faithful layout prep policy.
7. Select H001-Mini validation scan payloads.
8. Define the calibration table schema.
9. Implement counterfactual negative export only after scan split is fixed.
