# p_obs / p_rel Observability Ingestion

This folder stores model-safe and hidden views built from the filled p_obs /
p_rel observability labels.

## Current Run

```text
latest/
```

Status:

```text
status = h002_pobs_prel_observability_label_ingestion_ready
validation_errors = 0
rows = 265
model_safe_qe_view_rows = 265
model_safe_prel_view_rows = 265
hidden_observability_label_rows = 265
observable_clear = 135
ambiguous_evidence = 126
unobservable_missing_evidence = 4
obs_1 = 135
obs_0 = 130
human_confirmed = false
metric_rerun_allowed_now = false
next_todo = pobs_prel_observability_schema_audit
```

## Files

| File | Role |
| --- | --- |
| `model_safe_qe_view.jsonl` | Q_e-only model-safe view for observability/evidence quality |
| `model_safe_prel_view.jsonl` | p_rel candidate view with T_e/G_e/Q_e/Z_e fields |
| `hidden_observability_labels.jsonl` | hidden labels and provenance, excluded from model-safe views |
| `label_balance.csv` | label and decision counts |
| `ingestion_manifest.json` | row counts, boundary, and output manifest |
| `validation_errors.jsonl` | validation errors; expected to be empty |

## Boundary

The model-safe views exclude labels and target-derived construction fields.
Hidden labels remain Codex-filled, not human-confirmed.
