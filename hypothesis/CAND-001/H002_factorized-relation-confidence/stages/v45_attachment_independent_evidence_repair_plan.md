# V45 Attachment Independent-Evidence Repair Plan

Date: 2026-06-23 KST

## Purpose

v44 path decision 이후 attachment target을 바로 다시 mining하거나 posterior smoke로 넘기지 않고,
독립적인 label/audit evidence를 먼저 설계했다.

핵심은 relation reliability label이 3D geometry summary나 construction metadata를 그대로
따라가지 않도록 label evidence와 deployable input feature를 분리하는 것이다.

## Artifact

```text
artifacts/train_rga_full/open3dsg_train_full/rga/
  reliability_target_v19_attachment_deferred_independent_evidence_repair_plan/
    summary.json
    report.md
    upstream_snapshot.json
    independent_evidence_contract.json
    label_schema_contract.json
    source_inventory_contract.json
    target_independence_plan.json
    local_source_probe.json
    validation_errors.jsonl
```

Validation errors: `0`

Validation/test usage: `false`

Posterior smoke: `blocked`

## Status

```text
status = h002_reliability_target_v19_attachment_deferred_independent_evidence_repair_plan_ready_for_source_inventory
next_todo = reliability_target_v19_attachment_deferred_independent_evidence_source_inventory
```

## Decision

Selected repair route:

```text
independent_visual_or_mesh_audit_packet_before_labels
```

Scope:

```text
primary_scope = attached to, hanging on
diagnostic_scope = connected to
```

`connected to`는 계속 diagnostic-only다. Functional connection은 OBB-level geometry만으로
확정하기 어렵고 visual/mesh evidence가 필요할 수 있다.

## Why

v18 target의 실패 원인은 posterior combiner가 약해서가 아니다.

```text
relation_binary = {'0': 81, '1': 33}
strict_clear_slice_count = 0
diagnostic_clear_slice_count = 0
full_quick_probe_risk_flags = 119
slice_blocking_risk_flags = 3163
```

따라서 더 강한 결합 방식을 넣기 전에 target evidence를 먼저 고쳐야 한다.

## Evidence Contract

v19는 다음을 분리한다.

```text
S_e      = source semantic plausibility
G_3D_e   = deployable 3D geometry evidence
C_e      = coverage evidence
U_e      = uncertainty evidence
A_ind_e  = independent audit supervision source
V_mv_e   = future deployable visual evidence factor
```

현재 단계에서 `A_ind_e`는 label/audit supervision에만 쓰고, `V_mv_e`는 deployable model
input으로 만들지 않는다.

## Local Source Probe

Local probe only:

```text
3RScan root exists = true
sampled scan dirs = 40
sampled multi_view dirs = 40
sampled sequence dirs = 40
```

이는 full inventory가 아니라 다음 단계가 가능한지 보는 probe다. 다음 TODO에서 v18 rows별
subject/object crop, same-view/co-visible candidate, sequence context, mesh/point availability를
정식 inventory로 계산해야 한다.

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
reliability_target_v19_attachment_deferred_independent_evidence_source_inventory
```
