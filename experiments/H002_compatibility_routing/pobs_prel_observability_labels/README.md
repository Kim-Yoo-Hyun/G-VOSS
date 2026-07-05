# p_obs / p_rel Observability Labels

This folder stores the filled observability labels for the p_obs / p_rel
extension audit queue.

## Current Run

```text
latest/
```

Status:

```text
status = h002_pobs_prel_observability_label_fill_ready
validation_errors = 0
filled_rows = 265
observable_clear = 135
ambiguous_evidence = 126
unobservable_missing_evidence = 4
human_confirmed = false
metric_rerun_allowed_now = false
next_todo = pobs_prel_observability_label_ingestion
```

## Files

| File | Role |
| --- | --- |
| `filled_observability_labels.jsonl` | Codex-filled observability labels for the audit queue |
| `label_summary.csv` | label and queue-kind count summary |
| `summary.json` | run manifest and boundary decision |
| `validation_errors.jsonl` | validation errors; expected to be empty |

## Boundary

These labels are `codex_filled_not_human_confirmed`. They are acceptable for the
next ingestion/schema-audit gate, but they should not be treated as
human-confirmed paper GT without user review.
