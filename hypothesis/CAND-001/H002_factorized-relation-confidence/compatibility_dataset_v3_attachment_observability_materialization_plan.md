# Compatibility Dataset V3 Attachment Observability Materialization Plan

## Result

```text
artifact_root = artifacts/compatibility_dataset_v3_attachment_observability_materialization_plan/
status = h002_compatibility_dataset_v3_attachment_observability_materialization_plan_ready
selected_path = plan_primary_attached_hanging_gq_materialization_keep_connected_diagnostic
validation_errors = 0
next_todo = compatibility_dataset_v3_attachment_observability_materialization
```

This stage is a plan only. It does not materialize rows, run learned smoke, use
validation/test data, or modify H001 artifacts.

## Planned Waves

| Wave | Predicates | Planned Rows | Role |
| --- | --- | ---: | --- |
| `W1_primary_attachment_observability` | `attached to`, `hanging on` | 480 | source rows plus hidden targets for the primary observability route |
| `W2_connected_diagnostic` | `connected to` | 80 | diagnostic taxonomy only |
| `W3_full_train_expansion_deferred` | all R7 predicates | 0 | future capacity pool, not materialized now |

`attached to` and `hanging on` are the next primary materialization scope.
`connected to` remains diagnostic because source inventory found `0` explicit
topology/functional evidence rows.

## Factor Contract

`T_e` can include predicate text, predicate family, subject/object class labels,
and class-family fields. Source score, source rank, query id, packet id, GT
status, and review labels are blocked.

`G_e_attachment` should be recomputed or extracted as predicate-independent
geometry evidence: pair distance/gap, OBB overlap, point/mesh contact proxy,
anchor-surface proxy, relative pose, vertical offset, floor/support confound,
and normal/orientation proxy where available. It must not copy construction
proxy labels or old `p_geom_valid` as the geometry factor.

`Q_e_observability` can include evidence availability fields: mesh/multiview
packet readiness, contact-sheet readiness, subject/object image counts,
same-frame co-visibility, weak same-view availability, scan mesh/point/multiview
availability, and visual-evidence tier. It must not include `review_coverage`,
`review_endpoint_identity`, `review_uncertainty`, `p_obs_target`, or packet id.

`Z_e` remains hidden diagnostic only.

## Target Contract

`p_obs` is materialized first. It asks whether the current evidence is sufficient
to decide the relation.

`p_rel_observable` is materialized only for observable `attached to` and
`hanging on` rows. It is not defined for `connected to` in this wave.

`C_e_attachment` remains metadata-only until schema audit confirms that
wrong-`T_e`, shuffled-`G_e`, shuffled-`Q_e`, class-pair, query/rank, and packet
shortcuts are controlled.

## Target Snapshot

The locked label artifact has:

- rows: `560`
- predicates: `attached to 238`, `hanging on 242`, `connected to 80`
- `p_obs`: observable `306`, abstain `254`
- observable `p_rel`: accept `60`, reject `246`
- previous quick shortcut-risk flags: `98`

Therefore the next materialization can create useful source/target artifacts,
but it still cannot justify a learned reliability claim. A schema shortcut audit
must run first, and `p_rel` positive sparsity must be treated as a risk.

## Outputs For Next Stage

The next materialization should emit:

- `source_rows.jsonl`
- `model_safe_view.jsonl`
- `target_manifest.jsonl`
- `hidden_manifest.jsonl`
- `control_manifest.jsonl`
- `schema_audit_inputs.json`

The model-safe view must contain no review labels, source score/rank, query id,
packet id, GT status, instance id, scan id, construction proxy, or target fields.

## Required Controls

- wrong-`T_e` predicate swap
- shuffled-`G_e`
- shuffled-`Q_e`
- no-view or low-evidence mask
- class-pair-only probe
- hidden query/rank/source/packet leakage probe
- connected-to diagnostic probe
