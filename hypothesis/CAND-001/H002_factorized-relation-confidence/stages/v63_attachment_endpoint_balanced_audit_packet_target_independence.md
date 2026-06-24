# v63 Attachment Endpoint-Balanced Audit Packet Target Independence

## Goal

v62에서 ingested 된 v20 attachment-deferred endpoint-balanced counterfactual audit packet labels가
posterior smoke의 primary target으로 충분히 독립적인지 확인했다.

검증 대상은 train-only row만 사용했다. Validation/test row는 사용하지 않았다.

## Input

- Label ingestion artifact:
  `artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_audit_packet_label_ingestion/`
- Rows: `320`
- Primary binary target: `207` rows, accept/reject = `25/182`
- Diagnostic `connected to`: `64` rows, all `abstain_uncertain`

## Result

```text
status = h002_reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_audit_packet_target_independence_audit_blocked_positive_sparse_and_shortcut_risk
rows = 320
relation_binary_rows = 207
relation_binary_counts = 0:182, 1:25
relation_strict_clear_slices = 0
relation_diagnostic_clear_slices = 0
full_quick_probe_risk_flags = 82
slice_blocking_risk_flags = 1112
validation_errors = 0
posterior_smoke_allowed = false
```

Auxiliary target decisions:

```text
geometry_support_binary = 219 rows, 61/158, class mass pass, no strict clear slice
endpoint_identity_binary = 320 rows, 259/61, class mass pass, no strict clear slice
coverage_binary = 320 rows, 75/245, class mass pass, no strict clear slice
uncertainty_multiclass = 320 rows, min class 35, class sparse
connected_diagnostic = 64 rows, single class abstain_uncertain
```

## Interpretation

이번 audit는 v20의 row 수나 packet 품질 문제가 아니라 target 품질 문제를 확인했다.
Primary relation target은 positive가 `25`개뿐이라 minimum-per-class `60` gate를 통과하지
못한다. 또한 balanced `25/25` slice를 만들 수 있어도 predicate, review geometry support,
endpoint identity, uncertainty, subject/object label, visible pair, scan/subgraph id 같은
control axis가 여전히 label을 설명한다.

특히 `review_geometry_support`가 relation binary를 거의 직접 설명한다. 이는 현재 label이
relation reliability 전체 문제라기보다 geometry-support decision에 너무 가깝게 collapse될
위험이 있다는 뜻이다. 이 target으로 posterior를 돌리면 factorized reliability가 좋아진
것인지, human review field를 재현한 것인지 구분하기 어렵다.

## Decision

v20 target은 posterior smoke로 승격하지 않는다.

다음 단계는 path decision이다.

```text
next_todo = reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_audit_packet_path_decision_after_audit
```

Path decision에서 판단해야 할 선택지는 다음이다.

- v20을 diagnostic negative target-construction evidence로 고정한다.
- 현재 attachment-deferred route를 더 이상 label mining으로 밀지 않는다.
- relation reliability target을 만들기 위해 accept mass가 실제로 늘어나는 relation family나
  label policy를 재설계한다.
- stronger posterior combiner나 multi-view-as-input은 target-independence가 해결되기 전까지
  계속 보류한다.

## Artifacts

- `artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_audit_packet_target_independence_audit/summary.json`
- `artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_audit_packet_target_independence_audit/report.md`
- `artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_audit_packet_target_independence_audit/target_decisions.json`
- `artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_audit_packet_target_independence_audit/full_shortcut_risks.json`
- `artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_audit_packet_target_independence_audit/slice_audit.csv`
- `artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_audit_packet_target_independence_audit/slice_risks.json`
