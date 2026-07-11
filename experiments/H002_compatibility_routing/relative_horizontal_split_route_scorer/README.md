# Relative Horizontal Split Route Scorer

## Role

This folder owns the split-route review for `relative_horizontal`. It ranks each
sub-route candidate pool independently; it does not filter from the full
`relative_horizontal` top-K list.

It separates:

- `lateral_left_right`: `left`, `right`
- `depth_front_behind`: `front`, `behind`

The split uses the existing frozen `RH1_source_x_frame_score`; it does not tune
the score after seeing results.

## Latest Output

```text
latest = latest/
status = h002_relative_horizontal_split_route_scorer_ready
validation_errors = 0
lateral_left_right = include_as_caveated_lateral_main_route
lateral_left_right_lock_status = caveated_lateral_main_validated_route
lateral_left_right_win_cells = 15/20
lateral_left_right_recall_loss_gt_0p05_cells = 0
depth_front_behind = classify_as_depth_reference_frame_failure_case
depth_front_behind_win_cells = 11/20
depth_front_behind_recall_loss_gt_0p05_cells = 8
```

## Outputs

| File | Role |
| --- | --- |
| `latest/subroute_metrics.csv` | Recall@K / Violation@K by source, subroute, score, and K |
| `latest/subroute_delta_metrics.csv` | `RH1` deltas against source baseline and controls |
| `latest/subroute_win_count.csv` | win-count, recall-loss, Violation-regression, and control summary |
| `latest/promotion_gate.csv` | subroute pass/fail gates |
| `latest/lateral_bootstrap_ci.csv` | bootstrap CI for lateral `S0`/`RH1` deltas |
| `latest/lateral_compact_table.csv` | compact `left/right` table for table-planning review |
| `latest/report.md` | runtime summary |
