# V26 Physical Relation-Family Candidate Mining

Date: 2026-06-23 KST

## Purpose

v25 sampling plan의 240-row quota를 실제 train-only queue에 적용해 reviewer-visible
candidate sheet와 hidden audit manifest를 생성했다. 이 단계는 label을 채우지 않는다.

## Artifact

```text
artifacts/train_rga_full/open3dsg_train_full/rga/
  reliability_target_v14_physical_relation_family_candidate_mining/
    summary.json
    report.md
    label_ready_sheet_v14.tsv
    hidden_audit_manifest_v14.jsonl
    selected_candidates_internal.jsonl
    cell_summary.csv
    quota_adjustments.jsonl
    cap_summary.json
    visible_leakage_hits.jsonl
    validation_errors.jsonl
    review_cards_v14/
```

Validation errors: `0`

Visible leakage hits: `0`

Validation/test usage: `false`

Posterior smoke: `blocked`

## Status

```text
status = h002_reliability_target_v14_physical_relation_family_candidate_mining_ready_for_label_fill
selected_rows = 240
support_contact_rows = 160
relative_vertical_rows = 80
unique_scans = 202
unique_subgraphs = 222
unique_directed_pairs = 240
raw_feature_joined_rows = 240
next_todo = reliability_target_v14_physical_relation_family_label_fill
```

## Effective Quota

| Cell | Effective rows | Selected rows | Note |
| --- | ---: | ---: | --- |
| `S1_support_lie_hl` | 80 | 80 | received fallback rows |
| `S2_support_lie_lh` | 68 | 68 | original quota |
| `S3_support_stand_hl` | 0 | 0 | all candidate rows violated hard endpoint filter |
| `S4_support_stand_lh` | 12 | 12 | limited diversity |
| `V1_vertical_lower_hl` | 40 | 40 | control family |
| `V2_vertical_lower_lh` | 40 | 40 | control family |

## Quota Adjustment

`standing on` HL had 17 raw rows, but all had hard room-surface subjects such as
`floor` or `wall`. Keeping them would reintroduce the exact shortcut this stage is
trying to avoid. Therefore the 12 planned rows from `S3_support_stand_hl` were moved
to `S1_support_lie_hl`.

```text
S3_support_stand_hl -> S1_support_lie_hl: 12 rows
```

This keeps the total `support_contact` mass at 160 rows and avoids hard-room-surface
endpoint dominance.

## Guardrail

The visible label sheet and review cards do not expose:

- queue kind
- source rank
- machine hint
- label-match status
- raw scores
- RGA bucket

These fields are retained only in `hidden_audit_manifest_v14.jsonl`.

## Next

```text
reliability_target_v14_physical_relation_family_label_fill
```

Next step fills the reviewer-visible fields only. Posterior remains blocked until
label ingestion and target-independence audit pass.
