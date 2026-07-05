# Attachment Independent Positive Anchor Label Ingestion V1

Created: 2026-06-26 KST

## Purpose

Ingest the `560` locked visible-packet labels from
`attachment_independent_positive_anchor_label_fill_v1` with hidden/control provenance from
`attachment_independent_positive_anchor_packet_materialization_v1`.

This stage does not relabel rows. Hidden query/proxy/rank/source/GT fields are joined only after
label lock and remain diagnostic control fields.

## Runner

```bash
python hypothesis/CAND-001/H002_factorized-relation-confidence/tools/attachment_independent_positive_anchor_label_ingestion_v1.py
```

## Outputs

```text
artifact_root = artifacts/attachment_independent_positive_anchor_label_ingestion_v1/
ingested_rows = artifacts/attachment_independent_positive_anchor_label_ingestion_v1/ingested_rows.jsonl
factor_views = artifacts/attachment_independent_positive_anchor_label_ingestion_v1/factor_views.jsonl
primary_binary_target = artifacts/attachment_independent_positive_anchor_label_ingestion_v1/primary_binary_target.jsonl
compatibility_binary_target = artifacts/attachment_independent_positive_anchor_label_ingestion_v1/compatibility_binary_target.jsonl
p_rel_target = artifacts/attachment_independent_positive_anchor_label_ingestion_v1/p_rel_target.jsonl
p_obs_target = artifacts/attachment_independent_positive_anchor_label_ingestion_v1/p_obs_target.jsonl
shortcut_probe_risks = artifacts/attachment_independent_positive_anchor_label_ingestion_v1/shortcut_probe_risks.json
summary = artifacts/attachment_independent_positive_anchor_label_ingestion_v1/summary.json
```

## Result

```text
status = h002_attachment_independent_positive_anchor_label_ingested_class_mass_pass_with_shortcut_risk
rows = 560
validation_errors = 0
next_todo = attachment_independent_positive_anchor_target_independence_audit_v1
```

Target counts:

```text
multiclass_rows = 560
primary_binary_rows = 306
compatibility_binary_rows = 306
p_rel_rows = 306
p_obs_rows = 560
p_obs_primary_rows = 480
geometry_support_rows = 306
evidence_quality_rows = 560
connected_diagnostic_rows = 80
abstain_rows = 254
```

Primary target:

```text
primary_positive_rows = 60
primary_negative_rows = 246
class_mass_pass = true
```

Review label distribution:

```text
accept_reliable = 60
reject_unreliable = 246
abstain_uncertain = 254

p_obs_target:
  observable = 306
  abstain_or_unobservable = 254
```

## Shortcut / Control Signals

```text
quick_probe_risk_flags = 98
model_shortcut_probe_risk_flags = 75
construction_proxy_probe_risk_flags = 42
label_derived_probe_risk_flags = 23
```

Mixed primary binary groups:

```text
same_query_mixed_primary_binary_groups = 5
same_proxy_role_mixed_primary_binary_groups = 3
same_cell_mixed_primary_binary_groups = 5
same_rank_band_mixed_primary_binary_groups = 5
same_predicate_mixed_primary_binary_groups = 2
same_visible_pair_mixed_primary_binary_groups = 2
same_mixed_endpoint_family_rank_coverage_mixed_primary_binary_groups = 5
same_selection_route_mixed_primary_binary_groups = 5
```

Interpretation:

- class mass is now sufficient for a diagnostic posterior smoke in terms of row count;
- the target is still shortcut-risky because endpoint labels, visible-pair identity, query/cell
  construction, and high-cardinality scan/subgraph fields can predict labels too well;
- the existence of mixed groups means the target is not trivially identical to query/cell/proxy
  construction, but this must be checked more formally before training.

## Boundary

```text
split = train_only
validation_usage = false
test_usage = false
fills_new_labels = false
reads_hidden_manifest_after_label_lock = true
hidden_manifest_used_for_label_fill = false
hidden_fields_as_model_input = false
source_score_or_rank_as_model_input = false
construction_proxy_as_model_input = false
uses_p_geom_valid = false
trains_new_posterior = false
posterior_smoke_allowed = false
paper_evidence_allowed = false
h001_artifacts_modified = false
numeric_g_e_materialized = false
```

## Next

```text
attachment_independent_positive_anchor_target_independence_audit_v1
```

The next step should decide whether controlled slices remain usable after removing obvious
predicate/endpoint/construction shortcuts. Posterior smoke is still blocked.

