# H002 Support/Contact Individual Predicate Point/Multiview Materialization

Date: 2026-06-29 KST

## Purpose

이 단계는 `support/contact` individual predicate branch에서 point/mesh/multiview
evidence를 실제 row-level artifact로 materialize했다. 목표는 결합 모델을 바로 학습하는
것이 아니라, 다음 schema/shortcut audit에서 사용할 수 있도록 `G_e`와 `Q_e`를 분리한
model-safe view와 hidden/audit/control manifest를 만드는 것이다.

## Status

```text
artifact_root = artifacts/compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_materialization/
status = h002_compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_materialization_ready_for_schema_shortcut_audit
selected_path = materialized_gq_separated_point_mesh_view_audit_rows
rows = 800
main_rows = 640
diagnostic_rows = 160
point_stats_found_rows = 800
validation_errors = 0
next_todo = compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_schema_shortcut_audit
```

Predicate counts:

```text
lying on = 320
standing on = 320
supported by = 160
```

`supported by`는 계속 diagnostic-only다.

`Q_e` state counts:

```text
limited = 419
sufficient = 373
uncertain_or_low_observability = 8
```

## Materialized Files

- `model_safe_view.jsonl`: `T_e`, `G_e_obb_baseline`, `G_e_point_pose`, `G_e_contact_patch`, `Q_e_observability`, labels.
- `source_manifest.jsonl`: scan/object/source confidence/provenance hidden manifest.
- `visual_audit_manifest.jsonl`: multi-view crop metadata and paths for audit/control only.
- `control_manifest.jsonl`: wrong-pair geometry, shuffled geometry, wrong-view, shuffled-view pairings.
- `feature_stats.json`: numeric feature finite/range audit.
- `validation_errors.jsonl`: materialization validation errors.

## Boundary

- Validation/test rows are not used.
- H001 artifacts are not modified.
- No learned smoke is run.
- No model is trained.
- No point crop or image crop files are copied into a new model dataset.
- Multi-view is audit/`Q_e` metadata only, not learned visual input.
- Source confidence `Z_e` stays in hidden source manifest and is excluded from `C_e`.

## Feature Separation

`G_e` is split into:

- `G_e_obb_baseline`: existing semseg OBB pose/contact numeric baseline.
- `G_e_point_pose`: point-derived object extent, centroid, vertical/horizontal shape proxy, bottom/top z.
- `G_e_contact_patch`: point-derived surface gap, XY overlap, center distance, near-contact/support proxy.

`Q_e_observability` stores evidence quality only:

- point/mesh/multiview availability
- semseg/OBB availability
- segment/crop/view-count metadata
- crop score and low-observability reason flags

`Q_e` is not a truth label and must not decide relation validity by itself.

## Interpretation

이번 결과는 support/contact individual predicate branch가 point-level geometry와
multi-view audit metadata를 실제로 붙일 수 있음을 확인한 materialization step이다. 다만
아직 main learned evidence가 아니다. 다음 단계에서 `predicate`, `class_pair`,
rank/source metadata, raw geometry feature, `Q_e` state만으로 target이 쉽게 맞춰지는지
확인해야 한다.

Schema/shortcut audit가 통과해야 `T_e + G_e_point/contact` compatibility smoke로 넘어갈 수
있다. 실패하면 이 branch는 point/multiview evidence를 붙였더라도 diagnostic으로 유지한다.
