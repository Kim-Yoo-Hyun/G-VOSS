# V30 Physical Relation-Family Path Decision

Date: 2026-06-23 KST

## Purpose

v29 target-independence audit 이후 v14 physical relation-family branch를 어떻게
처리할지 결정했다. 이 단계는 posterior smoke를 실행하지 않고, v14를 primary
posterior target으로 유지할지 또는 repair route로 넘길지만 판단한다.

## Artifact

```text
artifacts/train_rga_full/open3dsg_train_full/rga/
  reliability_target_v14_physical_relation_family_path_decision_after_audit/
    summary.json
    report.md
    option_matrix.jsonl
    selected_plan.json
    validation_errors.jsonl
```

Validation errors: `0`

Validation/test usage: `false`

Posterior smoke: `blocked`

## Status

```text
status = h002_reliability_target_v14_physical_relation_family_path_decision_select_v15_repair_plan
selected_path = freeze_v14_diagnostic_select_v15_witness_matched_physical_relation_repair_plan
relation_binary_counts = 0:152, 1:48
relation_class_mass_pass = false
relation_strict_clear_slice_count = 0
relation_diagnostic_clear_slice_count = 0
posterior_allowed = false
validation_errors = 0
next_todo = reliability_target_v15_physical_relation_family_repair_plan
```

## Decision

Current v14 is frozen as diagnostic target-construction evidence, not discarded.

Selected next route:

```text
v15 witness-matched physical relation-family repair plan
```

The repair plan should increase reliable positive mass and reduce shortcut risk
without simply relaxing labels.

## Why Not Just Add Two Positives

The target is not blocked only by `48 < 50`. A balanced `48/48` full slice exists,
but it still has shortcut risk from:

- scan/object identity
- visible and hidden object-pair identity
- quota cell
- rank band
- machine hint
- direct witness-summary text

Adding two positives would pass the numeric threshold while leaving the core
independence failure intact.

## Selected Repair Requirements

- Increase primary relation positive mass without simply relaxing labels.
- Sample within matched predicate, source queue, rank band, geometry status, and witness buckets.
- Reduce or redesign visible witness text so it is not a direct label template.
- Separate `support_contact` primary target from `relative_vertical` control target.
- Require mixed accept/reject groups within matched witness strata before label fill.
- Keep hidden audit fields and target construction keys out of model inputs.
- Keep multi-view as audit evidence only.

## Boundary

This is a train-only path decision.

It is not:

- paper-level benchmark evidence
- posterior performance evidence
- validation/test evidence
- a change to H001 or paper artifacts

## Next

```text
reliability_target_v15_physical_relation_family_repair_plan
```
