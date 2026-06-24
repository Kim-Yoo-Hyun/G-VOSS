# V54 Attachment Endpoint-Balanced Repair Plan

## Purpose

v53 path decision에서 선택한 v20 route를 구체적인 target-repair contract로 고정한다.

이 단계는 plan artifact이며 candidate mining, label fill, posterior smoke가 아니다.

Input:

```text
artifacts/train_rga_full/open3dsg_train_full/rga/
  reliability_target_v19_attachment_deferred_independent_evidence_audit_packet_path_decision_after_audit/
  reliability_target_v19_attachment_deferred_independent_evidence_audit_packet_target_independence_audit/
  reliability_target_v19_attachment_deferred_independent_evidence_source_inventory/
  reliability_target_v17_attachment_deferred_witness_schema_capacity_scan/
```

Output:

```text
artifacts/train_rga_full/open3dsg_train_full/rga/
  reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_repair_plan/
```

Script:

```text
tools/reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_repair_plan.py
```

## Result

```text
status = h002_reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_repair_plan_ready_for_capacity_scan
next_todo = reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_capacity_scan
validation_errors = 0
posterior_smoke_allowed = false
```

Selected route:

```text
route = endpoint_balanced_counterfactual_repair
primary_predicates = attached to, hanging on
diagnostic_predicates = connected to
```

## Why

v19 audit packet target은 leakage-free packet provenance를 확보했지만 primary binary가
`26/99`로 positive-sparse이고, strict/diagnostic clear slice가 모두 `0`이었다. 또한
endpoint/object/predicate/scan shortcut이 강했다.

따라서 v20에서는 결합 방식을 바꾸기 전에 target construction을 먼저 고친다.

## Contract

Capacity scan은 다음을 평가해야 한다.

- Full train attachment candidate pool에서 mining한다.
- `attached to`와 `hanging on`은 primary target으로 유지한다.
- `connected to`는 diagnostic-only로 유지한다.
- Candidate sample size 후보는 `240`, `320`, `400`을 모두 평가한다.
- Capacity가 허용되면 default candidate sheet는 `320`으로 둔다.
- Post-label gate는 accept/reject 최소 `60/60`, usable binary 최소 `160`이다.
- `attached to`와 `hanging on` 각각 accept/reject 최소 `25/25`를 요구한다.
- Exact visible endpoint-pair mixed contrast를 우선하고, 부족하면 object-family/predicate/evidence-tier/scan-balanced counterfactual fallback을 평가한다.
- Multi-view/mesh는 label/audit confirmation evidence로만 쓰고 deployable model input으로 쓰지 않는다.
- Source score, rank band, `p_geom_valid`, geometry status, machine hint, typed witness cell, sampling role은 model input이나 visible label-surface로 노출하지 않는다.

## Boundary

- Train-only H002 hypothesis artifact.
- No validation/test rows were used.
- No labels were filled.
- No candidates were mined.
- No posterior was trained or evaluated.
- H001 and paper artifacts were not modified.

## Next

```text
reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_capacity_scan
```
