# Support/Contact Capacity Decision

This folder stores the H002 capacity decision after support/contact repair
materialization.

## Role

The decision determines whether the repaired `standing on` / `lying on`
support/contact target is large enough for a meaningful metric rerun or should
remain diagnostic.

## Current Output

```text
latest/
```

Key files:

| File | Role |
| --- | --- |
| `summary.json` | final capacity decision and next TODO |
| `capacity_options.csv` | considered paths and decisions |
| `decision_matrix.csv` | pass/fail gates for schema, capacity, and metric rerun readiness |
| `paper_boundary.csv` | allowed and blocked wording for paper claims |
| `reopen_conditions.csv` | conditions required to reopen support/contact as a solved route |
| `class_pair_capacity.csv` | mixed class-pair capacity evidence |
| `validation_errors.jsonl` | empty when decision synthesis passes |

## Boundary

Current support/contact remains diagnostic. Metric rerun and solved-route claims
are blocked because strict shortcut-controlled materialization leaves only 40
binary rows over four class-pairs.
