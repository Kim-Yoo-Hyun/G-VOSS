# Compatibility Dataset V3 Support/Contact Visual/Mesh Audit Packet Materialization

## Result

```text
artifact_root = artifacts/compatibility_dataset_v3_support_contact_visual_mesh_audit_packet_materialization/
status = h002_compatibility_dataset_v3_support_contact_visual_mesh_audit_packet_materialization_ready_for_label_fill
selected_path = packet_assets_materialized_visible_sheet_ready_for_label_fill
validation_errors = 0
next_todo = compatibility_dataset_v3_support_contact_visual_mesh_audit_label_fill
```

## Purpose

This step materializes reviewer-facing packet assets for the 480 support/contact audit candidates.
It replaces the previous `PACKET_PENDING/...` placeholders with concrete packet paths.

It does not fill labels, train a model, run learned smoke, use validation/test rows, or modify H001
artifacts.

## Packet Counts

```text
packet_rows = 480
ready = 480
non_ready = 0
label_ready_rows = 480
visible_leakage_hits = 0
validation_errors = 0
```

Predicate readiness:

```text
lying on | ready = 194
standing on | ready = 156
supported by | ready = 130
```

Evidence readiness:

```text
subject_image_rows = 480
object_image_rows = 480
pair_crop_rows = 480
mesh_render_rows = 480
multiview_sheet_rows = 480
total_subject_images = 1884
total_object_images = 1884
```

## Generated Packet Assets

For each row, the packet now includes:

- `point_pair_crop.png`: side-by-side subject/object visual crop.
- `multiview_contact_sheet.jpg`: multi-view crop sheet for subject and object.
- `mesh_contact_render.png`: reviewer-facing mesh/geometry availability card.
- `packet.md`: packet index that links the visible evidence.

Important limitation:

```text
mesh_contact_render.png is an availability/evidence card, not a full 3D mesh contact render.
```

It confirms that aligned point labels, scene mesh, mesh segmentation, object semantic segmentation,
and RGB-D/multiview sources exist. It does not visualize the full 3D mesh contact surface yet.

## Visible Sheet

Label-ready visible sheet:

```text
artifacts/compatibility_dataset_v3_support_contact_visual_mesh_audit_packet_materialization/visible_review_sheet_with_packets.csv
```

The review fields remain blank:

```text
review_relation_reliability
review_geometry_support
review_observability
review_counter_relation
review_uncertainty_reason
review_notes
```

Hidden metadata remains separated in:

```text
artifacts/compatibility_dataset_v3_support_contact_visual_mesh_audit_packet_materialization/materialized_hidden_manifest.jsonl
```

The visible sheet and packet markdown do not expose source score/rank, queue kind, old
`geometry_status`, old `p_geom_valid`, label-match status, construction bucket, hidden stratum,
prediction id, subject id, or object id.

## Outputs

- `artifacts/compatibility_dataset_v3_support_contact_visual_mesh_audit_packet_materialization/summary.json`
- `artifacts/compatibility_dataset_v3_support_contact_visual_mesh_audit_packet_materialization/visible_review_sheet_with_packets.csv`
- `artifacts/compatibility_dataset_v3_support_contact_visual_mesh_audit_packet_materialization/packet_manifest.jsonl`
- `artifacts/compatibility_dataset_v3_support_contact_visual_mesh_audit_packet_materialization/materialized_hidden_manifest.jsonl`
- `artifacts/compatibility_dataset_v3_support_contact_visual_mesh_audit_packet_materialization/label_ready_manifest.jsonl`
- `artifacts/compatibility_dataset_v3_support_contact_visual_mesh_audit_packet_materialization/non_ready_packet_rows.jsonl`
- `artifacts/compatibility_dataset_v3_support_contact_visual_mesh_audit_packet_materialization/visible_leakage_hits.jsonl`
- `artifacts/compatibility_dataset_v3_support_contact_visual_mesh_audit_packet_materialization/report.md`
- `artifacts/compatibility_dataset_v3_support_contact_visual_mesh_audit_packet_materialization/packets/`

## Verification

```text
python -m py_compile tools/compatibility_dataset_v3_support_contact_visual_mesh_audit_packet_materialization.py
validation_errors.jsonl rows = 0
visible_leakage_hits.jsonl rows = 0
non_ready_packet_rows.jsonl rows = 0
```

Sample packet images were visually checked:

```text
packets/scvm_audit_0001_008560ab98/point_pair_crop.png
packets/scvm_audit_0001_008560ab98/mesh_contact_render.png
packets/scvm_audit_0001_008560ab98/multiview_contact_sheet.jpg
```

## Next

```text
compatibility_dataset_v3_support_contact_visual_mesh_audit_label_fill
```

The next step can fill the visible review fields using only
`visible_review_sheet_with_packets.csv` and the packet assets. Hidden metadata should be joined only
after labels are locked.
