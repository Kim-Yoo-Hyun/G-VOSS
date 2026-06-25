# V74 Hanging-On Strict Audit Packet Label Ingestion

## 목적

v73에서 잠근 visible-only `hanging on` labels를 hidden materialized manifest와 사후
join해 target artifacts와 GT/reliability mismatch analysis axis를 만들었다.

이 단계에서 hidden manifest는 label lock 이후에만 읽었다. Hidden fields와 existing
GT-match axis는 target construction, provenance, shortcut audit, mismatch analysis 용도이며
model input이 아니다.

## 결과

```text
status = h002_reliability_target_v22_hanging_on_strict_conditional_contrast_audit_packet_label_ingested_positive_sparse_with_probe_risk
next_todo = reliability_target_v22_hanging_on_strict_conditional_contrast_audit_packet_target_independence_audit
rows = 240
validation_errors = 0
posterior_smoke_allowed = false
```

Target artifacts:

```text
multiclass_rows = 240
primary_binary_rows = 202
geometry_support_rows = 202
endpoint_identity_rows = 240
coverage_rows = 240
uncertainty_rows = 240
abstain_rows = 38
```

Primary relation reliability target:

```text
positive = 9
negative = 193
minimum_per_class_for_posterior = 60
class_mass_pass = false
```

Existing GT relation match auxiliary axis:

```text
no_gt_for_pair = 164
pair_has_other_predicate = 76
exact_match = 0
family_match = 0
```

GT/reliability mismatch table:

```text
GT match & reliability accept = 0
GT match & reliability reject = 0
GT match & abstain = 0
No GT/current relation & reliability accept = 9
No GT/current relation & reliability reject = 193
No GT/current relation & abstain = 38
```

Shortcut diagnostics:

```text
quick_probe_risk_flags = 97
same_scan_mixed_primary_binary_groups = 2
same_visible_pair_mixed_primary_binary_groups = 0
same_evidence_tier_mixed_primary_binary_groups = 2
same_proxy_role_mixed_primary_binary_groups = 2
same_strict_group_mixed_primary_binary_groups = 5
same_geometry_bucket_mixed_primary_binary_groups = 4
same_rank_band_mixed_primary_binary_groups = 2
same_gt_status_mixed_primary_binary_groups = 2
```

## 해석

Ingestion은 정상적으로 완료됐지만, target은 posterior-ready가 아니다.
Primary binary target은 `9/193`으로 severe positive-sparse이며, minimum per-class
posterior gate `60/60`을 통과하지 못한다. Quick probe도 97개 risk flag를 반환했다.

특히 `review_geometry_support`와 `primary_reason_v22`는 label-derived field이므로
label 자체를 설명하는 것은 당연하다. 더 중요한 점은 hidden/source-side axis에서도
scan/subgraph/object-family/strict-group 계열 risk가 나타난다는 것이다. 따라서 다음 단계는
posterior smoke가 아니라 target-independence audit이다.

GT mismatch table은 모든 row가 `No_GT_current_relation`에 속한다. 그중 9개만 reliability
accept다. 이는 기존 GT-only evaluation이 reliable relation을 일부 놓칠 수 있다는 분석 축으로는
쓸 수 있지만, 현재 수량만으로 main posterior target을 만들기에는 부족하다.

## 산출물

- Script: `tools/reliability_target_v22_hanging_on_strict_conditional_contrast_audit_packet_label_ingestion.py`
- Artifact root: `artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v22_hanging_on_strict_conditional_contrast_audit_packet_label_ingestion/`
- Ingested rows: `ingested_rows.jsonl`
- Targets: `multiclass_target.jsonl`, `primary_binary_target.jsonl`, `geometry_support_target.jsonl`, `endpoint_identity_target.jsonl`, `coverage_target.jsonl`, `uncertainty_target.jsonl`
- Diagnostics: `quick_probe_risks.json`, `gt_reliability_mismatch_table.csv`, contrast summaries
- Summary: `summary.json`
- Report: `report.md`
- Validation errors: `validation_errors.jsonl`
