# Compatibility Dataset V3 Support/Contact Visual/Mesh Audit Class-Pair Repair Packet Materialization

## Result

```text
artifact_root = artifacts/compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_packet_materialization/
status = h002_compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_packet_materialization_ready_for_label_fill
selected_path = class_pair_repair_packet_assets_materialized_visible_sheet_ready_for_label_fill
validation_errors = 0
next_todo = compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_label_fill
```

## Boundary

```text
split = train full only
validation_usage = false
test_usage = false
h001_artifacts_modified = false
fills_labels = false
runs_learned_smoke = false
trains_new_model = false
paper_evidence_allowed = false
repair_proxy_is_sampling_only = true
final_target_requires_visible_packet_label_fill = true
```

This step materializes reviewer-facing packet assets for the 480 class-pair
controlled repair candidates. It does not create final labels and does not run a
model.

## Packet Counts

```text
packet_rows = 480
label_ready_rows = 480
non_ready_rows = 0
visible_leakage_hits = 0

lying on ready = 160
standing on ready = 160
supported by ready = 160

accept_like ready = 240
reject_like ready = 240
```

Evidence assets:

```text
subject_image_rows = 480
object_image_rows = 480
pair_crop_rows = 480
mesh_render_rows = 480
multiview_sheet_rows = 480
total_subject_images = 1852
total_object_images = 1888
```

## Visible Label Sheet

```text
artifacts/compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_packet_materialization/visible_review_sheet_with_packets.csv
```

The visible sheet hides source confidence, source rank, old geometry status,
old `p_geom_valid`, label-match status, `repair_proxy_kind`, and construction
fields.

## Caveats

- `repair_proxy_kind` remains hidden and sampling-only. It is not a target.
- `mesh_contact_render.png` is still a reviewer-facing mesh/geometry availability
  card rather than a full 3D contact-surface render.
- Some repair candidates include generic labels such as `object`, which may
  remain visually weak even after class-pair control. The next label-fill and
  post-lock audit should track generic-class cases separately.

## Artifacts

```text
visible_review_sheet_with_packets.csv
packet_manifest.jsonl
materialized_hidden_manifest.jsonl
label_ready_manifest.jsonl
non_ready_packet_rows.jsonl
visible_leakage_hits.jsonl
summary.json
report.md
validation_errors.jsonl
packets/*/{point_pair_crop.png,mesh_contact_render.png,multiview_contact_sheet.jpg,packet.md}
```

## Next

```text
compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_label_fill
```

The next step should fill labels from the visible packet sheet only, then lock
the labels before joining hidden fields for target materialization and shortcut
audit.
