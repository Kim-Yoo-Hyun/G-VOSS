# p_obs / p_rel Observability Metric Review

This folder stores the result review for the diagnostic p_obs / p_rel rerun on
the 265-row user-confirmed observability subset.

## Current Run

```text
latest/
```

Status:

```text
status = h002_pobs_prel_observability_metric_result_review_ready
validation_errors = 0
p_obs_status = failed_observability_gate
p_rel_status = diagnostic_signal_present
selective_decision_status = failed_due_to_no_abstain_behavior
pobs_prel_framework_component_allowed = true
pobs_prel_solved_claim_allowed = false
paper_promotion_pass = false
next_todo = pobs_prel_qe_repair_plan
```

## Key Result

```text
p_obs_AUROC = 0.500000
p_obs_ECE_10 = 0.446174
p_rel_AUROC = 0.774704
p_rel_ECE_10 = 0.083819
decision_macro_F1 = 0.331637
```

The failure is a `Q_e` feature/label mismatch: ambiguous and missing-evidence
rows are labeled as abstain targets, but the model-safe `Q_e` view still marks
all label groups as sufficient.

## Files

| File | Role |
| --- | --- |
| `summary.json` | review decision and next TODO |
| `review_decision.csv` | p_obs / p_rel / selective-decision pass-fail summary |
| `qe_feature_gap.csv` | Q_e feature-label mismatch audit |
| `qe_repair_plan.csv` | ordered Q_e repair plan |
| `paper_boundary.csv` | allowed and blocked paper claims |
| `report.md` | compact human-readable review |
| `validation_errors.jsonl` | validation errors; expected to be empty |
