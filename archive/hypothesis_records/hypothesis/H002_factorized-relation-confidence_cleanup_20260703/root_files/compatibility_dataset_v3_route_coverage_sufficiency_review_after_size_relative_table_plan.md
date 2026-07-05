# Compatibility Dataset V3 Route Coverage Sufficiency Review After Size-Relative Table Plan

Created: 2026-06-29 KST

## Purpose

`size_relative`까지 포함한 table plan 이후, 현재 relation-family coverage가 H002 promotion
planning으로 넘어가기에 충분한지 검토했다. 사용자 판단은 “다른 relation family도 더 추가해서
다 진행해보고 판단하자”였으므로, 이 단계에서는 promotion이 아니라 additional family sweep을
선택했다.

## Command

```bash
python hypothesis/CAND-001/H002_factorized-relation-confidence/tools/compatibility_dataset_v3_route_coverage_sufficiency_review_after_size_relative_table_plan.py
```

## Artifact

```text
artifact_root = artifacts/compatibility_dataset_v3_route_coverage_sufficiency_review_after_size_relative_table_plan/
status = h002_compatibility_dataset_v3_route_coverage_sufficiency_review_after_size_relative_table_plan_ready
selected_path = coverage_not_sufficient_add_relation_family_sweep_before_promotion
validation_errors = 0
next_todo = compatibility_dataset_v3_additional_relation_family_sweep_plan_after_coverage_review
```

Generated files:

```text
summary.json
coverage_decision.csv
expansion_queue.csv
sweep_scope.csv
predicate_gap_snapshot.csv
reviewer_risks.csv
next_plan_contract.json
report.md
validation_errors.jsonl
```

## Decision

Current coverage is not sufficient for promotion planning.

Current main mechanism rows are useful:

```text
relative_vertical
size_relative
support_contact
```

However, this is not enough to stop exploration because high-mass or semantically
distinct families remain untested or deferred.

## Expansion Queue

| Rank | Family | First Step | Expected Role |
| ---: | --- | --- | --- |
| 1 | `relative_horizontal` | reference-frame protocol and schema probe | high-value reference-frame probe |
| 2 | `containment_in` | containment geometry schema and capacity scan | possible main if identifiable, otherwise diagnostic |
| 3 | `attachment_deferred` | visual/mesh/Q_e protocol | observability-heavy future/diagnostic |
| 4 | `part_structural` | diagnostic schema boundary scan | likely diagnostic or out-of-scope |
| 5 | `identity_symmetry` | out-of-scope rationale and count audit | exclude from physical compatibility claim |

## Boundary

- Do not promote current three-family table as final paper result.
- Do not train one all-family model before per-family schemas are defined.
- Do not use validation/test for target construction.
- Do not modify H001 artifacts.

## Next

```text
compatibility_dataset_v3_additional_relation_family_sweep_plan_after_coverage_review
```
