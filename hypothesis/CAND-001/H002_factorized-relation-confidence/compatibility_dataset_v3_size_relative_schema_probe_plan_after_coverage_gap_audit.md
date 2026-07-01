# H002 Size-Relative Schema Probe Plan After Coverage Gap Audit

## Status

```text
artifact_root = artifacts/compatibility_dataset_v3_size_relative_schema_probe_plan_after_coverage_gap_audit/
status = h002_compatibility_dataset_v3_size_relative_schema_probe_plan_after_coverage_gap_audit_ready
selected_path = size_relative_source_inventory_with_semseg_obb_scale_features
validation_errors = 0
next_todo = compatibility_dataset_v3_size_relative_source_inventory_after_schema_probe_plan
```

## Decision

다음 active H002 relation-family probe는 `size_relative`다.

```text
family = size_relative
predicates = bigger than, smaller than
GT count = 911 + 911
current H002 queue count = 0
```

이 단계는 schema/source-adapter plan이다. 아직 row materialization, learned smoke, posterior run,
paper-level promotion을 하지 않는다.

## Why Size Relative

`size_relative`는 vertical/support/proximity와 다른 새 physical relation family다. 동시에 object OBB,
extent, volume, footprint area, height 같은 predicate-independent geometry evidence를 만들 수 있어
source-adapter 비용이 낮다.

핵심은 단순 size threshold가 아니라 같은 directed object-pair geometry에 대해 `bigger than`과
`smaller than`을 모두 생성하는 same-G predicate-flip contrast다.

```text
same subject/object geometry
row 1: predicate = bigger than
row 2: predicate = smaller than
```

이렇게 하면 `G_e_size`는 두 row에서 동일하고, 달라지는 것은 `T_e`의 predicate뿐이다. 따라서
geometry-only가 아니라 `C_e = compatibility(T_e, G_e)`가 필요한지 확인할 수 있다.

## Schema Contract

```text
T_e = predicate text/label and optional object class text
G_e_size = OBB/extent/volume/area/height ratios, excluding predicate and source score
Q_e_size = OBB availability and ambiguous-size-band evidence
C_e = compatibility(T_e, G_e_size), excluding Z_e
```

Primary `G_e_size` fields:

- `subject_volume`
- `object_volume`
- `log_volume_ratio_subject_over_object`
- `log_max_extent_ratio_subject_over_object`
- `log_footprint_area_ratio_subject_over_object`
- `log_height_ratio_subject_over_object`
- `size_evidence_margin`

## Controls

필수 gate:

- same-G predicate flip
- geometry-only collapse check
- plain concat baseline
- class-pair shortcut
- source/GT leakage block
- ambiguous band abstain
- structural object filter
- scan/endpoint grouped split

## Source Adapter Plan

다음 source inventory는 아래를 확인해야 한다.

- `3DSSG/relationships.json`에서 `bigger than` / `smaller than` GT anchor count
- 3RScan `semseg.v2.json` OBB join rate
- pair OBB availability
- size-ratio margin distribution
- ambiguous-band row count
- class-pair / structural-object mass
- same-G predicate-flip capacity

## Claim Boundary

아직 허용되지 않는 claim:

- final main table
- paper-level evidence
- all-family generality
- size-relative solved
- geometry-only success as H002 main claim
- no-GT pair as negative

## Next

```text
compatibility_dataset_v3_size_relative_source_inventory_after_schema_probe_plan
```
