# H002 Support/Contact Individual Predicate Schema Shortcut Audit

작성일: 2026-06-29 KST

## Status

```text
artifact_root = artifacts/compatibility_dataset_v3_support_contact_individual_predicate_schema_shortcut_audit/
status = h002_compatibility_dataset_v3_support_contact_individual_predicate_schema_shortcut_audit_ready_for_sanitized_view_smoke_plan
selected_path = schema_clean_allowed_shortcuts_low_hidden_construction_risk_reported
validation_errors = 0
next_todo = compatibility_dataset_v3_support_contact_individual_predicate_sanitized_view_smoke_plan
```

## Inputs

```text
model_safe_view = artifacts/compatibility_dataset_v3_support_contact_individual_predicate_candidate_materialization/model_safe_view.jsonl
hidden_manifest = artifacts/compatibility_dataset_v3_support_contact_individual_predicate_candidate_materialization/hidden_manifest.jsonl
main_binary_rows = 640
diagnostic_rows = 160
```

## Result

```text
schema_leakage_hits = 0
allowed_high_risk_probes = 0
hidden_high_risk_probes = 2
sanitized_rows = 640
validation_errors = 0
```

Model-safe `feature_blocks`에는 hidden/source/GT/H001 construction field가 새지 않았다.
`T_e` class/predicate probes와 단일 `G_e` numeric threshold probes도 high-risk shortcut을
만들지 않았다.

## High-Risk Notes

High-risk probes는 hidden target-construction field에서만 발생했다.

```text
hidden_label_match_status accuracy = 1.000
hidden_candidate_role accuracy = 1.000
```

이 둘은 label 생성 provenance이므로 높게 나오는 것이 예상된다. 중요한 점은 이 field들이
model-safe view에 없다는 것이다. 따라서 현 단계에서는 learned smoke를 바로 실행하지 않고,
sanitized-view smoke plan으로 넘어간다.

## Key Low-Risk Probes

```text
model_T_predicate_label accuracy = 0.500
model_T_subject_object_class_pair accuracy = 0.514
hidden_hard_surface_pair accuracy = 0.503
hidden_rank_band accuracy = 0.516
hidden_predicate_class_pair accuracy = 0.684
hidden_predicate_class_pair_rank accuracy = 0.706
best single G_e probe accuracy <= 0.530
hidden_p_geom_valid accuracy = 0.527
hidden_semantic_rank accuracy = 0.520
```

Cap relaxation 때문에 `hidden_predicate_class_pair`와 `hidden_predicate_class_pair_rank`는
반드시 확인해야 했지만, 둘 다 high/medium threshold에 걸리지 않았다.

## Outputs

```text
sanitized_view = artifacts/compatibility_dataset_v3_support_contact_individual_predicate_schema_shortcut_audit/sanitized_view.jsonl
shortcut_probe_summary = artifacts/compatibility_dataset_v3_support_contact_individual_predicate_schema_shortcut_audit/shortcut_probe_summary.csv
feature_path_audit = artifacts/compatibility_dataset_v3_support_contact_individual_predicate_schema_shortcut_audit/feature_path_audit.csv
critical_probe_failures = artifacts/compatibility_dataset_v3_support_contact_individual_predicate_schema_shortcut_audit/critical_probe_failures.csv
diagnostic_profile = artifacts/compatibility_dataset_v3_support_contact_individual_predicate_schema_shortcut_audit/diagnostic_profile.csv
```

## Interpretation

이 artifact는 schema/shortcut audit을 통과했으므로, 다음 단계에서 smoke plan을 작성할 수 있다.
단, 아직 learned smoke를 실행한 것은 아니다. 다음 단계에서는 `T_only`, `G_only`, `T+G`,
hidden-control probes, wrong/shuffled controls를 포함한 sanitized-view smoke protocol을 고정해야 한다.

