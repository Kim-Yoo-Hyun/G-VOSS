# H002 Ablation And Table Plan Update After Relative-Horizontal

Date: 2026-06-29 KST

## Status

```text
artifact_root = artifacts/compatibility_dataset_v3_ablation_and_table_plan_update_after_relative_horizontal_synthesis/
status = h002_compatibility_dataset_v3_ablation_and_table_plan_update_after_relative_horizontal_synthesis_ready
selected_path = freeze_relative_horizontal_aware_table_contract_select_route_coverage_sufficiency_review
validation_errors = 0
next_todo = compatibility_dataset_v3_route_coverage_sufficiency_review_after_relative_horizontal_table_plan
```

## Purpose

`relative_horizontal`이 multi-family synthesis에 추가된 뒤, H002의 candidate table,
ablation, control, promotion gate 계약을 다시 고정했다. 이 단계는 새 learned smoke를
실행하지 않고, 지금까지의 train-only mechanism evidence를 reviewer-facing table 구조로
정리한다.

## Updated Candidate Tables

| Table | Role | Rows |
| --- | --- | --- |
| `T1` | Predicate-Geometry Compatibility Mechanism | `relative_vertical`, `size_relative`, `relative_horizontal`, `support_contact` |
| `T2` | Relation-Aware Evidence Routing Taxonomy | clean, challenging, geometry-easy, observability-heavy, superordinate, frame-aware routes |
| `T3` | Diagnostic Boundary Cases | `close by`, `supported by`, `attached to`, `hanging on`, `connected to`, `in front of` |
| `T4` | Calibration and Claim Boundary | blocked claims, caveats, promotion gates, forbidden wording |

## Main Mechanism Rows

```text
relative_vertical = clean sign compatibility route
size_relative = clean size-comparison compatibility route
relative_horizontal = frame-aware directional compatibility route
support_contact = challenging compatibility route with caveat
```

## Added Horizontal Controls

`relative_horizontal` 때문에 table/control matrix에 다음 항목을 명시적으로 추가했다.

```text
wrong-frame x/y swap
selected-axis sign flip
subject/object endpoint swap
```

`in front of`는 현재 train-side source에서 관측되지 않으므로 diagnostic/deferred로
남긴다.

## Boundary

Allowed:

- train-only relation-aware `C_e = compatibility(T_e, G_e)` mechanism evidence
- family-specific route taxonomy
- clean route anchors plus support/contact caveat

Blocked:

- paper-level performance
- held-out/test reliability
- calibrated `p_rel` / `p_obs`
- complete horizontal ontology
- geometry-only framework
- support/contact fully solved
- all-family generality

## Next

다음 단계는 route coverage sufficiency review다. 즉, 현재 4개 main mechanism rows와
diagnostic/deferred routes가 H002 paper-framework로 충분한지, 아니면 relation family를
더 추가해야 하는지를 판단한다.

