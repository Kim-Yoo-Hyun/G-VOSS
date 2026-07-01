# R7 Attachment Observability Class-Pair Repair Label Ingestion

## Result

```text
artifact_root = artifacts/compatibility_dataset_v3_attachment_observability_class_pair_repair_label_ingestion/
status = h002_compatibility_dataset_v3_attachment_observability_class_pair_repair_label_ingested_ready_for_schema_shortcut_audit
selected_path = ingest_visible_packet_labels_run_schema_shortcut_audit_next
validation_errors = 0
next_todo = compatibility_dataset_v3_attachment_observability_class_pair_repair_schema_shortcut_audit
```

## Target Artifacts

- `ingested_target_rows.jsonl`: `480`
- `multiclass_rows.jsonl`: `480`
- `observability_binary_rows.jsonl`: `480`
- `observable_relation_binary_rows.jsonl`: `348`
- `target_count_audit.csv`
- `target_viability.csv`
- `shortcut_preview.csv`
- `risk_register.csv`
- `model_input_boundary.json`
- `validation_errors.jsonl`
- `summary.json`
- `report.md`

## Target Summary

- multiclass relation: `accept 258`, `reject 90`, `abstain 132`
- observability: `observable 455`, `uncertain 25`
- `p_obs`: positive `455`, negative `25`
- observable `p_rel`: rows `348`, accept `258`, reject `90`

Predicate-specific observable `p_rel`:

- `attached to`: rows `172`, accept `172`, reject `0`
- `hanging on`: rows `176`, accept `86`, reject `90`

## Viability

- `relation_multiclass_accept_reject_abstain`: diagnostic-ready, needs shortcut audit
- `p_obs_observable_binary`: negative-sparse, diagnostic only
- `p_rel_observable_accept_reject`: ready for schema/shortcut audit
- `p_rel_observable_attached to`: single-class, diagnostic only
- `p_rel_observable_hanging on`: ready for schema/shortcut audit

## Risk Notes

The ingestion confirms that combined observable `p_rel` has enough class mass to
audit, but it is not yet a learned-smoke target. The quick preview flags shortcut
risk from visible class-pair fields, decision reason, predicate, subject labels,
and hidden construction/provenance fields. The next stage must decide whether a
controlled target can be formed after removing blocked fields and controlling
class-pair leakage.

Important blocker:

- `attached to` has no observable reject labels under the current visible packet
  policy.
- `p_obs` has only `25` negative rows because the packet materialization stage
  intentionally selected T1-ready evidence.

## Boundary

- train-only label ingestion
- no validation/test usage
- no H001 artifact modification
- labels ingested after visible label lock
- hidden fields joined only after label lock for audit
- no model-safe rows
- no learned smoke
- no paper-level evidence claim

## Next

Run `compatibility_dataset_v3_attachment_observability_class_pair_repair_schema_shortcut_audit`.
The audit should focus on combined observable `p_rel`, `hanging on` observable
`p_rel`, and diagnostic-only treatment for `p_obs` and `attached to`.
