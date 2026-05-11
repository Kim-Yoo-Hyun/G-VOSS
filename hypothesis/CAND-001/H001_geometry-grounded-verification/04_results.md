# Results

Last updated: 2026-05-07

## Role

This document merges H001-Mini results, hardened metrics, ablation/control
results, GT-based verifier evaluation, and evidence-lock interpretation.

Merged former files:

- `06_results.md`
- `07_summary.md`
- `12_ablation.md`
- `21_evidence_lock.md`
- `22_gt_eval.md`

## H001-Mini Result

H001-Mini role:

```text
smoke/pilot only
```

Facts:

| Condition | R@50 | R@100 | Violation@50 | Violation@100 |
| --- | ---: | ---: | ---: | ---: |
| `semantic_only` | 0.8741 | 0.9263 | not final | not final |
| `rule_verified` | 0.8777 | 0.9299 | diagnostic | diagnostic |
| `probabilistic_recalibrated` | 0.8831 | 0.9353 | 0.0061 | 0.0193 |

Inference:

- H001-Mini showed a positive but insufficient signal.
- It justified hardened validation, but is not top-tier-ready evidence.

## Hardened Prediction Metrics

Fixed hardened scope:

| Item | Count |
| --- | ---: |
| scans | 127 |
| subgraphs | 388 |
| prediction rows | 673,816 |
| ground-truth rows | 7,505 |
| in-scope prediction rows | 155,496 |
| in-scope GT denominator | 2,545 |

Main result:

| Condition | R@50 | R@100 | Violation@50 | Violation@100 |
| --- | ---: | ---: | ---: | ---: |
| `semantic_only` | 0.9599 | 0.9894 | 0.0247 | 0.0469 |
| `rule_verified_point_subtype` | 0.9587 | 0.9890 | 0.0000 | 0.0000 |
| `probabilistic_recalibrated` | 0.9642 | 0.9921 | 0.0234 | 0.0391 |
| `family_specific_p_geom_valid` | 0.9619 | 0.9914 | 0.0204 | 0.0310 |

Delta versus `semantic_only`:

| Condition | dR@50 | dR@100 | dViolation@50 | dViolation@100 |
| --- | ---: | ---: | ---: | ---: |
| `probabilistic_recalibrated` | +0.0043 | +0.0028 | -0.0014 | -0.0078 |
| `family_specific_p_geom_valid` | +0.0020 | +0.0020 | -0.0044 | -0.0159 |
| `rule_verified_point_subtype` | -0.0012 | -0.0004 | -0.0247 | -0.0469 |

Inference:

- The strongest scoped result is probabilistic reranking, not hard filtering.
- `family_specific_p_geom_valid` is a stricter violation-first operating point.
- `rule_verified_point_subtype` gives zero top-k violations with a small recall
  cost and should be framed as a diagnostic/operating point.

## Nontriviality Controls

| Control | R@50 | R@100 | Violation@50 | Violation@100 | Reading |
| --- | ---: | ---: | ---: | ---: | --- |
| `control_p_geom_valid_only` | 0.2028 | 0.5049 | 0.0642 | 0.0701 | semantics remain necessary |
| `control_distance_only` | 0.3835 | 0.5642 | 0.0731 | 0.0993 | not a simple distance heuristic |
| `control_shuffled_geometry` | 0.9297 | 0.9788 | 0.0289 | 0.0559 | instance-specific geometry matters |
| `control_wrong_pair_geometry` | 0.9242 | 0.9788 | 0.0302 | 0.0581 | object-pair geometry matters |

Inference:

- The positive signal is not explained by geometry alone, distance alone, a
  shuffled geometry distribution, or wrong-pair geometry.

## GT-Based Verifier Evaluation

Setup:

- GT positives from the fixed hardened validation scope.
- GT-derived counterfactual negatives generated without changing scan split,
  verifier, thresholds, or calibrator.

Counts:

| Item | Count |
| --- | ---: |
| GT positives | 2,545 |
| GT-derived negatives | 2,545 |
| total rows | 5,090 |

Main result:

| Metric | Value |
| --- | ---: |
| GT-positive nonviolated rate | 0.9972 |
| GT-derived negative nonsatisfied rate | 0.9694 |
| `p_geom_valid` Brier | 0.0538 |
| `p_geom_valid` AUROC | 0.9779 |
| `p_geom_valid` AUPRC | 0.9737 |

Family breakdown:

| Family | Positive nonviolated | Negative nonsatisfied | AUROC |
| --- | ---: | ---: | ---: |
| `proximity` | 1.0000 | 1.0000 | 0.9980 |
| `relative_vertical` | 1.0000 | 1.0000 | 0.9088 |
| `support_contact` | 0.9942 | 0.9349 | 0.9906 |

Inference:

- The verifier and frozen `p_geom_valid` separate held-out geometry-valid GT
  positives from deterministic geometry-invalid counterfactuals.
- This reduces the need for large human audit, while keeping qualitative visual
  sanity check as supporting evidence.

## Evidence Lock

Evidence-lock status:

```text
scoped_hypothesis_evidence_locked_with_reduced_visual_sanity_check
```

Allowed conclusion:

```text
On reproduced VL-SAT 3DSSG predictions, geometry-calibrated relation
verification improves relation reliability for geometry-checkable families by
reducing geometry-inconsistent top-k predictions while preserving or improving
useful recall.
```

Remaining blockers:

- `second_source_metric_missing_for_baseline_agnostic_claim`
- `open_vocab_adapter_metric_missing_for_broad_open_vocabulary_claim`

## Canonical Artifacts

| Artifact | Path |
| --- | --- |
| hardened predictions | `artifacts/evaluation/vlsat_closed_set/hardened/predictions.jsonl` |
| hardened ground truth | `artifacts/evaluation/vlsat_closed_set/hardened/ground_truth.jsonl` |
| hardened geometry join | `artifacts/evaluation/vlsat_closed_set/hardened_geometry/verification.jsonl` |
| hardened metrics | `artifacts/evaluation/vlsat_closed_set/hardened_metrics/metrics.json` |
| G3 controls | `artifacts/evaluation/vlsat_closed_set/hardened_g3/metrics.json` |
| GT verifier evaluation | `artifacts/evaluation/vlsat_closed_set/hardened/gt_eval/manifest.json` |
| evidence lock | `artifacts/evaluation/vlsat_closed_set/hardened/evidence_lock/manifest.json` |
