# Compatibility Dataset V3 Support/Contact Visual/Mesh Audit Path Decision After Label Ingestion

## Result

```text
artifact_root = artifacts/compatibility_dataset_v3_support_contact_visual_mesh_audit_path_decision_after_label_ingestion/
status = h002_compatibility_dataset_v3_support_contact_visual_mesh_audit_path_decision_class_pair_repair_ready_for_packet_materialization
selected_path = class_pair_controlled_repair_first
validation_errors = 0
next_todo = compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_packet_materialization
```

## Train Split Boundary

Yes. This repair decision and candidate mining are still train-only.

```text
source = artifacts/train_rga_full/open3dsg_train_full/rga/
used_files = train_hl_queue.jsonl, train_lh_queue.jsonl
validation_usage = false
test_usage = false
h001_artifacts_modified = false
runs_learned_smoke = false
trains_new_model = false
```

The current 480 visible-packet proxy labels came from a train-full source subset.
The repair candidates were mined again from the same train-full support/contact
queues, not from validation or test.

## Why Repair Is Needed

The ingested 480 proxy labels have enough binary row mass, but almost no exact
class-pair-controlled mixed target:

```text
axis = class_pair
usable_rows = 369
mixed_groups = 1
balanced_rows = 2

axis = predicate_x_class_pair
usable_rows = 369
mixed_groups = 0
balanced_rows = 0
```

So the old 480-row target cannot show that `G_e` or `C_e` is doing meaningful
work after controlling visible semantic identity.

## Full Train Capacity

Full train support/contact candidate scan found enough repair capacity:

```text
source_rows_after_proxy_filter = 27201
class_pair mixed_groups = 313
class_pair balanced_raw_rows = 13020
predicate_x_class_pair mixed_groups = 71
predicate_x_class_pair balanced_raw_rows = 960
```

The selected repair path is therefore not diagnostic-only freeze. It is:

```text
class_pair_controlled_repair_first
```

## Selected Repair Candidate Set

The runner selected a new 480-row repair candidate set under exact
`predicate + subject/object class-pair` control.

```text
selected_rows = 480
lying on = 160
standing on = 160
supported by = 160
accept_like = 240
reject_like = 240
predicate_x_proxy_kind = 80 rows for each predicate/proxy-kind cell
predicate_class_pair_groups = 68
max_predicate_class_pair_rows = 31
max_scan_rows = 11
max_directed_pair_rows = 1
hard_surface_rows = 252
required_source_file_errors = 0
```

Important boundary:

```text
repair_proxy_kind is sampling-only.
It is not a final target.
Final target requires visible packet materialization and label fill.
```

## Artifacts

```text
label_sheet_template.csv
hidden_manifest.jsonl
packet_source_manifest.jsonl
repair_candidate_manifest.jsonl
current_control_capacity.csv
full_train_capacity.csv
balance.csv
cap_gates.csv
summary.json
report.md
validation_errors.jsonl
```

## Next

```text
compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_packet_materialization
```

The next step should materialize visible packets for these 480 repair candidates,
then fill labels from visible packet fields only. Only after that label lock
should hidden fields be joined again for target-independence and shortcut audit.
