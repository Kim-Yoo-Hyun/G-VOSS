# V25 Physical Relation-Family Sampling Plan

Date: 2026-06-23 KST

## Purpose

v24 feasibility scan 이후 실제 candidate mining에 들어가기 전, train-only sampling quota,
cap policy, label surface, independence gate를 고정했다. 이 단계는 row를 아직 선택하지
않고, 다음 mining step이 어떤 원칙으로 240-row sheet를 만들지 정의한다.

## Artifact

```text
artifacts/train_rga_full/open3dsg_train_full/rga/
  reliability_target_v14_physical_relation_family_sampling_plan/
    summary.json
    report.md
    cell_quotas.csv
    excluded_cells.csv
    target_schema.json
    mining_policy.json
    label_surface_contract.json
    independence_gate.json
    validation_errors.jsonl
```

Validation errors: `0`

Validation/test usage: `false`

Posterior smoke: `blocked`

## Status

```text
status = h002_reliability_target_v14_physical_relation_family_sampling_plan_ready_for_candidate_mining
selected_route = support_contact_primary_anchor_relative_vertical_control
target_queue_rows = 240
primary_anchor_rows = 160
control_rows = 80
next_todo = reliability_target_v14_physical_relation_family_candidate_mining
```

## Quota

| Cell | Family | Predicate | Queue | Rows | Available | Role |
| --- | --- | --- | --- | ---: | ---: | --- |
| `S1_support_lie_hl` | `support_contact` | `lying on` | `HL` | 68 | 1,052 | primary anchor |
| `S2_support_lie_lh` | `support_contact` | `lying on` | `LH` | 68 | 59,600 | primary anchor |
| `S3_support_stand_hl` | `support_contact` | `standing on` | `HL` | 12 | 17 | limited primary diversity |
| `S4_support_stand_lh` | `support_contact` | `standing on` | `LH` | 12 | 50,228 | limited primary diversity |
| `V1_vertical_lower_hl` | `relative_vertical` | `lower than` | `HL` | 40 | 758 | control family |
| `V2_vertical_lower_lh` | `relative_vertical` | `lower than` | `LH` | 40 | 61,544 | control family |

## Excluded From Current Primary Target

- `supported by`: LH-only under current queue and outside the narrow current H002 core.
- `higher than`: HL capacity is one row, so same-predicate controlled sampling is unstable.
- `attachment_deferred`: current geometry policy marks the family as `unsupported_family`; witness schema is required first.

## Key Guardrail

```text
HL/LH queue bucket != relation reliability label
```

HL/LH is used only for sampling semantic-geometry disagreement cases. The reliability
target must be assigned later from reviewer-visible evidence, and posterior inputs
must not include queue kind, rank band, machine hint, label-match status, or hidden
audit fields.

## Mining Policy

The next candidate mining step must:

1. use train-only queues only;
2. fill the six quota cells above;
3. exclude duplicate prediction ids and avoid duplicate directed endpoint pairs;
4. cap scan/subgraph/object-label concentration;
5. avoid hard room surface endpoint shortcuts, especially for `support_contact`;
6. keep multi-view as audit/confirmation evidence only;
7. produce a reviewer-visible label surface with hidden audit fields separated.

## Next

```text
reliability_target_v14_physical_relation_family_candidate_mining
```
