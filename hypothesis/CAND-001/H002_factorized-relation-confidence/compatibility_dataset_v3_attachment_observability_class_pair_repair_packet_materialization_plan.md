# R7 Attachment Observability Class-Pair Repair Packet Materialization Plan

## Result

```text
artifact_root = artifacts/compatibility_dataset_v3_attachment_observability_class_pair_repair_packet_materialization_plan/
status = h002_compatibility_dataset_v3_attachment_observability_class_pair_repair_packet_materialization_plan_ready
selected_path = class_pair_repair_packet_materialization_plan_ready
validation_errors = 0
next_todo = compatibility_dataset_v3_attachment_observability_class_pair_repair_packet_materialization
```

## Scope

This step plans packet/material evidence generation for the `480` train-only R7
class-pair repair candidates selected in the previous step.

- `attached to`: `240` rows
- `hanging on`: `240` rows
- `connected to`: `0` primary rows, still diagnostic
- proxy role quota per predicate: accept `80`, reject `120`, uncertain `40`
- unique scans: `340`
- exact predicate/class-pair groups: `160`

## Evidence Readiness

All selected rows are ready for packet generation under the current audit
definition.

- scan, mesh, semseg, and sequence evidence: `480/480`
- subject/object multi-view evidence: `480/480`
- shared view evidence: `480/480`
- shared frame evidence: `64/480`
- evidence tier: `T1_pair_multiview_ready = 480`
- limited/not-ready rows: `0`

`shared_frame` is not required for this materialization gate because the
available `multi_view` packet names expose shared view ranks for all rows. The
actual packet generation step should still preserve frame-level provenance when
it exists.

## Artifacts

- `summary.json`
- `report.md`
- `packet_materialization_contract.json`
- `visible_label_schema.json`
- `packet_plan_rows.jsonl`
- `hidden_asset_manifest_plan.jsonl`
- `evidence_inventory_by_candidate.jsonl`
- `evidence_tier_audit.csv`
- `quota_audit.csv`
- `materialization_steps.csv`
- `validation_errors.jsonl`

## Field Boundary

The visible plan rows contain only reviewer-facing relation text, evidence
readiness summaries, and blank review fields. They exclude scan id, instance id,
source/rank fields, proxy role, GT match status, construction buckets, and file
paths.

The hidden manifest preserves those fields for packet generation and later audit
only. Multi-view and mesh are still audit/evidence sources, not model input.

## Boundary

- train-only packet materialization plan
- no validation/test usage
- no H001 artifact modification
- no packet assets created yet
- no label fill or label ingestion
- no model-safe rows
- no learned smoke
- no paper-level evidence claim

## Next

Run `compatibility_dataset_v3_attachment_observability_class_pair_repair_packet_materialization`
to create the actual review packets and label-ready surface, then run readiness
and schema/shortcut checks before any label ingestion or learned smoke.
