# R7 Attachment Observability Class-Pair Repair Packet Materialization

## Result

```text
artifact_root = artifacts/compatibility_dataset_v3_attachment_observability_class_pair_repair_packet_materialization/
status = h002_compatibility_dataset_v3_attachment_observability_class_pair_repair_packet_materialization_ready_for_label_fill
selected_path = attachment_observability_packets_ready_for_label_fill
validation_errors = 0
next_todo = compatibility_dataset_v3_attachment_observability_class_pair_repair_label_fill
```

## Scope

This step materialized reviewer-facing packet assets for the `480` train-only R7
class-pair repair candidates selected for `attached to` and `hanging on`.

- `attached to`: `240` packets ready
- `hanging on`: `240` packets ready
- `connected to`: `0` primary packets, still diagnostic
- `accept_proxy_supported_candidate`: `160` packets ready
- `reject_proxy_contradicted_candidate`: `240` packets ready
- `uncertain_proxy`: `80` packets ready

## Packet Outputs

Each packet directory contains:

- `packet.md`
- `pair_crop.png`
- `observability_card.png`
- `multiview_sheet.jpg`
- copied subject/object review thumbnails under `images/`

The root artifact contains:

- `visible_review_sheet.csv`
- `packet_manifest.jsonl`
- `materialized_hidden_manifest.jsonl`
- `label_ready_manifest.jsonl`
- `non_ready_packet_rows.jsonl`
- `visible_leakage_hits.jsonl`
- `validation_errors.jsonl`
- `summary.json`
- `report.md`

## Counts

- packet rows: `480`
- label-ready rows: `480`
- non-ready rows: `0`
- subject image rows: `480`
- object image rows: `480`
- pair crop rows: `480`
- observability card rows: `480`
- multiview sheet rows: `480`
- total subject thumbnails copied: `2772`
- total object thumbnails copied: `2804`
- visible leakage hits: `0`

## Field Boundary

The visible review sheet keeps only reviewer-facing relation text, readiness
summary fields, `packet_status`, and blank review fields. It does not include
scan ids, instance ids, source/rank fields, proxy roles, GT status, construction
buckets, or filesystem paths.

Packet paths, copied-image provenance, source asset paths, and sampling proxy
fields are stored only in `materialized_hidden_manifest.jsonl`. Multi-view and
mesh remain audit evidence, not model input.

## Boundary

- train-only packet materialization
- no validation/test usage
- no H001 artifact modification
- packet assets were created
- no label fill
- no label ingestion
- no model-safe rows
- no learned smoke
- no paper-level evidence claim

## Next

Run `compatibility_dataset_v3_attachment_observability_class_pair_repair_label_fill`.
The label fill should use the visible sheet and packets only, then label
ingestion and schema/shortcut audit must run before any learned smoke.
