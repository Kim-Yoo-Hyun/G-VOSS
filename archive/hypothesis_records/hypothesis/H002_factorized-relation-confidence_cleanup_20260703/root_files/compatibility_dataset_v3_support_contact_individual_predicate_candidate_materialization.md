# H002 Support/Contact Individual Predicate Candidate Materialization

작성일: 2026-06-29 KST

## Status

```text
artifact_root = artifacts/compatibility_dataset_v3_support_contact_individual_predicate_candidate_materialization/
status = h002_compatibility_dataset_v3_support_contact_individual_predicate_candidate_materialization_ready_for_schema_shortcut_audit
selected_path = materialized_route_aware_standing_lying_with_supported_by_diagnostic
validation_errors = 0
next_todo = compatibility_dataset_v3_support_contact_individual_predicate_schema_shortcut_audit
```

## Materialized Rows

```text
total_rows = 800
main_compatibility_rows = 640
supported_by_diagnostic_rows = 160
unique_scans = 357
hard_surface_rows = 474
```

Predicate/role counts:

```text
standing on clear_accept = 160
standing on hard_reject_lying_like = 160
lying on clear_accept = 160
lying on hard_reject_standing_like = 160
supported by clear_accept = 40
supported by hard_reject_no_support = 40
supported by overlap_or_abstain = 80
```

## Outputs

```text
candidate_rows = artifacts/compatibility_dataset_v3_support_contact_individual_predicate_candidate_materialization/candidate_rows.jsonl
model_safe_view = artifacts/compatibility_dataset_v3_support_contact_individual_predicate_candidate_materialization/model_safe_view.jsonl
hidden_manifest = artifacts/compatibility_dataset_v3_support_contact_individual_predicate_candidate_materialization/hidden_manifest.jsonl
quota_audit = artifacts/compatibility_dataset_v3_support_contact_individual_predicate_candidate_materialization/quota_audit.csv
cap_audit = artifacts/compatibility_dataset_v3_support_contact_individual_predicate_candidate_materialization/cap_audit.csv
schema_precheck = artifacts/compatibility_dataset_v3_support_contact_individual_predicate_candidate_materialization/schema_precheck.csv
selection_profile = artifacts/compatibility_dataset_v3_support_contact_individual_predicate_candidate_materialization/selection_profile.csv
```

## Schema Precheck

```text
row_count = 800 / 800
hidden_manifest_count = 800 / 800
row_id_join_integrity = pass
blocked_fields_absent_from_model_safe = pass
finite_G_e_rows = 800 / 800
learned_smoke_allowed = false
```

Model-safe view에는 `T_e`, semseg OBB 기반 `G_e_mesh_pose_contact`, `Q_e`, target labels만
남겼다. Source score/rank, GT join status, `p_geom_valid`, old geometry status, scan/object ids,
candidate role, route name은 hidden manifest에만 둔다.

## Cap Relaxation

Plan 단계의 cap은 planned quota와 충돌했다. 따라서 materialization에서는 quota를 맞추기
위해 다음 cap을 완화했고, 이 위험은 다음 schema/shortcut audit의 핵심 점검 항목으로 넘긴다.

```text
max_rows_per_predicate_class_pair: plan 32 -> actual 200
max_rows_per_predicate_class_pair_rank: plan 24 -> actual 80
max_hard_surface_rows: plan 360 -> actual 640
```

Actual cap audit:

```text
max_rows_per_scan = 15 / 20
max_rows_per_directed_pair = 2 / 2
max_rows_per_predicate_class_pair = 71 / 200
max_rows_per_predicate_class_pair_rank = 55 / 80
max_hard_surface_rows = 474 / 640
```

## Interpretation

이 단계는 relation별 evidence route를 실제 candidate rows로 만든 것이다.

- `standing on`과 `lying on`은 main compatibility target 후보로 materialize했다.
- `supported by`는 diagnostic/superordinate relation으로 유지했다.
- `G_e`는 H001 `p_geom_valid`가 아니라 semseg OBB 기반 mesh/pose/contact feature로 새로 계산했다.
- 다만 cap relaxation 때문에 이 artifact를 바로 learned smoke에 쓰면 안 된다.
- 다음 단계에서 class-pair, rank-band, hard-surface, source/GT hidden field shortcut audit를 통과해야 한다.

