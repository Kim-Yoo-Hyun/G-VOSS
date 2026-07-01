# H002 Attachment Numeric Geometry Materialization V1

Date: 2026-06-25 KST

## Purpose

이 문서는 `attachment_deferred` relation에 대해 numeric predicate-independent `G_e`를
materialize한 단계를 기록한다. 이전 `prototype_dataset_v1`에서는 `attached to`,
`hanging on`, `connected to`가 audit/reliability diagnostic row로만 들어갔고
`G_e.geometry_features`가 비어 있었다.

이번 단계의 목표는 다음이다.

```text
attachment_deferred relation도 T_e + G_e compatibility smoke에 넣을 수 있는
numeric geometry evidence artifact를 만든다.
```

## Runner

```text
tools/attachment_numeric_geometry_materialization_v1.py
```

Default command:

```bash
python hypothesis/CAND-001/H002_factorized-relation-confidence/tools/attachment_numeric_geometry_materialization_v1.py
```

Input:

```text
artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v18_attachment_deferred_label_ingestion/ingested_rows.jsonl
```

Output:

```text
artifacts/attachment_numeric_geometry_v1/
```

## Why V18 Is Used

`v18` is used because it contains locked train-only attachment rows with a hidden raw geometry block:

```text
raw_features_hidden
```

This block was hidden during label fill and becomes usable after label lock as geometry-only
materialization input. The runner extracts only low-level numeric geometry fields from this block.

Excluded from `G_e`:

- source score and rank;
- predicate/family labels;
- label or audit decisions;
- `cell_id_hidden`;
- `machine_hint_hidden`;
- `geometry_status_hidden`;
- `attachment_witness_support_score_hidden`;
- `attachment_witness_contradiction_score_hidden`;
- any target/construction shortcut field.

## Materialized `G_e`

Raw geometry fields:

```text
center_delta_z
normalized_center_delta_z
normalized_distance_3d
normalized_distance_xy
projected_iou_xy
projected_subject_overlap_ratio
projected_object_overlap_ratio
vertical_gap_subject_on_object
near_contact
loose_near_contact
far_separated
projected_overlap_indicator
```

Derived geometry fields:

```text
distance_closeness_3d
distance_closeness_xy
abs_normalized_center_delta_z
vertical_gap_abs
vertical_gap_closeness
overlap_max_ratio
overlap_min_subject_object_ratio
near_contact_indicator
loose_near_contact_indicator
far_separated_indicator
```

These fields are predicate-independent object-pair geometry evidence. Predicate-specific
interpretation is left to:

```text
C_e = compatibility(T_e, G_e)
```

## Current Result

Result artifact:

```text
artifacts/attachment_numeric_geometry_v1/summary.json
```

Counts:

```text
rows = 240
numeric_g_rows = 240
compatibility_binary_rows = 114
compatibility_positive = 33
compatibility_negative = 81
counterfactual_groups = 33
connected_diagnostic_rows = 62
validation_errors = 0
```

Predicate counts:

```text
attached to = 82
hanging on = 96
connected to = 62
```

Compatibility counts:

```text
attached to: positive 11 / negative 38 / unknown 33
hanging on: positive 22 / negative 43 / unknown 31
connected to: unknown 62
```

## Interpretation

This step successfully removes the previous attachment bottleneck where `attachment_deferred`
had audit labels but no numeric `G_e`.

The result is still not paper evidence. It is a train-only hypothesis artifact that enables the
next smoke:

```text
attachment_numeric_geometry_smoke_v1
```

Important caveats:

- `attached to` and `hanging on` have binary geometry-support compatibility rows.
- `connected to` is kept diagnostic because current rows do not provide a balanced physical
  compatibility target.
- The binary target is still class-imbalanced: `33/81`.
- The target came from v18 visible-only geometry-support labeling, so shortcut and construction
  controls must be rechecked before any method claim.

## Boundary

This step:

- uses train-only rows only;
- does not use validation/test data;
- does not train a model;
- does not modify upstream artifacts;
- does not modify `prototype_dataset_v1`;
- does not produce paper-level evidence.

## Follow-Up

```text
attachment_numeric_geometry_smoke_v1 = completed
next = attachment_smoke_path_decision_v1
```

The attachment-specific smoke has now run over `artifacts/attachment_numeric_geometry_v1/`.
It confirmed a meaningful `G_e` and `T_e + G_e` signal, while also showing that hidden
construction probes remain high. The next step is a path decision.

The smoke compared:

- source-only `Z_e`;
- geometry-only `G_e`;
- semantic+source `T_e + Z_e`;
- compatibility `T_e + G_e`;
- predicate/family shortcut probe;
- construction shortcut audit using hidden controls only outside the model.
