# Compatibility Dataset V3 Support/Contact Visual/Mesh Audit Source Inventory

## Result

```text
artifact_root = artifacts/compatibility_dataset_v3_support_contact_visual_mesh_audit_source_inventory/
status = h002_compatibility_dataset_v3_support_contact_visual_mesh_audit_source_inventory_ready_for_packet_materialization
selected_path = source_inventory_ready_packet_materialization_required
validation_errors = 0
next_todo = compatibility_dataset_v3_support_contact_visual_mesh_audit_packet_materialization
```

## Purpose

This step inventories actual train-only source rows for the fixed support/contact visual/mesh audit
target. It writes candidate rows, visible label-sheet templates, hidden manifests, and packet source
manifests.

It does not render packet assets, fill labels, train a model, run learned smoke, or use
validation/test rows.

## Selected Source Rows

```text
selected_rows = 480
label_sheet_rows = 480
hidden_manifest_rows = 480
all_required_sources_exist = true
```

Predicate distribution:

```text
lying on = 194
standing on = 156
supported by = 130
```

Sampling strata:

```text
lying_on_clear_accept = 60
lying_on_hard_reject_standing_like = 40
lying_on_abstain_or_ambiguous = 20
standing_on_clear_accept = 60
standing_on_hard_reject_lying_like = 40
standing_on_abstain_or_ambiguous = 20
supported_by_clear_accept = 60
supported_by_hard_reject_no_support = 40
supported_by_abstain_or_ontology_overlap = 20
cross_predicate_control = 50
coverage_stress_control = 35
hard_surface_cap_control = 35
```

Hidden source-balance fields:

```text
queue_kind = HL 112 / LH 368
label_match_status = exact_match 180 / family_match 85 / no_gt_for_pair 149 / pair_has_other_predicate 66
hard_surface_rows = 90
hard_surface_share = 0.1875
```

These hidden fields are used for target-source balance and later shortcut audit only. They are not
visible to the reviewer during label creation.

## Cap Gates

All source inventory caps passed:

```text
selected_rows = 480 / 480
max_scan_rows = 4 <= 24
max_subject_object_class_pair_rows = 13 <= 48
max_directed_pair_rows = 2 <= 2
hard_surface_rows = 90 <= 288
hidden_HL_rows = 112 >= 60
```

The low max-scan and max-class-pair counts are important because previous H002 targets repeatedly
failed by becoming predicate/class/endpoint shortcuts.

## Visible / Hidden Split

Visible label sheet:

```text
artifacts/compatibility_dataset_v3_support_contact_visual_mesh_audit_source_inventory/label_sheet_template.csv
```

Visible fields contain:

- `review_id`
- `scan_id_visible`
- `subject_label`, `predicate_label`, `object_label`
- packet paths currently marked as `PACKET_PENDING/...`
- visible review fields left blank

Hidden manifest:

```text
artifacts/compatibility_dataset_v3_support_contact_visual_mesh_audit_source_inventory/hidden_manifest.jsonl
```

Hidden fields include:

- source score / rank / source id
- queue kind
- old geometry status and `p_geom_valid`
- label match status
- construction bucket and hidden stratum
- object ids and exact prediction ids

## Packet Source Boundary

Raw packet sources exist for all 480 rows:

```text
aligned_ply
mesh_obj
mesh_seg
semseg
sequence_zip
```

The visible sheet is not label-ready yet because packet images/sheets are still pending. The next
step must materialize visual/mesh packet assets from:

```text
artifacts/compatibility_dataset_v3_support_contact_visual_mesh_audit_source_inventory/packet_source_manifest.jsonl
```

## Outputs

- `artifacts/compatibility_dataset_v3_support_contact_visual_mesh_audit_source_inventory/summary.json`
- `artifacts/compatibility_dataset_v3_support_contact_visual_mesh_audit_source_inventory/source_pool_summary.json`
- `artifacts/compatibility_dataset_v3_support_contact_visual_mesh_audit_source_inventory/selected_candidate_inventory.jsonl`
- `artifacts/compatibility_dataset_v3_support_contact_visual_mesh_audit_source_inventory/label_sheet_template.csv`
- `artifacts/compatibility_dataset_v3_support_contact_visual_mesh_audit_source_inventory/hidden_manifest.jsonl`
- `artifacts/compatibility_dataset_v3_support_contact_visual_mesh_audit_source_inventory/packet_source_manifest.jsonl`
- `artifacts/compatibility_dataset_v3_support_contact_visual_mesh_audit_source_inventory/source_balance_report.csv`
- `artifacts/compatibility_dataset_v3_support_contact_visual_mesh_audit_source_inventory/cap_diagnostics.csv`
- `artifacts/compatibility_dataset_v3_support_contact_visual_mesh_audit_source_inventory/report.md`

## Next

```text
compatibility_dataset_v3_support_contact_visual_mesh_audit_packet_materialization
```

The next step should render or assemble the point/mesh/multiview packets referenced by the
`PACKET_PENDING/...` placeholders, then recheck packet readiness before label fill.
