# R7 Attachment Observability Class-Pair Repair Path Decision

## Result

```text
artifact_root = artifacts/compatibility_dataset_v3_attachment_observability_class_pair_repair_path_decision_after_schema_shortcut_audit/
status = h002_compatibility_dataset_v3_attachment_observability_class_pair_repair_path_decision_freeze_diagnostic
selected_path = freeze_r7_class_pair_repair_as_diagnostic_select_scope_synthesis
validation_errors = 0
next_todo = compatibility_dataset_v3_scope_synthesis_after_attachment_observability_diagnostic_freeze
```

## Decision

Current R7 `attached to` / `hanging on` class-pair repair artifact is frozen as
diagnostic evidence. It must not be used for learned smoke, calibrated `p_rel`,
calibrated `p_obs`, or paper-level reliability evidence.

The blocker is not row count. The current artifact has enough rows to look
tempting:

- combined observable `p_rel`: `258/90`
- `hanging on` observable `p_rel`: `86/90`

But the target is not independent:

- combined `p_rel`: `predicate_subject_object_class_pair` majority accuracy `1.0`
- `hanging on` `p_rel`: `subject_label` / `subject_object_class_pair` majority accuracy `1.0`
- `attached to` `p_rel`: single-class `172/0`
- `p_obs`: negative-sparse `455/25`
- exact predicate-class-pair mixed capacity after visible labels: `0`

## Rejected Routes

| Route | Decision | Reason |
| --- | --- | --- |
| learned smoke on combined `p_rel` | reject | `predicate_subject_object_class_pair` solves the target |
| learned smoke on `hanging on` only | reject | balanced counts exist, but class labels solve the target |
| repeat same proxy-based class-pair mining | reject | the first full-train repair attempt collapsed after visible labels |
| mine truly mixed same-class-pair visual rows | defer | requires a new evidence-first audit protocol |
| reframe R7 as `p_obs` / abstention | defer | current packet set is T1-ready and `p_obs` is sparse |

## Selected Path

```text
freeze_r7_class_pair_repair_as_diagnostic_select_scope_synthesis
```

R7 remains in the H002 route taxonomy as an observability-heavy relation family,
but the current artifact is diagnostic-only. A future R7 revisit must use a new
target construction, not the same source-proxy/class-pair repair recipe.

## Boundary

- train-only path decision
- no validation/test usage
- no H001 artifact modification
- no new labels
- no row materialization
- no learned smoke
- no paper-level evidence claim

## Next

Run `compatibility_dataset_v3_scope_synthesis_after_attachment_observability_diagnostic_freeze`.
