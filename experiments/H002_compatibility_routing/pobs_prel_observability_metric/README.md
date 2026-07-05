# p_obs / p_rel Observability Metric

This folder stores the diagnostic p_obs / p_rel rerun on the 265-row
user-confirmed observability subset.

## Current Run

```text
latest/
```

Status:

```text
status = h002_pobs_prel_observability_metric_ready
validation_errors = 0
train_protocol = existing_internal_train_pobs_prel_materialization
eval_protocol = user_confirmed_265_row_observability_subset
pobs_train = 24340
pobs_eval = 265
prel_train = 4868
prel_eval = 135
p_obs_AUROC = 0.500000
p_obs_ECE_10 = 0.446174
p_rel_AUROC = 0.774704
p_rel_ECE_10 = 0.083819
decision_macro_F1 = 0.331637
diagnostic_metric_pass = false
paper_promotion_pass = false
next_todo = pobs_prel_observability_metric_result_review
```

## Interpretation

The rerun confirms that the current `Q_e` features do not distinguish
`observable_clear` from `ambiguous_evidence` or
`unobservable_missing_evidence`. All three label groups have median
`p_obs = 0.955608`, so the model never abstains on ambiguous or missing-evidence
rows.

`p_rel` still has useful signal on the observable subset, but p_obs fails as an
observability gate. This keeps calibrated p_obs / p_rel solved-claim wording
blocked.

## Files

| File | Role |
| --- | --- |
| `metric_manifest.json` | main metric result and boundary |
| `pobs_metrics.csv` | p_obs binary metric |
| `prel_metrics.csv` | p_rel binary metric on observable rows |
| `decision_metrics.csv` | accept/reject/abstain decision metric |
| `queue_kind_metrics.csv` | metrics grouped by queue source |
| `observability_label_metrics.csv` | metrics grouped by observability label |
| `risk_coverage_curve.csv` | coverage-risk data |
| `prediction_scores.jsonl` | row-level p_obs/p_rel/prediction scores |
| `validation_errors.jsonl` | validation errors; expected to be empty |
