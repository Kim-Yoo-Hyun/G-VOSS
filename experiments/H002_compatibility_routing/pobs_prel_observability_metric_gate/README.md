# p_obs / p_rel Observability Metric Gate

This folder records the decision to allow a diagnostic p_obs / p_rel metric
rerun after user review of the Codex-filled observability labels.

## Current Run

```text
latest/
```

Status:

```text
status = h002_pobs_prel_observability_metric_gate_ready
validation_errors = 0
rows = 265
user_review_completed = true
metric_rerun_allowed_now = true
metric_scope = diagnostic_observability_subset_rerun
paper_level_gt_claim_allowed = false
next_todo = pobs_prel_observability_metric_rerun
```

## Boundary

The raw label file still records `human_confirmed=false` because the labels were
initially filled by Codex. This gate records the user's confirmation that those
labels may be treated as user-confirmed for a diagnostic metric rerun. It does
not convert the labels into an independently human-authored paper benchmark.
