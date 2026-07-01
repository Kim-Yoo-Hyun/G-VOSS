# Compatibility Dataset V3 Attachment Observability Target Plan

## Result

```text
artifact_root = artifacts/compatibility_dataset_v3_attachment_observability_target_plan/
status = h002_compatibility_dataset_v3_attachment_observability_target_plan_ready_for_source_inventory
selected_path = plan_r7_attachment_observability_first_source_inventory_before_materialization
validation_errors = 0
next_todo = compatibility_dataset_v3_attachment_observability_source_inventory
```

This step defines the R7 attachment observability route for `attached to`,
`hanging on`, and `connected to`. It does not materialize rows, run a model, use
validation/test data, or promote paper evidence.

## Decision

R7 should be handled as an observability-first route.

The first question is not whether the relation is reliable. The first question is
whether the required evidence is present enough to judge the relation at all.

```text
p_obs low -> abstain
p_obs high + p_rel high -> accept
p_obs high + p_rel low -> reject
```

`p_rel` is only valid on observable rows. This keeps `Q_e` from directly becoming
a relation-truth shortcut.

## Predicate Policy

| Predicate | Role | Policy |
| --- | --- | --- |
| `attached to` | primary observability-then-reliability | needs visible/mesh/point evidence for physical attachment, mounted contact, or stable contact beyond proximity/support |
| `hanging on` | primary observability-then-reliability | needs anchor/contact/suspension evidence; near-contact or floor support is not enough |
| `connected to` | diagnostic observability-then-topology | remains diagnostic until physical/topological/functional connection evidence is explicit |

## Target Contract

| Target | Label Space | Use |
| --- | --- | --- |
| `p_obs` | observable / abstain / topology-functional uncertain | first-head selective decision |
| `p_rel_observable` | observable accept / observable reject | second-head reliability on `p_obs`-positive rows only |
| `multiclass_route_label` | accept / reject / abstain / functional-topology uncertain | diagnostic taxonomy until balance and independence pass |
| `C_e_attachment` | compatible / incompatible / abstain | candidate learned compatibility target after source inventory and schema audit |

## Evidence Boundary

`T_e` contains predicate and object-class semantic content. It must not include
source score, rank, query id, construction proxy, packet id, GT status, or review
label.

`G_e_attachment` contains predicate-independent geometry evidence such as pair
point/contact features, surface/contact area, mesh contact/topology, distance,
overlap, anchor geometry, vertical suspension, pose, normal, and orientation.

`Q_e` contains observability and evidence-quality fields such as same-frame
visibility, crop availability, point count, mesh completeness, occlusion,
endpoint identity, visual-mesh disagreement, and functional/topology ambiguity.

`Z_e` is source confidence. It can be used as a diagnostic or final baseline, but
it is excluded from `C_e` construction.

## Existing Attachment Artifacts

The previous positive-anchor attachment artifacts are reused only as inventory
and blocker evidence:

- `attachment_independent_positive_anchor_label_ingestion_v1`: `560` rows;
  predicate counts `attached to 238`, `hanging on 242`, `connected to 80`;
  labels `accept 60`, `reject 246`, `abstain 254`; shortcut-risk flags `98`.
- `attachment_independent_positive_anchor_target_independence_audit_v1`:
  strict clear slices `0`; confirms the old binary target is not independently
  identifiable enough for learned smoke.
- `attachment_independent_positive_anchor_packet_materialization_v1`: `560`
  ready packets; usable as source-inventory evidence, not as direct model input.

## Gates

The next step is source inventory. It must count available point, mesh, visual,
packet, and topology/functional evidence by predicate before any materialization.

Learned smoke remains blocked until:

- `Q_e` is separated from accept/reject labels.
- `p_rel` rows are emitted only for observable candidates.
- predicate/class/query/packet/source/rank shortcuts are audited.
- wrong-pair, shuffled-view, shuffled-`G_e`, wrong-`T_e`, and no-view controls
  are predeclared.
