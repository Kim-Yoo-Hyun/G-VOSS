# V53 Attachment Audit Packet Path Decision

## Purpose

v52에서 막힌 `attachment_deferred` v19 audit packet target을 posterior smoke로 넘길지,
diagnostic evidence로 고정하고 target repair로 이동할지 결정한다.

Input:

```text
artifacts/train_rga_full/open3dsg_train_full/rga/
  reliability_target_v19_attachment_deferred_independent_evidence_audit_packet_target_independence_audit/
```

Output:

```text
artifacts/train_rga_full/open3dsg_train_full/rga/
  reliability_target_v19_attachment_deferred_independent_evidence_audit_packet_path_decision_after_audit/
```

Script:

```text
tools/reliability_target_v19_attachment_deferred_independent_evidence_audit_packet_path_decision_after_audit.py
```

## Result

```text
status = h002_reliability_target_v19_attachment_deferred_audit_packet_path_decision_select_v20_endpoint_balanced_counterfactual_repair_plan
selected_path = freeze_v19_audit_packet_diagnostic_select_v20_endpoint_balanced_counterfactual_repair_plan
next_todo = reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_repair_plan
validation_errors = 0
posterior_smoke_allowed = false
```

Audit snapshot:

```text
relation_binary_rows = 125
relation_binary_counts = {1: 26, 0: 99}
relation_class_mass_pass = false
relation_strict_clear_slices = 0
relation_diagnostic_clear_slices = 0
geometry_support_rows = 140
geometry_support_counts = {1: 41, 0: 99}
connected_diagnostic_rows = 62
connected_diagnostic_counts = {
  diagnostic_connected_possible: 15,
  diagnostic_connected_ambiguous: 47
}
full_quick_probe_risk_flags = 56
slice_blocking_risk_flags = 1185
```

## Decision

v19 audit packet target은 diagnostic-only negative target-construction evidence로 고정한다.

다음 route는 `v20_attachment_deferred_endpoint_balanced_counterfactual_repair_plan`이다.

## Why

현재 blocker는 posterior 결합 방식이 약해서가 아니다. Label target 자체가 아직
positive-sparse이고, endpoint/object/predicate/scan 같은 쉬운 shortcut으로 설명된다.

따라서 여기서 더 강한 posterior combiner를 넣으면 factorized reliability를 검증하는 것이 아니라
target construction artifact를 학습할 위험이 크다.

## Rejected Options

- posterior smoke now: reject
- stronger posterior combiner now: reject
- geometry-support as primary relation reliability target: reject
- `connected to` primary binary target: reject
- more rows with the same packet recipe: reject
- looser positive label policy: reject
- multi-view or mesh as model input now: reject for now

## Selected Repair Requirements

- Train-only rows만 사용한다.
- posterior smoke는 새 target-independence audit이 통과할 때까지 금지한다.
- 현재 240-row packet만 확장하지 말고 full train attachment candidate pool에서 다시 설계한다.
- label 이후 최소 accept/reject `60/60` class mass를 요구한다.
- 가능하면 exact endpoint-pair 내부 accept/reject contrast를 우선한다.
- exact endpoint-pair contrast가 부족하면 subject/object-family, predicate, evidence-tier, scan-balanced counterfactual strata를 사용한다.
- repeated scan/subgraph/object label/visible endpoint pair를 cap한다.
- `attached to`와 `hanging on` 각각에 accept/reject가 모두 존재하도록 설계한다.
- `connected to`는 별도 visual/mesh-functional criterion이 생기기 전까지 diagnostic-only로 유지한다.
- multi-view/mesh는 label/audit confirmation evidence로만 사용하고 deployable model input으로 넣지 않는다.
- geometry status, rank band, machine hint, source score, `p_geom_valid`, cell id, queue id는 model input으로 노출하지 않는다.

## Boundary

- Train-only H002 hypothesis artifact.
- No validation/test rows were used.
- No posterior was trained or evaluated.
- Multi-view and mesh remain audit/confirmation evidence only.
- H001 and paper artifacts were not modified.

## Next

```text
reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_repair_plan
```
