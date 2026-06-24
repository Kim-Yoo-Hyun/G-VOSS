# v64 Attachment Endpoint-Balanced Audit Packet Path Decision

## Goal

v63 target-independence audit 이후, v20 endpoint-balanced audit packet을 posterior smoke로
넘길지, diagnostic evidence로 고정하고 새로운 target route로 넘어갈지 결정했다.

## Input

- Audit artifact:
  `artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_audit_packet_target_independence_audit/`
- Primary relation binary target: `207` rows, `25/182`
- Strict/diagnostic clear slices: `0/0`
- Full quick-probe risk flags: `82`
- Slice-level blocking risk flags: `1,112`

## Result

```text
status = h002_reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_audit_packet_path_decision_select_v21_conditional_contrast_capacity_scan
selected_path = freeze_v20_audit_packet_diagnostic_select_v21_conditional_contrast_capacity_scan
next_todo = reliability_target_v21_attachment_deferred_conditional_contrast_capacity_scan
validation_errors = 0
posterior_smoke_allowed = false
```

## Decision

v20 endpoint-balanced audit packet은 posterior target으로 승격하지 않는다.

대신 v20은 diagnostic negative target-construction evidence로 고정하고, 다음 route는
`v21_attachment_deferred_conditional_contrast_capacity_scan`으로 선택한다.

## Why

v20의 320-row packet이 우연히 reject-heavy였을 가능성은 남아 있다. 따라서 현재 결과만으로
`attachment_deferred` 전체나 H002 factorization을 기각하지 않는다.

하지만 현재 v20 target은 posterior 검증용으로는 부적합하다.

```text
relation_binary_rows = 207
relation_binary_counts = accept:25, reject:182
relation_strict_clear_slices = 0
relation_diagnostic_clear_slices = 0
```

특히 balanced `25/25` slice를 만들 수 있어도 predicate, object/endpoint, geometry-support,
uncertainty, scan/subgraph shortcut이 남는다. 이 상태에서 posterior smoke를 실행하면
factorized reliability를 검증하는 것이 아니라 target construction artifact를 학습할 위험이 크다.

## Rejected Options

- `run_posterior_smoke_now`: reject
- `use_balanced_25_25_slice_as_posterior_target`: reject
- `try_stronger_posterior_combiner_now`: reject
- `use_geometry_support_as_primary`: reject
- `promote_connected_to_primary`: reject
- `conclude_h002_factorization_is_unnecessary`: reject
- `multi_view_or_mesh_as_model_input_now`: reject for now
- `label_more_rows_with_same_v20_recipe`: defer until full-train conditional contrast capacity is known

## Selected Next Contract

Next route:

```text
reliability_target_v21_attachment_deferred_conditional_contrast_capacity_scan
```

Purpose:

```text
Scan the full train attachment pool for conditional strata where reliability cannot be explained by one easy axis alone.
```

Required contrast questions:

- same predicate + same/near geometry-support proxy can still yield accept/reject candidates
- same predicate + same rank band can still yield accept/reject candidates
- same evidence tier + same coverage state can still contain mixed reliability candidates
- same object-pair family can still contain mixed reliability candidates
- uncertainty/coverage can explain abstain separately from reject

This scan should answer whether the v20 320-row failure is a sampling artifact or whether the
current attachment-deferred route structurally lacks factorization-requiring target strata.

## Boundary

- Train-only H002 hypothesis artifact.
- No validation/test rows were used.
- No posterior was trained or evaluated.
- No new labels were filled.
- Multi-view and mesh remain audit/confirmation evidence only.
- H001 and paper artifacts were not modified.

## Artifacts

- `artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_audit_packet_path_decision_after_audit/summary.json`
- `artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_audit_packet_path_decision_after_audit/path_decision.json`
- `artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_audit_packet_path_decision_after_audit/report.md`
