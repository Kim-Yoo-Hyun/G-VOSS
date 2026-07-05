# C_e Improvement Path

## Role

This folder owns the Docker-backed experiment-stage check for improving
`C_e = compatibility(T_e, G_e)` after p_obs/p_rel was demoted to optional
diagnostic/future evidence.

## Current Status

```text
status = h002_ce_improvement_path_ready
validation_errors = 0
source_rows_scored = 762888
best_primary_score = I4_calibrated_route_aware_source_x_Ce
calibrated_ce_candidate_pass = true
calibrated_ce_main_promotion = false
richer_ge_support_contact_promotion = false
pobs_prel_reopened = false
next_todo = h002_ce_candidate_ci_family_review_before_promotion
```

## Interpretation

The calibrated route-aware C_e variant improves primary comparison-route point
estimates over the current `S2_current_source_x_Ce`, but it is not promoted to
the main score before bootstrap CI and family-wise review.

The follow-up CI/family review has completed under
`../ce_candidate_ci_family_review/latest/`. It keeps I4 as a candidate
ablation/secondary result rather than replacing the current main score.

Support/contact remains blocked as a main hard route because the strict
shortcut-controlled repair leaves only `40` binary rows over `4` mixed
class-pairs.

## Outputs

```text
latest/summary.json
latest/score_condition_metrics.csv
latest/source_family_metrics.csv
latest/improvement_summary.csv
latest/ce_internal_calibration_metrics.csv
latest/stage_decision.csv
latest/report.md
latest/validation_errors.jsonl
```
