# Compatibility Dataset V3 Paper Framework Readiness Review After Route Specific Probes

## Status

```text
artifact_root = artifacts/compatibility_dataset_v3_paper_framework_readiness_review_after_route_specific_probes/
status = h002_compatibility_dataset_v3_paper_framework_readiness_review_after_route_specific_probes_ready
selected_path = readiness_review_completed_select_promotion_gap_plan
validation_errors = 0
next_todo = compatibility_dataset_v3_promotion_gap_plan_after_paper_framework_readiness_review
```

## Purpose

This stage reviews the current H002 route-specific probes from a paper/framework readiness perspective.
It does not run a new model or smoke test. The goal is to separate:

- train-only mechanism evidence that can become candidate main table rows,
- diagnostic/control/boundary evidence,
- claims that remain blocked,
- gates required before paper-level promotion.

## Input Artifacts

- `artifacts/compatibility_dataset_v3_scope_synthesis_after_attachment_observability_diagnostic_freeze/`
- `artifacts/compatibility_dataset_v3_schema_freeze_and_promotion_protocol_after_route_coverage_review/`
- `artifacts/compatibility_dataset_v3_route_specific_target_manifest_consistency_audit_after_plan/`

## Main Verdict

H002 is framework-ready at hypothesis stage, but not paper-result ready.

The current evidence is sufficient to define a relation-aware evidence-routing framework and candidate
main mechanism table, but paper-level claims still require Docker reproduction, held-out grouped
evaluation, calibration/selective-decision evaluation, and final claim wording.

## Candidate Main Mechanism Rows

| Family | Predicates | Current role |
| --- | --- | --- |
| `relative_vertical` | `higher than`, `lower than` | clean `T_e x G_e` mechanism anchor |
| `size_relative` | `bigger than`, `smaller than` | second clean mechanism anchor with calibration caveat |
| `relative_horizontal` | `left`, `right`, `front`, `behind` | frame-aware mechanism anchor with reference-frame caveat |
| `support_contact` | `standing on`, `lying on` | challenging compatibility-route evidence with caveat |

These rows are candidate main table rows only. They are not paper-level results yet.

## Diagnostic / Boundary Rows

| Family | Relations | Role |
| --- | --- | --- |
| `proximity` | `close by` | geometry-only route control/generality evidence |
| `support_contact_superordinate` | `supported by` | superordinate decomposition / relabel / abstain diagnostic |
| `attachment_like` | `attached to`, `hanging on`, `connected to` | observability-heavy diagnostic/future boundary |
| future/separate routes | containment, `cover`, `leaning against`, identity/symmetry, semantic/structural | deferred taxonomy boundary |

## Blocked Claims

- paper-level reliability improvement
- calibrated `p_rel` / `p_obs`
- all-family generality
- current R7 attachment-like learned reliability
- support/contact fully solved
- complete 3DSSG relation coverage

## Required Promotion Gates

1. Docker reproduction.
2. Held-out grouped evaluation by scan and endpoint pair.
3. Calibration and selective-decision evaluation for `p_rel` and `p_obs`.
4. Target-independence replication for any promoted route.
5. Failure taxonomy and final claim wording lock.

## Output Files

- `summary.json`
- `readiness_table.csv`
- `candidate_main_table_rows.csv`
- `diagnostic_boundary_table.csv`
- `promotion_gap_table.csv`
- `blocked_claims.csv`
- `reviewer_risk_register.csv`
- `next_contract.json`
- `report.md`
- `validation_errors.jsonl`
