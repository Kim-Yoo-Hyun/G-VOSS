# V27 Physical Relation-Family Label Fill

Date: 2026-06-23 KST

## Purpose

v26에서 만든 240-row physical relation-family label-ready sheet를 reviewer-visible
fields만 사용해 proxy label로 채웠다. 이 단계는 hidden audit manifest를 읽지 않고,
posterior smoke도 실행하지 않는다.

## Artifact

```text
artifacts/train_rga_full/open3dsg_train_full/rga/
  reliability_target_v14_physical_relation_family_label_fill/
    summary.json
    report.md
    filled_label_sheet_v14.tsv
    label_decisions_v14.jsonl
    validation_errors.jsonl
```

Validation errors: `0`

Hidden audit manifest read: `false`

Validation/test usage: `false`

Posterior smoke: `blocked`

## Status

```text
status = h002_reliability_target_v14_physical_relation_family_label_filled_codex_proxy_visible_only
rows = 240
accept_reliable = 48
reject_unreliable = 152
abstain_uncertain = 40
binary_usable_rows = 200
geometry_support_supports = 48
geometry_support_contradicts = 152
geometry_support_ambiguous = 40
validation_errors = 0
next_todo = reliability_target_v14_physical_relation_family_label_ingestion
```

## Family Breakdown

| Family | Accept | Reject | Abstain | Note |
| --- | ---: | ---: | ---: | --- |
| `support/contact relation` | 16 | 114 | 30 | conservative support/contact geometry policy |
| `relative vertical relation` | 32 | 38 | 10 | control family with clearer vertical evidence |

## Key Risk

The binary target has `200` usable rows, but the positive class has only `48`
rows. This is two rows below the previous post-label minimum-per-class gate of
`50`. Therefore this label fill unlocks ingestion and target-independence audit
only; it does not unlock posterior smoke.

The next stage must check whether the `48/152` binary class split is sufficient
under the v14 target-independence audit and whether shortcut controls remain
valid after hidden audit manifest join.

## Boundary

This is hypothesis-stage proxy target material.

It is not:

- paper-level human-confirmed benchmark evidence
- posterior performance evidence
- validation/test evidence
- a change to H001 or paper artifacts

## Next

```text
reliability_target_v14_physical_relation_family_label_ingestion
```

The next step should join the filled visible labels with the hidden audit
manifest, derive multiclass/binary/geometry-support/usefulness target artifacts,
and preserve hidden fields as audit/control-only metadata.
