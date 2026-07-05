# p_obs / p_rel Q_e Repair Materialization

## Role

This folder owns the repaired `Q_e v2` model-safe train/eval views and hidden
observability labels for the H002 p_obs-only repair path.

## Current Status

```text
status = h002_pobs_prel_qe_repair_materialization_ready
validation_errors = 0
blocked_field_hits = 0
train_qe_v2_rows = 14604
eval_qe_v2_rows = 265
train_label_counts = observable_clear:4868,ambiguous_evidence:4868,unobservable_missing_evidence:4868
eval_label_counts = observable_clear:135,ambiguous_evidence:126,unobservable_missing_evidence:4
paper_level_pobs_prel_solved_claim_allowed = false
next_todo = pobs_prel_qe_repair_schema_audit
```

## Outputs

```text
latest/materialization_manifest.json
latest/model_safe_qe_v2_train.jsonl
latest/model_safe_prel_v2_train.jsonl
latest/model_safe_qe_v2_eval.jsonl
latest/model_safe_prel_v2_eval.jsonl
latest/hidden_observability_v2_labels.jsonl
latest/qe_v2_feature_alignment.csv
latest/label_balance.csv
latest/blocked_field_hits.jsonl
latest/validation_errors.jsonl
```

## Boundary

The eval `Q_e v2` view uses audit-proxy diagnostics, not independently authored
visual/mesh labels. It is valid for schema audit and p_obs-only diagnostic
smoke testing, but it does not permit a paper-level calibrated p_obs/p_rel
solved claim.
