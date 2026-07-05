# p_obs / p_rel Evaluation

## Role

This folder owns selective-decision metrics for the H002 p_obs / p_rel
extension.

It trains from the internal H002 split and evaluates on official-validation
materialized rows without tuning on validation labels.

## Metrics

- `p_obs`: AUROC, AUPRC, Brier, ECE
- `p_rel`: AUROC, AUPRC, Brier, ECE
- selective decision: accept / reject / abstain macro-F1
- missing-evidence controls: abstain rate and p_obs collapse
- risk-coverage curve and AURC

## Current Output

```text
latest/gate_decision.json
latest/eval_manifest.json
latest/pobs_metrics.csv
latest/prel_metrics.csv
latest/decision_metrics.csv
latest/missing_evidence_control_metrics.csv
latest/risk_coverage_curve.csv
latest/prediction_scores.jsonl
latest/validation_errors.jsonl
```

## Boundary

This is a selective stress-test unless independent human observability labels
are added. A passing result can support p_obs / p_rel as a framework component,
but paper promotion still needs calibration review, qualitative examples, and
failure wording.
