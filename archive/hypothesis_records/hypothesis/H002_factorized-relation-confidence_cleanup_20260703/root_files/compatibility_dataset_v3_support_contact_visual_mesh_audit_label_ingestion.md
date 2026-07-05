# Compatibility Dataset V3 Support/Contact Visual/Mesh Audit Label Ingestion

## Result

```text
artifact_root = artifacts/compatibility_dataset_v3_support_contact_visual_mesh_audit_label_ingestion/
status = h002_compatibility_dataset_v3_support_contact_visual_mesh_audit_label_ingested_shortcut_risk_blocks_smoke
selected_path = ingest_proxy_labels_run_independence_diagnostics_block_smoke_if_shortcut
validation_errors = 0
next_todo = compatibility_dataset_v3_support_contact_visual_mesh_audit_path_decision_after_label_ingestion
```

This step ingested the 480 locked visible-packet proxy labels, joined the hidden
manifest only after label lock, and materialized `C_e`, `Q_e`, `p_obs`, and
`p_rel` target artifacts.

## Target Counts

```text
rows = 480
relation multiclass = accept 208 / reject 161 / abstain 111
p_rel binary rows = 369
p_rel binary target = positive 208 / negative 161
C_e binary rows = 369
C_e binary target = positive 208 / negative 161
p_obs target = positive 480 / negative 0
Q_e ordinal = sufficient 480
```

Predicate-level relation labels:

```text
lying on = accept 53 / reject 87 / abstain 54
standing on = accept 73 / reject 63 / abstain 20
supported by = accept 82 / reject 11 / abstain 37
```

## Boundary

```text
split = train full only
validation_usage = false
test_usage = false
h001_artifacts_modified = false
label_provenance = codex_visible_packet_proxy_labeler_user_requested
independent_human_audit = false
hidden_manifest_join_after_label_lock = true
hidden_manifest_used_for_label_fill = false
source_score_or_rank_used_for_label_fill = false
old_geometry_used_for_label_fill = false
runs_learned_smoke = false
paper_evidence_allowed = false
```

The current labels are user-requested Codex proxy labels. They are useful for
target plumbing and shortcut diagnosis, but they are not independent blind human
audit evidence.

## Shortcut Diagnosis

The binary class mass is sufficient, but the target is shortcut-prone. Learned
smoke is therefore blocked.

Key predictors that are too predictive:

```text
subject_object_class_pair -> p_rel majority accuracy 0.9973
object_label -> p_rel majority accuracy 0.8428
subject_label -> p_rel majority accuracy 0.8184
construction_bucket_hidden -> p_rel majority accuracy 0.9106
label_match_status_hidden -> p_rel majority accuracy 0.8726
geometry_status_hidden -> p_rel majority accuracy 0.7642
queue_kind_hidden -> p_rel majority accuracy 0.7642
```

Interpretation:

- The artifact now has enough accept/reject rows for `p_rel` and `C_e`.
- However, visible semantic identity, especially subject/object class-pair, can
  almost reconstruct the proxy labels.
- Hidden construction/source fields are not model inputs, but they confirm that
  sampling strata and old proxy states are highly correlated with the new target.
- `p_obs` and `Q_e` cannot be learned from this artifact because all 480 rows are
  sufficiently observable.

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

Do not run a learned model smoke on this target yet. The next step is a path
decision: either repair the target with stronger class-pair/semantic-stratum
controls, or freeze this support/contact visual/mesh audit as diagnostic-only.
