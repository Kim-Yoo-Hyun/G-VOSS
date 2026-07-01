# R7 Attachment Observability Materialization

Date: 2026-06-30

## Status

```text
artifact_root = artifacts/compatibility_dataset_v3_attachment_observability_materialization/
status = h002_compatibility_dataset_v3_attachment_observability_materialization_ready_for_schema_shortcut_audit
selected_path = materialized_r7_gq_separated_source_target_hidden_control_views
validation_errors = 0
next_todo = compatibility_dataset_v3_attachment_observability_schema_shortcut_audit
```

## Purpose

This step materializes the R7 attachment-observability route without running any
learned model. The goal is to separate model-safe evidence from hidden source,
target, review, and construction fields before testing whether the route is
identifiable without shortcut leakage.

## Inputs

- `artifacts/compatibility_dataset_v3_attachment_observability_materialization_plan/summary.json`
- `artifacts/compatibility_dataset_v3_attachment_observability_source_inventory/packet_reuse_inventory_rows.jsonl`
- `artifacts/attachment_independent_positive_anchor_label_ingestion_v1/ingested_rows.jsonl`
- `artifacts/attachment_independent_positive_anchor_packet_materialization_v1/label_ready_manifest.jsonl`
- `artifacts/attachment_independent_positive_anchor_candidate_mining_v1/candidate_rows_internal.jsonl`
- `local_dataset/3RScan/scans/*/semseg.v2.json`

## Outputs

- `source_rows.jsonl`: train-only rows with factor blocks.
- `model_safe_view.jsonl`: allowed model input view.
- `target_manifest.jsonl`: `p_obs`, observable `p_rel`, and reliability labels.
- `hidden_manifest.jsonl`: ids, packet paths, source score/rank, review labels,
  and construction fields.
- `control_manifest.jsonl`: planned controls for the next schema audit.
- `schema_audit_inputs.json`: next-step audit contract.
- `model_safe_feature_manifest.csv`: allowed feature list.
- `target_distribution.csv`: target count summary.
- `summary.json`, `validation_errors.jsonl`, `report.md`

## Row Counts

| Predicate | Role | Rows |
| --- | --- | ---: |
| `attached to` | primary observability then reliability | 238 |
| `hanging on` | primary observability then reliability | 242 |
| `connected to` | diagnostic observability then topology | 80 |
| total |  | 560 |

Additional counts:

- Geometry available rows: `560/560`
- Model-safe rows: `560`
- Target manifest rows: `560`
- Hidden manifest rows: `560`
- Control manifest rows: `7`
- Strong same-frame visual rows: `116`
- Same-view weak rows: `444`

## Target Snapshot

| Target | Distribution |
| --- | --- |
| `p_obs_target` | `1:306`, `0:254` |
| `p_rel_observable_target` | `1:60`, `0:246`, `None:254` |

Interpretation:

- `p_obs` is the first decision head: can this relation candidate be judged from
  the available evidence?
- `p_rel` is only defined for observable primary `attached to` / `hanging on`
  rows.
- `connected to` has no primary `p_rel` target because explicit topology or
  functional-connection evidence is absent in the current artifact.

## Model-Safe Boundary

Allowed model-safe blocks:

- `T_e`: predicate and object semantic content.
- `G_e_attachment`: derived OBB/geometry evidence from scan semseg, not old
  construction proxy or old `p_geom_valid`.
- `Q_e_observability`: mesh/multiview/contact-sheet/same-view availability and
  scan evidence readiness.

Hidden-only fields:

- candidate id, query id, scan id, subject/object ids
- packet paths and packet request ids
- source score, source rank, rank band
- review labels, review notes, reviewer status
- target labels and construction/audit fields

## Control Manifest

The next audit must check at least:

- wrong-`T_e` predicate swap
- shuffled-`G_e` within predicate
- shuffled-`Q_e` within predicate
- no-view / low-evidence mask
- class-pair-only probe
- hidden query/rank/packet probe
- `connected to` diagnostic probe

## Boundary

- Train-only hypothesis artifact.
- No validation/test split was used.
- No learned smoke was executed.
- No paper-level reliability claim is allowed from this step.
- H001 artifacts were not modified.

## Caveat

Observable `p_rel` remains positive sparse: `60` accept vs `246` reject. This is
acceptable for materialization, but it is not sufficient for a learned
reliability claim until the schema shortcut audit shows that target labels are
not recoverable from construction shortcuts, class-pair artifacts, source/rank
leakage, or packet/review provenance.
