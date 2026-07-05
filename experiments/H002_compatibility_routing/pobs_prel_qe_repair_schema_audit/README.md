# p_obs / p_rel Q_e Repair Schema Audit

## Role

This folder owns the leakage/schema audit for repaired `Q_e v2` materialization.
It verifies model-safe / hidden separation before any p_obs-only diagnostic
metric rerun.

## Current Status

```text
status = h002_pobs_prel_qe_repair_schema_audit_ready
validation_errors = 0
blocked_field_hits = 0
train_qe_rows = 14604
train_prel_rows = 14604
train_hidden_rows = 14604
eval_qe_rows = 265
eval_prel_rows = 265
eval_hidden_rows = 265
schema_separation = true
row_alignment = true
qe_required_blocks = true
train_label_balance = true
eval_ambiguous_missing_not_sufficient = true
pobs_only_diagnostic_metric_allowed = true
full_selective_decision_rerun_allowed = false
paper_level_pobs_prel_solved_claim_allowed = false
next_todo = pobs_prel_qe_repair_pobs_only_metric
```

## Outputs

```text
latest/summary.json
latest/schema_separation_audit.csv
latest/row_alignment.csv
latest/qe_v2_block_audit.csv
latest/qe_v2_feature_label_alignment.csv
latest/label_balance.csv
latest/blocked_field_hits.jsonl
latest/validation_errors.jsonl
```

## Boundary

The audit permits a p_obs-only diagnostic metric smoke test. It does not permit
full selective-decision rerun or paper-level calibrated p_obs/p_rel solved
wording.
