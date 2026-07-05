# p_obs / p_rel Q_e Repair Plan

This folder stores the Q_e repair plan after the user-confirmed p_obs / p_rel
observability metric review.

## Current Run

```text
latest/
```

Status:

```text
status = h002_pobs_prel_qe_repair_plan_ready
validation_errors = 0
failure_cause = qe_feature_label_mismatch
ambiguous_rows_marked_sufficient = 126
missing_rows_marked_sufficient = 4
p_obs_AUROC = 0.500000
p_rel_AUROC = 0.774704
pobs_prel_solved_claim_allowed = false
next_todo = pobs_prel_qe_repair_materialization
```

## Decision

The next step is Q_e repair before any new p_obs / p_rel solved-claim attempt.
The repaired schema should add:

- `Q_e_asset_availability`
- `Q_e_visual_coverage`
- `Q_e_geometry_quality`
- `Q_e_ambiguity`
- `Q_e_state_v2`

## Files

| File | Role |
| --- | --- |
| `summary.json` | repair-plan decision and next TODO |
| `qe_schema_v2.csv` | repaired Q_e feature schema |
| `materialization_contract.csv` | train/eval/hidden artifact contract |
| `evaluation_protocol.csv` | p_obs-only, controls, and selective-decision rerun protocol |
| `pass_fail_gates.csv` | gates required before p_obs/p_rel claim promotion |
| `implementation_steps.csv` | next implementation steps |
| `paper_boundary.csv` | allowed/blocked paper claims |
| `report.md` | compact repair plan |
| `validation_errors.jsonl` | validation errors; expected to be empty |
