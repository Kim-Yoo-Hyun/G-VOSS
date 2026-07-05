# Compatibility Dataset V3 Support/Contact Visual-Mesh Source Inventory

## Status

```text
status = h002_compatibility_dataset_v3_support_contact_visual_mesh_source_inventory_ready_for_mesh_pose_contact_probe
selected_path = mesh_pose_contact_feature_probe_before_materialization
next = compatibility_dataset_v3_support_contact_mesh_pose_contact_feature_probe_plan
validation_errors = 0
```

## Purpose

이 단계는 `support_contact` train 후보가 실제로 3RScan mesh, aligned instance PLY,
`semseg.v2.json`, `sequence.zip`, 기존 packet-rendering asset과 join 가능한지 확인하는
source inventory다. 아직 feature extraction, candidate materialization, learned smoke는 하지
않는다.

## Inputs

```text
plan = artifacts/compatibility_dataset_v3_support_contact_visual_mesh_evidence_plan/
probe_runner = artifacts/compatibility_dataset_v3_support_contact_evidence_probe_runner/
rga_queue = artifacts/train_rga_full/open3dsg_train_full/rga/
3RScan = local_dataset/3RScan/scans/
visual_audit = artifacts/visual_annotation_audit/
attachment_packet_template = artifacts/attachment_independent_positive_anchor_packet_materialization_v1/
```

## Outputs

```text
artifact_root = artifacts/compatibility_dataset_v3_support_contact_visual_mesh_source_inventory/
summary.json
path_decision.json
scan_asset_inventory.csv
support_contact_candidate_source_join_preview.jsonl
mesh_pose_contact_feature_feasibility.csv
multiview_packet_feasibility.csv
shortcut_and_scope_risk.csv
sequence_zip_sample.csv
report.md
validation_errors.jsonl
```

## Join Coverage

```text
support_rows = 161498
distinct_scans = 1157
distinct_directed_pairs = 75763
distinct_visible_pairs = 4109

scan_asset_complete_rate = 1.000000
semseg_both_objects_present_rate = 1.000000
mesh_contact_surface_possible_rate = 1.000000
sequence_multiview_possible_rate = 1.000000
```

Source snapshot:

```text
candidate_scans = 1157
scan_dirs_present = 1157
semseg_present = 1157
mesh_obj_present = 1157
mesh_seg_present = 1157
aligned_ply_present = 1157
aligned_ply_has_object_id = 1157
sequence_zip_present = 1157
sampled_sequence_zips = 24
sampled_sequence_color_depth_pose_ok = 24
```

Interpretation:

Support/contact candidates can be joined to scan-level and object-level sources. In every checked
candidate row, both subject/object IDs exist in `semseg.v2.json`, both have OBB and dominant normal
metadata, aligned PLY has `objectId`, mesh files exist, and sequence zips exist. This is enough to
authorize a mesh/pose/contact feature feasibility probe.

## Predicate And Queue Distribution

```text
lying on = 60652
standing on = 50245
supported by = 50601

HL = 1069
LH = 160429
geometry satisfied = 160429
geometry unsatisfied = 1069
```

The predicate distribution is balanced enough for source inventory, but HL/LH is not. This means
direct reliability smoke remains unsafe. The next step should derive predicate-independent
`G_e` candidates first, then later build a shortcut-controlled target.

## Feature Feasibility

Available at 100% row coverage:

- instance OBB pose and extent;
- dominant normal;
- aligned PLY object points;
- mesh contact surface source files;
- sequence zip for future multi-view / `Q_e`.

Planned primary `G_e` candidates:

- subject/object pose and orientation from OBB axes;
- uprightness / horizontalness / major-axis alignment;
- local dominant-normal alignment;
- support surface direction;
- object-point crop and contact candidate bands;
- mesh contact gap / support area proxy.

Multi-view remains audit / `Q_e` first. It is not allowed as immediate model input.

## Risks

High risks blocking materialization or learned smoke:

```text
hard_surface_dominance = 0.7023059109091134
HL/LH queue imbalance = HL 1069 / LH 160429
same exact-pair clean capacity = 4
```

These risks do not block source-level feature probing. They do block immediate support/contact
candidate materialization and learned smoke.

## Decision

```text
mesh_pose_contact_feature_probe_allowed = true
candidate_materialization_allowed = false
learned_smoke_allowed = false
numeric_only_smoke_allowed = false
multiview_model_input_allowed_now = false
multiview_qe_audit_first = true
```

The correct next step is to define a mesh/pose/contact feature probe plan. That probe should
derive features and check whether they vary in a way that can support `C_e`, while still avoiding
source score, construction proxy, and human-label leakage.

## Boundary

- Train-only source inventory.
- No full `match_rows.jsonl` scan.
- No candidate materialization.
- No learned smoke.
- No validation/test usage.
- No paper-level evidence promotion.
- No H001 artifact modification.
