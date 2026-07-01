# Compatibility Dataset V3 Promotion Gap Plan After Paper Framework Readiness Review

## Status

```text
artifact_root = artifacts/compatibility_dataset_v3_promotion_gap_plan_after_paper_framework_readiness_review/
status = h002_compatibility_dataset_v3_promotion_gap_plan_after_paper_framework_readiness_review_ready
selected_path = promotion_gap_plan_ready_select_docker_heldout_protocol_plan
validation_errors = 0
next_todo = compatibility_dataset_v3_docker_heldout_protocol_plan_after_promotion_gap_plan
```

## Purpose

This stage converts the paper/framework readiness review into a concrete promotion plan.
It does not create a Docker experiment root, run a model, run validation/test evaluation, or promote any H002 result to a paper metric.

The goal is to define what must happen before H002 can move from hypothesis-stage route evidence to paper-level evidence.

## Main Verdict

H002 must be promoted in stages:

1. Docker and held-out split protocol.
2. Docker reproduction of route-specific rows and controls.
3. Held-out grouped evaluation.
4. Calibration/selective-decision evaluation only if `p_rel` / `p_obs` claims are kept.
5. Target-independence replication.
6. Paper claim wording lock.

The next step is a Docker + held-out protocol plan, not immediate experiment-root creation.

## Candidate Routes for Promotion

| Family | Predicates | Priority | Current role |
| --- | --- | --- | --- |
| `relative_vertical` | `higher than`, `lower than` | A minimal | clean compatibility mechanism |
| `size_relative` | `bigger than`, `smaller than` | A minimal | clean compatibility mechanism |
| `relative_horizontal` | `left`, `right`, `front`, `behind` | B reference-frame | frame-aware compatibility mechanism |
| `support_contact` | `standing on`, `lying on` | B challenging | challenging compatibility-route evidence |

For these routes, paper-level promotion requires Docker reproduction, held-out grouped evaluation,
target-independence audits, and claim wording lock. Calibration is required only if the paper claims
calibrated `p_rel` / `p_obs`, not merely route-specific `C_e`.

## Routes Not Promoted In Current Path

| Family | Relations | Reason |
| --- | --- | --- |
| `proximity` | `close by` | geometry-only control/generality route, not `T_e x G_e` interaction proof |
| `support_contact_superordinate` | `supported by` | broad superordinate support needs relabel/abstain decomposition |
| `attachment_like` | `attached to`, `hanging on`, `connected to` | current R7 artifact is shortcut-prone and needs evidence-first observability targets |
| future/separate | containment, `cover`, `leaning against`, identity/symmetry, semantic/structural | route taxonomy boundary only |

## Gate Summary

| Gate | Required before |
| --- | --- |
| Docker reproduction | any paper-level H002 metric |
| Held-out grouped evaluation | generalization/performance claim |
| Calibration/selective decision | calibrated `p_rel` / `p_obs` claim |
| Target-independence replication | reviewer defense against construction shortcut |
| Claim wording lock | manuscript/table drafting |

## Output Files

- `summary.json`
- `promotion_roadmap.csv`
- `route_gate_matrix.csv`
- `docker_protocol_contract.csv`
- `heldout_split_contract.csv`
- `calibration_selective_contract.csv`
- `target_independence_contract.csv`
- `claim_unlock_table.csv`
- `execution_order.csv`
- `next_contract.json`
- `report.md`
- `validation_errors.jsonl`
