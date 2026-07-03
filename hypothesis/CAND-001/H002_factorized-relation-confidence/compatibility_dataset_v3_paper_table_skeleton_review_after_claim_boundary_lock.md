# Compatibility Dataset V3 Paper Table Skeleton Review After Claim Boundary Lock

## Status

```text
artifact_root = artifacts/compatibility_dataset_v3_paper_table_skeleton_review_after_claim_boundary_lock/
status = h002_compatibility_dataset_v3_paper_table_skeleton_review_after_claim_boundary_lock_reviewed
selected_path = table_review_keep_as_bounded_mechanism_evidence_select_gap_plan
validation_errors = 0
next_todo = compatibility_dataset_v3_principled_design_gap_plan_after_table_review
```

## Core Judgment

H002의 구조는 원리적으로 자연스럽다. Relation reliability를 upstream confidence
하나로 보지 않고, semantic content `T_e`, source confidence `Z_e`, geometry evidence
`G_e`, compatibility `C_e`, observability/evidence quality `Q_e`로 분리하는 것은
현재 문제에서 필요한 분해다.

특히 `C_e = compatibility(T_e, G_e)`는 자연스럽다. Relation은 predicate 의미와
object-pair geometry가 서로 맞을 때만 신뢰 가능하므로, wrong-`T`와 shuffled-`G`
control은 이 원리를 직접 검증한다.

다만 현재 paper-table skeleton은 final paper result로 승격하기에는 아직 좁다.
Primary rows가 `relative_vertical`, `size_relative` 같은 signed comparison route에
집중되어 있어 reviewer가 “직접 geometry sign rule을 맞춘 것 아닌가?”라고 공격할 수 있다.

## Principle Review

| Principle | Verdict | Interpretation |
| --- | --- | --- |
| `T_e` and `Z_e` separation | natural and required | source confidence shortcut을 막기 위해 필요하다. |
| predicate-independent `G_e` | natural and required | geometry evidence가 predicate/source score를 미리 포함하면 compatibility 검증이 깨진다. |
| `C_e = compatibility(T_e, G_e)` | principled | relation reliability의 핵심 mechanism으로 유지 가능하다. |
| `Q_e` separated from truth | principled but not evaluated here | observability는 참/거짓이 아니라 판단 가능성을 담당해야 한다. |
| route-specific evidence | natural | relation family마다 필요한 evidence route가 다르다는 현재 결과와 맞다. |

## Paper Claim Review

| Item | Verdict | Action |
| --- | --- | --- |
| primary mechanism signal | strong | bounded mechanism evidence로 사용 가능 |
| primary relation scope | too clean for standalone top-tier claim | broad paper result로 승격 금지 |
| `relative_horizontal` | supporting with caveat | frame-aware evidence로만 보고 |
| `support_contact` | diagnostic not success | failure taxonomy / evidence-gap motivation으로 사용 |
| paper promotion | not yet | harder route 또는 source-deployable evidence gap plan 필요 |

## Decision

- 설계 방향은 유지한다.
- 현재 table은 bounded mechanism evidence로만 둔다.
- final paper result promotion은 하지 않는다.
- 다음 단계는 harder route 또는 source-deployable evidence를 통해 top-tier claim gap을 줄이는 계획을 세우는 것이다.

## Next

```text
compatibility_dataset_v3_principled_design_gap_plan_after_table_review
```
