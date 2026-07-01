# Compatibility Dataset V3 Ablation And Table Plan Update After Size-Relative Synthesis

Created: 2026-06-29 KST

## Purpose

`size_relative`가 multi-family synthesis에 추가된 뒤, H002의 candidate table,
ablation, control, promotion gate 계약을 갱신했다. 이 단계는 새 learned smoke를
실행하지 않고, paper/framework로 이어질 수 있는 표 구조와 claim boundary를 정리한다.

## Command

```bash
python hypothesis/CAND-001/H002_factorized-relation-confidence/tools/compatibility_dataset_v3_ablation_and_table_plan_update_after_size_relative_synthesis.py
```

## Artifact

```text
artifact_root = artifacts/compatibility_dataset_v3_ablation_and_table_plan_update_after_size_relative_synthesis/
status = h002_compatibility_dataset_v3_ablation_and_table_plan_update_after_size_relative_synthesis_ready
selected_path = freeze_size_relative_aware_table_contract_select_route_coverage_sufficiency_review
validation_errors = 0
next_todo = compatibility_dataset_v3_route_coverage_sufficiency_review_after_size_relative_table_plan
```

Generated files:

```text
summary.json
main_table_plan.csv
route_taxonomy_table.csv
ablation_matrix.csv
control_matrix.csv
promotion_gates.csv
forbidden_wording.csv
reviewer_response_plan.csv
table_spec.md
report.md
validation_errors.jsonl
```

## Updated Candidate Tables

| Table | Role | Rows |
| --- | --- | --- |
| `T1` | Predicate-Geometry Compatibility Mechanism | `relative_vertical`, `size_relative`, `support_contact` |
| `T2` | Relation-Aware Evidence Routing Taxonomy | main, diagnostic, future, deferred route families |
| `T3` | Diagnostic Boundary Cases | `close by`, `supported by`, attachment-like, horizontal relations |
| `T4` | Calibration and Claim Boundary | blocked claims, caveats, promotion gates |

## Main Mechanism Rows

```text
relative_vertical primary signal = 1.0000
size_relative primary signal = 0.9999
support_contact primary signal = 0.6994
```

Interpretation:

- `relative_vertical` and `size_relative` are clean mechanism anchors.
- `support_contact` remains challenging compatibility-route evidence with caveat.
- `close by` stays geometry-easy diagnostic/control.
- `attachment_like`, `supported by`, and `relative_horizontal` remain non-main or deferred.

## Boundary

This artifact still blocks:

- paper-level performance
- held-out/test relation reliability
- calibrated `p_rel` / `p_obs`
- all relation-family generality
- solved support/contact wording
- geometry-only framework wording

## Next

```text
compatibility_dataset_v3_route_coverage_sufficiency_review_after_size_relative_table_plan
```

The next step should decide whether the current family coverage is sufficient for the
H002 paper-framework path or whether another relation family must be added before
promotion planning.
