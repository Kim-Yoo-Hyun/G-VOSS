# H002 Attachment Independent Target Independence Audit V1

Created: 2026-06-25

## Purpose

`attachment_independent_audit_label_ingestion_v1`에서 만든 `C_e`, `Q_e`, `p_obs`, `p_rel`
target이 construction proxy/source hidden field나 shallow visible/id field로 쉽게 설명되는지
검증한다.

이 단계는 posterior를 학습하지 않는다. 새 H002 framework에서 먼저 필요한 것은
`factorized compatibility learning`을 학습할 만큼 독립적인 hard-relation target이 존재하는지
확인하는 것이다.

## Runner

```bash
python hypothesis/CAND-001/H002_factorized-relation-confidence/tools/attachment_independent_target_independence_audit_v1.py
```

Default output:

```text
artifacts/attachment_independent_target_independence_audit_v1/
```

## Boundary

```text
split = train_only
validation_usage = false
test_usage = false
fills_new_labels = false
trains_new_posterior = false
posterior_smoke_allowed = false
paper_evidence_allowed = false
hidden_fields_as_model_input = false
source_proxy_fields_as_model_input = false
multi_view_as_model_input = false
mesh_as_model_input = false
h001_artifacts_modified = false
```

## Result

```text
status = h002_attachment_independent_target_independence_audit_blocked_primary_positive_sparse
rows = 200
validation_errors = 0
next = attachment_independent_target_repair_plan_v1
```

Primary target:

```text
p_rel_primary_binary rows = 108
p_rel_primary_binary class_counts = 91 negative / 17 positive
p_rel min_class = 17
posterior_min_per_class = 30
p_rel class_mass_pass = false
p_rel strict_clear_slice_count = 0
p_rel diagnostic_clear_slice_count = 0
```

Compatibility target:

```text
c_e_compatibility_binary rows = 108
c_e_compatibility_binary class_counts = 91 negative / 17 positive
c_e min_class = 17
c_e class_mass_pass = false
c_e strict_clear_slice_count = 0
c_e diagnostic_clear_slice_count = 0
```

Observability target:

```text
p_obs_primary_binary rows = 160
p_obs_primary_binary class_counts = 108 observable / 52 abstain-or-unobservable
p_obs class_mass_pass = true
p_obs strict_clear_slice_count = 0
p_obs diagnostic_clear_slice_count = 0
```

Full risk flags:

```text
full_risk_flags = 97
construction_proxy_or_source_hidden = 26
visible_semantic_or_packet = 29
instance_or_scan_id = 21
label_derived_auxiliary = 21
```

## Interpretation

현재 병목은 combiner가 아니라 target이다.

- `p_rel/C_e`는 primary hard relation target이지만 positive가 17개뿐이다.
- 전체 균형 slice를 만들면 `17/17`까지만 가능하고, posterior-smoke 기준인 class당 30개를 넘지 못한다.
- construction proxy를 통제해도 visible semantic/object-pair shortcut이 남는다.
- 특히 `subject_object_visible_pair`는 primary binary에서 accept/reject contrast를 만들지 못한다.
- `p_obs`는 class mass가 충분하지만, evidence tier/object label/hidden construction field와 여전히 얽혀 있어 독립 target으로 바로 승격하기 어렵다.

따라서 다음 단계는 더 강한 모델이나 posterior 결합 방식이 아니라 target repair다.

## Next

```text
attachment_independent_target_repair_plan_v1
```
