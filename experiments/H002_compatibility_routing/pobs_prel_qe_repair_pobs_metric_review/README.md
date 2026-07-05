# p_obs Metric Review After Q_e Repair

## Role

This folder owns the claim-boundary review for the repaired `Q_e v2`
`p_obs`-only diagnostic metric.

It decides whether the p_obs-only diagnostic pass should trigger a full
p_obs/p_rel selective-decision rerun or be kept as optional diagnostic evidence.

## Current Status

```text
status = h002_pobs_prel_qe_repair_pobs_metric_review_ready
validation_errors = 0
p_obs_AUROC = 1.000000
p_obs_ECE_10 = 0.049266
abstain_recall = 1.000000
direct_Qe_state_AUROC = 1.000000
proxy_shortcut_risk = high
pobs_required_for_core_claim = false
pobs_main_claim_allowed = false
pobs_optional_framework_component = true
full_selective_decision_rerun_now = false
selected_path = demote_pobs_to_optional_diagnostic_keep_core_claim_on_Ce_source_reranking
next_todo = h002_core_claim_without_pobs_boundary_update
```

## Interpretation

The repaired `Q_e v2` representation fixes the previous sufficient-state
mismatch and passes the p_obs-only diagnostic smoke test. However, direct
`Q_e state_code` also reaches AUROC `1.0`, the eval `Q_e v2` labels are
audit-proxy diagnostic material, and the missing-evidence slice has only `4`
rows.

Therefore `p_obs` is not a main solved claim for the current H002 paper path.
It remains an optional framework component for future observability-heavy routes.

## Outputs

```text
latest/summary.json
latest/review_decision.csv
latest/claim_boundary.csv
latest/proxy_shortcut_audit.csv
latest/next_steps.csv
latest/report.md
latest/validation_errors.jsonl
```
