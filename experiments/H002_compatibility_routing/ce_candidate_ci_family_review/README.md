# C_e Candidate CI / Family Review

## Role

This folder owns the Docker-backed promotion review for
`I4_calibrated_route_aware_source_x_Ce`.

It checks whether the calibrated route-aware C_e candidate can replace the
current main score `S2_current_source_x_Ce`.

## Current Status

```text
status = h002_ce_candidate_ci_family_review_ready
validation_errors = 0
n_bootstrap = 1000
candidate_score = I4_calibrated_route_aware_source_x_Ce
baseline_score = S2_current_source_x_Ce
promote_to_main_score = false
selected_path = keep_current_main_score_report_I4_as_candidate_or_ablation
next_todo = h002_ce_family_mitigation_or_keep_s2_boundary_update
```

## Key Result

Aggregate primary-route point estimates improve at K `{5,10,20,50}`:

```text
K=5:  Recall +0.005669, Violation -0.006937
K=10: Recall +0.015873, Violation -0.008769
K=20: Recall +0.021542, Violation -0.010512
K=50: Recall +0.007937, Violation -0.014035
```

However, promotion is blocked because family-wise review finds `5` violation
regression cells and `1` double-regression cell, concentrated in Open3DSG
`relative_vertical`.

## Outputs

```text
latest/summary.json
latest/primary_delta_ci.csv
latest/family_delta_ci.csv
latest/family_review.csv
latest/promotion_gate.csv
latest/point_metrics.csv
latest/report.md
latest/validation_errors.jsonl
```
