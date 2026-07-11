# Relative Horizontal Route Scorer

## Role

This folder owns the route-specific `relative_horizontal` scorer experiment for
`left`, `right`, `front`, and `behind`.

The scorer is separate from the locked generic `S2_current_source_x_Ce` score.
It tests whether a frame-aware directional residual can support a
route-specific H002 result.

## Latest Output

```text
latest = latest/
status = h002_relative_horizontal_route_scorer_ready
score = RH1_source_x_frame_score
validation_errors = 0
source_rows_scored = 254296
strict_balanced_main_route_pass = false
violation_control_route_pass = true
selected_path = allow_relative_horizontal_as_caveated_frame_aware_violation_control_route
```

## Outputs

| File | Role |
| --- | --- |
| `latest/score_manifest.json` | scorer definitions and no-tuning policy |
| `latest/source_family_metrics.csv` | source-wide Recall@K / Violation@K |
| `latest/source_predicate_metrics.csv` | left/right/front/behind slices |
| `latest/comparison_metrics.csv` | `RH1` deltas against source and controls |
| `latest/promotion_gate.csv` | strict vs caveated route decision gates |
| `latest/report.md` | runtime summary |
