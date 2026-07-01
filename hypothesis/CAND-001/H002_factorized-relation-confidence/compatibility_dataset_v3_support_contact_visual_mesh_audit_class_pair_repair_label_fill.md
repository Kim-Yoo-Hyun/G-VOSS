# Compatibility Dataset V3 Support/Contact Visual/Mesh Audit Class-Pair Repair Label Fill

## Result

```text
artifact_root = artifacts/compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_label_fill/
status = h002_compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_label_fill_completed
selected_path = codex_visible_packet_proxy_labels_filled_for_class_pair_repair_user_requested
validation_errors = 0
next_todo = compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_label_ingestion
```

## Boundary

```text
split = train full only
validation_usage = false
test_usage = false
h001_artifacts_modified = false
fills_labels = true
label_provenance = codex_visible_packet_proxy_labeler_user_requested
independent_human_audit = false
user_requested_codex_fill = true
used_visible_review_sheet = true
used_packet_paths = true
used_packet_asset_existence = true
used_hidden_manifest = false
used_source_score_or_rank = false
used_old_geometry_status_or_p_geom_valid = false
used_label_match_status = false
runs_learned_smoke = false
trains_new_model = false
paper_evidence_allowed = false
```

These are Codex proxy labels filled at the user's request. They are useful for
target repair diagnostics, but they are not independent blind human audit labels.

## Label Counts

```text
rows = 480
accept = 198
reject = 106
abstain = 176
geometry supports / contradicts / ambiguous = 198 / 106 / 176
observability sufficient = 480
```

By predicate:

```text
lying on = accept 47 / reject 45 / abstain 68
standing on = accept 52 / reject 46 / abstain 62
supported by = accept 99 / reject 15 / abstain 46
```

Uncertainty:

```text
other = 198
ontology_overlap = 187
ambiguous_pose = 95
```

## Generic Endpoint Risk

The repair packet visual sanity check already showed weak generic classes such as
`object -> box`. The filled labels confirm that generic endpoints are a major
source of abstention:

```text
generic_endpoint_rows = 100
generic_endpoint_labels = abstain 100
non_generic_labels = accept 198 / reject 106 / abstain 76
```

This is not necessarily a failure of the repair. It means the next ingestion
step must audit generic endpoint shortcuts separately from class-pair control.

## Artifacts

```text
filled_visible_review_sheet.csv
label_decisions.jsonl
label_counts.csv
summary.json
report.md
validation_errors.jsonl
```

## Next

```text
compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_label_ingestion
```

The next step should join hidden fields only after this label lock, materialize
`C_e`, `Q_e`, `p_obs`, and `p_rel` targets, and rerun shortcut diagnostics. No
learned smoke should run before that ingestion audit.
