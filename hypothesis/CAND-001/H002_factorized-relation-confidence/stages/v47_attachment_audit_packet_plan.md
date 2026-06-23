# V47 Attachment Audit Packet Plan

Date: 2026-06-23 KST

## Purpose

v46 source inventory를 바탕으로 attachment independent-evidence audit packet의 visible schema,
hidden asset manifest, evidence tier policy를 고정했다.

이 단계는 audit packet 설계만 수행한다. 새 label을 채우거나 posterior smoke를 실행하지 않는다.

## Artifact

```text
artifacts/train_rga_full/open3dsg_train_full/rga/
  reliability_target_v19_attachment_deferred_independent_evidence_audit_packet_plan/
    summary.json
    report.md
    audit_packet_contract.json
    visible_schema.json
    visible_packet_template.tsv
    packet_plan_rows.jsonl
    hidden_asset_manifest_plan.jsonl
    validation_errors.jsonl
```

Script:

```text
tools/reliability_target_v19_attachment_deferred_independent_evidence_audit_packet_plan.py
```

## Status

```text
status = h002_reliability_target_v19_attachment_deferred_independent_evidence_audit_packet_plan_ready_for_materialization
next_todo = reliability_target_v19_attachment_deferred_independent_evidence_audit_packet_materialization
validation_errors = 0
audit_packet_plan_gate_pass = true
posterior_smoke_allowed = false
multi_view_as_model_input = false
```

## Packet Roles

```text
rows = 240
primary_attachment_reliability_candidate = 160
connected_diagnostic_only = 62
uncertainty_or_coverage_audit_only = 18
```

`connected to`는 계속 diagnostic-only다. v18 U1 uncertainty rows 중 `connected to` 2개가 있으므로
connected diagnostic row는 60개가 아니라 62개로 집계된다.

## Evidence Tiers

```text
T1_strong_pair_visual = 43
T2_individual_visual_plus_mesh = 197
```

Primary rows:

```text
T1_strong_pair_visual = 31
T2_individual_visual_plus_mesh = 129
```

Primary by predicate:

```text
attached to: T1 17, T2 63
hanging on: T1 14, T2 66
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
review_uncertainty
review_notes
```

Forbidden from visible packet:

```text
scan_id
subgraph_id
subject_id/object_id
cell_id_hidden
sampling_queue_hidden
geometry_status_hidden
rank_band_hidden
semantic_rank_hidden
machine_hint_hidden
raw_features_hidden
v18 label states/targets/reasons/notes
```

Hidden asset paths are kept in `hidden_asset_manifest_plan.jsonl` for materialization only.

## Interpretation

The audit packet can proceed to materialization, but the packet must preserve the evidence-tier
distinction:

```text
T1 = direct same-frame visual context
T2 = separate object views plus mesh/sequence context
```

T2 rows should not be described as directly co-visible relation evidence. They are independent
object identity and mesh/context evidence for audit.

## Boundary

This stage does not:

- fill new labels
- mine new candidates
- train posterior
- create deployable multi-view features
- use validation/test data
- modify H001 or paper artifacts

## Next

```text
reliability_target_v19_attachment_deferred_independent_evidence_audit_packet_materialization
```
