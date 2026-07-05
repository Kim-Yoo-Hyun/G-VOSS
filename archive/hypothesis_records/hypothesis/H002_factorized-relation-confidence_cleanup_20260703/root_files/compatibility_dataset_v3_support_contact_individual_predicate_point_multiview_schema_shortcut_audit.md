# H002 Support/Contact Individual Predicate Point/Multiview Schema Shortcut Audit

Date: 2026-06-29 KST

## Purpose

이 단계는 point/multiview materialized dataset이 learned smoke로 넘어가기 전에
schema leakage와 shortcut risk를 확인한다. 특히 `T_e/G_e/Q_e` model-safe feature가
`C_e` target을 너무 쉽게 맞추는지, hidden source/construction/visual-audit field가
model-safe view에 섞였는지 확인했다.

## Status

```text
artifact_root = artifacts/compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_schema_shortcut_audit/
status = h002_compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_schema_shortcut_audit_ready_for_smoke_plan
selected_path = schema_clean_no_allowed_high_risk_probe_smoke_plan_allowed
main_binary_rows = 640
diagnostic_rows = 160
smoke_ready_rows = 640
target_counts = accept/positive 320, reject/negative 320
schema_leakage_hits = 0
allowed_high_risk_probes = 0
allowed_medium_risk_probes = 0
hidden_high_risk_probes = 3
validation_errors = 0
next_todo = compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_smoke_plan
```

## Main Probe Results

Top allowed model-safe probes:

```text
model_T_predicate_x_class_pair acc = 0.684375, risk = low
model_G_e_point_pose_subject_extent_y acc/AUROC = 0.540625 / 0.537920, risk = low
model_G_e_point_pose_subject_top_z acc/AUROC = 0.535937 / 0.529346, risk = low
model_G_e_point_pose_subject_centroid_z acc/AUROC = 0.534375 / 0.527788, risk = low
model_G_e_point_pose_subject_extent_z acc/AUROC = 0.534375 / 0.523584, risk = low
```

Hidden/control probes:

```text
hidden_candidate_role acc = 1.0, risk = high
hidden_label_match_status acc = 1.0, risk = high
hidden_machine_hint acc = 1.0, risk = high
hidden_scan_id acc = 0.653125, risk = low
hidden_p_geom_valid acc/AUROC = 0.526563 / 0.514346, risk = low
```

## Interpretation

이번 audit는 positive result다. 기존 support/contact branch에서 반복적으로 문제가 됐던
class-pair/predicate/source shortcut이 이번 point/multiview materialized model-safe view에서는
high-risk로 나타나지 않았다. 특히 `G_e_point_pose`, `G_e_contact_patch`,
`G_e_obb_baseline`, `Q_e_observability`의 단일 feature threshold가 target을 쉽게 풀지
못했다.

다만 hidden construction field인 `candidate_role`, `label_match_status`, `machine_hint`는
여전히 label을 완벽하게 설명한다. 이 필드들은 `source_manifest`에만 있고
`model_safe_view`에는 없으므로 현재 artifact를 막지는 않지만, 다음 smoke plan에서 절대
model input으로 넣으면 안 된다.

## Output Files

- `shortcut_probe_summary.csv`: allowed/hidden shortcut probe result.
- `feature_path_audit.csv`: model-safe feature path leakage audit.
- `critical_probe_failures.csv`: empty except header, because no allowed critical failure occurred.
- `diagnostic_profile.csv`: `supported by` diagnostic row profile.
- `smoke_ready_view.jsonl`: 640 main rows for the next smoke plan.
- `validation_errors.jsonl`: empty.

## Decision

Proceed to smoke planning. Do not run learned smoke directly from this step. The next step must define
model views and controls over:

- OBB-only baseline
- point-only geometry
- contact-only geometry
- point + contact geometry
- `T_e + G_e` compatibility
- `T_e + G_e + Q_e` observability-aware diagnostic
- wrong-pair geometry
- shuffled geometry global / within predicate
- wrong-view / shuffled-view controls, if visual metadata is used later
