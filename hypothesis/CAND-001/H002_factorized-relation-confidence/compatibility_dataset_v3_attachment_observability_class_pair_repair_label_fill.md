# R7 Attachment Observability Class-Pair Repair Label Fill

## Result

```text
artifact_root = artifacts/compatibility_dataset_v3_attachment_observability_class_pair_repair_label_fill/
status = h002_compatibility_dataset_v3_attachment_observability_class_pair_repair_label_fill_completed
selected_path = codex_visible_packet_labels_filled_user_requested
validation_errors = 0
next_todo = compatibility_dataset_v3_attachment_observability_class_pair_repair_label_ingestion
```

## Scope

This step filled reviewer labels for the `480` train-only R7 class-pair repair
packets using only:

- `visible_review_sheet.csv`
- packet assets under `packets/<review_row_id>/`

It did not use hidden manifests, source confidence, rank, GT match status,
sampling roles, construction buckets, model predictions, validation data, or
test data.

## Label Counts

- total rows: `480`
- observability: `observable 455`, `uncertain 25`
- relation label: `accept 258`, `reject 90`, `abstain 132`
- evidence quality: `sufficient 458`, `partial 22`
- endpoint identity: `clear 476`, `ambiguous 4`

Predicate by relation label:

- `attached to|accept`: `172`
- `attached to|abstain`: `68`
- `attached to|reject`: `0`
- `hanging on|accept`: `86`
- `hanging on|reject`: `90`
- `hanging on|abstain`: `64`

## Artifacts

- `filled_visible_review_sheet.csv`
- `label_decisions.jsonl`
- `label_count_audit.csv`
- `validation_errors.jsonl`
- `summary.json`
- `report.md`

## Interpretation

The label fill produces a usable visible-label artifact for ingestion. It also
reveals an important risk: the `attached to` subset currently has no visible-only
reject labels under the conservative packet policy. This does not invalidate the
packet artifact, but it means the next ingestion and schema/shortcut audit must
check whether the usable binary target is balanced enough and whether predicate,
class-pair, or endpoint-category shortcuts dominate.

## Boundary

- train-only visible packet label fill
- no validation/test usage
- no H001 artifact modification
- labels filled
- no label ingestion
- no model-safe rows
- no learned smoke
- no paper-level evidence claim

## Next

Run `compatibility_dataset_v3_attachment_observability_class_pair_repair_label_ingestion`.
The ingestion step should derive multiclass, observable relation, and
observability targets, then the following schema/shortcut audit should decide
whether any learned smoke is allowed.
