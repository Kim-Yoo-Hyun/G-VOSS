# p_obs-Only Metric After Q_e Repair

## Role

This folder owns the p_obs-only diagnostic smoke test for repaired `Q_e v2`.
It evaluates whether the repaired observability representation can separate
observable rows from ambiguous/missing-evidence rows before any full
p_obs/p_rel selective-decision rerun.

## Current Status

```text
status = h002_pobs_prel_qe_repair_pobs_only_metric_ready
validation_errors = 0
train_rows = 14604
eval_rows = 265
p_obs_AUROC = 1.000000
p_obs_ECE_10 = 0.049266
p_obs_Brier = 0.004222
p_obs_NLL = 0.051518
abstain_precision = 1.000000
abstain_recall = 1.000000
observable_false_abstain_rate = 0.000000
false_observable_rate = 0.000000
legacy_all_sufficient_AUROC = 0.500000
legacy_all_sufficient_abstain_recall = 0.000000
diagnostic_pass = true
paper_level_pobs_prel_solved_claim_allowed = false
next_todo = pobs_prel_qe_repair_pobs_metric_review
```

## Outputs

```text
latest/metric_manifest.json
latest/gate_decision.json
latest/pobs_metrics.csv
latest/threshold_metrics.csv
latest/observability_label_metrics.csv
latest/risk_coverage_curve.csv
latest/reliability_diagram.csv
latest/prediction_scores.jsonl
latest/validation_errors.jsonl
```

## Boundary

The run uses `Q_e v2` only and excludes `qe_v2_diagnostic_source` from model
input. Because eval `Q_e v2` is audit-proxy diagnostic material, this result is
a bottleneck-repair smoke test, not paper-level calibrated p_obs/p_rel solved
evidence.
