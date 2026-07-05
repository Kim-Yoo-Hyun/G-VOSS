# p_obs / p_rel Observability Repair

This folder stores the H002 repair package for observability-aware p_obs / p_rel
targets.

## Role

The current p_obs / p_rel metrics are not promoted as calibrated solved claims
because the real asset audit has only `observable` labels, while negative or
ambiguous observability labels come from synthetic controls. This root defines a
real visual/mesh audit label schema and creates a queue for label filling.

## Current Output

```text
latest/
```

Key files:

| File | Role |
| --- | --- |
| `summary.json` | status, blockers, decision, and next TODO |
| `observability_gap.csv` | current p_obs / p_rel blockers and repair actions |
| `label_schema.csv` | allowed observability labels and target semantics |
| `observability_label_queue.jsonl` | visual/mesh audit queue |
| `queue_summary.csv` | queue composition |
| `gate_plan.csv` | pass/fail gates before metric rerun |
| `next_steps.csv` | label-fill, ingestion, and metric-rerun order |
| `validation_errors.jsonl` | empty when repair synthesis passes |

## Boundary

This root does not run metrics and does not create final observability GT. It
creates the label queue needed before p_obs / p_rel can be evaluated as a
calibrated solved component.
