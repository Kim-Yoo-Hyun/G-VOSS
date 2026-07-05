# p_obs / p_rel Observability Schema Audit

This folder stores the schema-separation audit for the ingested p_obs / p_rel
observability labels.

## Current Run

```text
latest/
```

Status:

```text
status = h002_pobs_prel_observability_schema_audit_ready
validation_errors = 0
blocked_field_hits = 0
qe_rows = 265
prel_rows = 265
hidden_rows = 265
observable_clear = 135
ambiguous_evidence = 126
unobservable_missing_evidence = 4
human_confirmed = false
metric_rerun_allowed_now = false
next_todo = pobs_prel_observability_metric_gate_decision
```

## Files

| File | Role |
| --- | --- |
| `summary.json` | audit result, counts, boundary, and next decision |
| `schema_separation_audit.csv` | model-safe / hidden separation checks |
| `label_balance.csv` | label and decision balance after ingestion |
| `blocked_field_hits.jsonl` | blocked model-safe field hits; expected to be empty |
| `validation_errors.jsonl` | validation errors; expected to be empty |

## Boundary

The schema audit passes, but metric rerun is still gated because the labels are
Codex-filled and not human-confirmed. The next step is an explicit metric gate
decision, not an automatic p_obs / p_rel metric rerun.
