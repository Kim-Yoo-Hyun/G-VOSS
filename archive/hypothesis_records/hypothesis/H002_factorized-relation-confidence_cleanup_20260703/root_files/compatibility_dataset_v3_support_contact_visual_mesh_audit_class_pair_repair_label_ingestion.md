# Compatibility Dataset V3 Support/Contact Visual/Mesh Audit Class-Pair Repair Label Ingestion

## Result

```text
artifact_root = artifacts/compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_label_ingestion/
status = h002_compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_label_ingested_shortcut_risk_blocks_smoke
selected_path = ingest_class_pair_repair_labels_run_shortcut_diagnostics
validation_errors = 0
next_todo = compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_path_decision_after_label_ingestion
```

## Target Counts

```text
rows = 480
relation multiclass = accept 198 / reject 106 / abstain 176
p_rel binary rows = 304
p_rel positive/negative = 198 / 106
C_e binary rows = 304
C_e positive/negative = 198 / 106
p_obs = all 480 positive
Q_e = all 480 sufficient
```

By predicate:

```text
lying on = accept 47 / reject 45 / abstain 68
standing on = accept 52 / reject 46 / abstain 62
supported by = accept 99 / reject 15 / abstain 46
```

## Boundary

```text
split = train full only
validation_usage = false
test_usage = false
h001_artifacts_modified = false
hidden_manifest_join_after_label_lock = true
hidden_manifest_used_for_label_fill = false
source_score_or_rank_used_for_label_fill = false
old_geometry_used_for_label_fill = false
label_provenance = codex_visible_packet_proxy_labeler_user_requested
independent_human_audit = false
runs_learned_smoke = false
trains_new_model = false
paper_evidence_allowed = false
```

## Shortcut Diagnosis

The repair improved row balance but did not yet make the target smoke-ready.

```text
learned_smoke_allowed = false
p_rel class_mass_pass = true
C_e class_mass_pass = true
p_obs class_mass_pass = false
Q_e class_mass_pass = false
```

High-risk predictors for `p_rel` / `C_e`:

```text
predicate_x_subject_object_class_pair_visible majority accuracy = 1.0000
predicate_class_pair_hidden majority accuracy = 1.0000
hidden_stratum_hidden majority accuracy = 1.0000
directed_pair_key_hidden majority accuracy = 1.0000
subgraph_id_hidden majority accuracy = 0.9507
scan_id_hidden majority accuracy = 0.8816
subject_label majority accuracy = 0.7007
object_label majority accuracy = 0.6875
```

Generic endpoint risk is mainly a multiclass/abstain issue:

```text
generic_endpoint_visible = true rows 100
generic endpoint rows are all abstain in the visible-label fill
generic_endpoint_visible relation_multiclass majority accuracy = 0.6208
```

Interpretation:

- The repair fixed the extreme lack of binary row mass under support/contact
  class-pair repair.
- However, exact `predicate + subject/object class-pair` still reconstructs the
  proxy target because the current visible-label policy is strongly class-driven.
- Generic endpoints are excluded from binary `p_rel`/`C_e` as abstain, but they
  remain a strong multiclass abstain shortcut.
- `p_obs` and `Q_e` remain degenerate because every packet is observable.

## Artifacts

```text
target_rows.jsonl
p_rel_binary_target.jsonl
c_e_binary_target.jsonl
p_obs_target.jsonl
q_e_target.jsonl
relation_multiclass_target.jsonl
target_counts.csv
target_viability.csv
shortcut_diagnostics.csv
risk_register.csv
model_input_boundary.json
summary.json
report.md
validation_errors.jsonl
```

## Decision

Do not run learned smoke yet. The next step is a path decision:

```text
compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_path_decision_after_label_ingestion
```

The decision should choose between a stricter within-`predicate_x_class_pair`
human/visual label pass, a generic-endpoint filtered target, or freezing this
support/contact repair as diagnostic evidence.
