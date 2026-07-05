# Support/Contact Generalization Repair

This folder stores the H002 experiment-stage synthesis for repairing the
support/contact hard route.

## Role

The current support/contact route is not solved. This root records why the
previous hard-route metric failed and freezes the next repair direction before
new materialization or metric runs.

## Current Output

```text
latest/
```

Key files:

| File | Role |
| --- | --- |
| `summary.json` | status, metrics, decision, and next TODO |
| `feature_gap.csv` | current `G_e` availability and label-wise feature diagnostics |
| `predicate_error_summary.csv` | `standing on` / `lying on` high-confidence error summary |
| `class_pair_error_summary.csv` | class-pair concentration of high-confidence errors |
| `failure_taxonomy.csv` | root-cause taxonomy for the failed support/contact route |
| `repair_protocol.csv` | pose-aware relabel/abstain repair steps |
| `gate_plan.csv` | pass/fail gates for the next repaired materialization |
| `validation_errors.jsonl` | empty when synthesis validation passes |

## Boundary

This root does not promote support/contact as a solved route. The selected next
path is pose-aware relabel/abstain materialization before more model capacity or
new metrics.
