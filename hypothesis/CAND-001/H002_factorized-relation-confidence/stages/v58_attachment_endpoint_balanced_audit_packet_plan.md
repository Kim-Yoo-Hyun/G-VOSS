# V58 Attachment Endpoint-Balanced Audit Packet Plan

## Purpose

v57 source inventory를 바탕으로 v20 endpoint-balanced attachment candidate set의 audit
packet schema, hidden asset manifest plan, evidence-tier policy를 고정한다.

이 단계는 audit packet 설계만 수행한다. 이미지/mesh asset을 복사하거나 label을 채우거나
posterior smoke를 실행하지 않는다.

Input:

```text
artifacts/train_rga_full/open3dsg_train_full/rga/
  reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_source_inventory/
  reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_candidate_mining/
```

Output:

```text
artifacts/train_rga_full/open3dsg_train_full/rga/
  reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_audit_packet_plan/
```

Script:

```text
tools/reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_audit_packet_plan.py
```

## Result

```text
status = h002_reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_audit_packet_plan_ready_for_materialization
next_todo = reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_audit_packet_materialization
validation_errors = 0
audit_packet_plan_gate_pass = true
posterior_smoke_allowed = false
multi_view_as_model_input = false
```

## Packet Rows

```text
rows = 320
primary_attachment_reliability_candidate = 256
connected_diagnostic_only = 64
attached to = 128
hanging on = 128
connected to = 64
```

`connected to`는 계속 diagnostic-only다. Functional connection은 OBB/individual view/mesh
evidence만으로 primary binary reliability target에 바로 넣지 않는다.

## Evidence Tiers

```text
T1_strong_pair_visual = 75
T2_individual_visual_plus_mesh = 245
primary_T1_strong_pair_visual = 62
primary_T2_individual_visual_plus_mesh = 194
connected_T1_strong_pair_visual = 13
connected_T2_individual_visual_plus_mesh = 51
```

Primary by predicate:

```text
attached to: T1 27, T2 101
hanging on: T1 35, T2 93
```

## Visible Schema Boundary

Reviewer-visible packet fields are limited to:

```text
packet_id
blind_review_id
candidate_relation
subject_label
predicate_label
object_label
relation_family_visible
packet_role
evidence_tier
evidence_tier_description
visual_context_summary
mesh_context_summary
audit_question
review_relation_reliability
review_geometry_support
review_endpoint_identity
review_coverage
review_uncertainty
review_notes
```

Forbidden from visible packet:

```text
scan_id / subgraph_id / source_id
subject_id / object_id / instance_id
prediction_id / directed_pair_id
proxy_role_hidden / selection_route_level_hidden
cell_id_hidden / capacity_evidence_tier_hidden
typed witness fields
rank / source score / p_geom_valid / geometry_status
near_contact / projected_overlap / far_separated construction fields
raw feature paths and original source paths
```

Hidden asset paths and construction metadata stay only in `hidden_asset_manifest_plan.jsonl` for
the next materialization step.

## Interpretation

v58 confirms that the v20 audit packet can be materialized with a clean visible/hidden split.
The important design choice is to preserve the evidence-tier distinction:

```text
T1 = direct same-frame visual context
T2 = separate object views plus mesh/sequence context
```

T2 rows must not be described as direct co-visible relation evidence. They are still useful for
audit because the reviewer can inspect object identity and mesh/context evidence, but they are a
weaker evidence tier.

## Boundary

- Train-only H002 hypothesis artifact.
- No validation/test rows were used.
- No labels were filled.
- No posterior was trained or evaluated.
- No packet assets were copied or materialized.
- Multi-view/mesh is audit/confirmation evidence only, not model input.
- H001 and paper artifacts were not modified.

## Next

```text
reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_audit_packet_materialization
```
