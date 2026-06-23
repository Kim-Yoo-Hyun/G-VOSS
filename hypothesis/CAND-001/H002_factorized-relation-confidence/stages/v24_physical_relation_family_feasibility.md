# V24 Physical Relation-Family Feasibility

Date: 2026-06-23 KST

## Purpose

v23에서 proximity branch를 diagnostic/generality evidence로 고정한 뒤, 다음 primary
target route로 어떤 physical relation family를 사용할 수 있는지 train-only에서 점검했다.

비교 대상은 다음 세 family다.

```text
support_contact: standing on, lying on, supported by
attachment_deferred: attached to, hanging on, connected to
relative_vertical: higher than, lower than
```

## Artifact

```text
artifacts/train_rga_full/open3dsg_train_full/rga/
  reliability_target_v14_physical_relation_family_feasibility_scan/
    summary.json
    report.md
    family_inventory.csv
    predicate_inventory.csv
    queue_inventory.csv
    route_matrix.jsonl
    preview_candidates.jsonl
    validation_errors.jsonl
```

Validation errors: `0`

Validation/test usage: `false`

Posterior smoke: `blocked`

## Status

```text
status = h002_reliability_target_v14_physical_relation_family_feasibility_scan_ready_support_primary_attachment_schema_deferred
selected_route = support_contact_primary_anchor_with_relative_vertical_control_attachment_schema_probe
next_todo = reliability_target_v14_physical_relation_family_sampling_plan
```

## Family Results

| Family | Match rows | Checkable rows | HL rows | LH rows | Same-predicate HL/LH capacity | Verdict |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `support_contact` | 556,038 | 556,038 | 1,069 | 160,429 | 2,138 | primary anchor candidate |
| `attachment_deferred` | 556,038 | 0 | 0 | 0 | 0 | defer until witness schema |
| `relative_vertical` | 370,692 | 370,692 | 759 | 123,845 | 1,518 | control family |

## Interpretation

`support_contact` is the best immediate route. It has geometry coverage and both
HL/LH queue rows. However, it is not posterior-ready. The HL/LH queue is strongly
imbalanced and same-predicate bidirectional capacity is dominated by `lying on`.
The next sampling plan must therefore avoid the old exact endpoint-pair route and
must not treat queue bucket as the target label.

`relative_vertical` also has row mass and bidirectional capacity, but it is a
geometry-easy relation. It is useful as a control for whether H002 is merely
learning vertical order, not as the main novelty target.

`attachment_deferred` has many raw rows, but current geometry policy marks the
whole family as `unsupported_family`. It should not be sampled as a posterior
target before defining relation-specific witnesses for attachment, hanging, or
connection. Multi-view can remain audit evidence for this future schema.

## Key Risk

The main risk is not lack of rows. The main risk is target construction:

```text
HL/LH queue bucket != relation reliability label
```

HL/LH is a sampling/control axis derived from semantic rank and geometry status.
The reliability label still needs reviewer-visible evidence and a later
target-independence audit.

## Next

```text
reliability_target_v14_physical_relation_family_sampling_plan
```

Next sampling plan requirements:

1. Use train-only rows only.
2. Select `support_contact` as the primary anchor.
3. Keep `relative_vertical` as a control family.
4. Do not use `attachment_deferred` as posterior target until witness schema exists.
5. Balance by family/predicate/queue where possible, but do not let queue bucket become the label.
6. Avoid the old exact endpoint-pair rank/predicate construction.
7. Keep posterior smoke blocked until the sampled target passes label ingestion and target-independence audit.
