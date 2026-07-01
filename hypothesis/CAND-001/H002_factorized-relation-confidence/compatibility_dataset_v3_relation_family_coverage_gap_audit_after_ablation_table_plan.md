# H002 Relation-Family Coverage Gap Audit After Ablation/Table Plan

## Status

```text
artifact_root = artifacts/compatibility_dataset_v3_relation_family_coverage_gap_audit_after_ablation_table_plan/
status = h002_compatibility_dataset_v3_relation_family_coverage_gap_audit_after_ablation_table_plan_ready
selected_path = select_size_relative_schema_probe_keep_horizontal_reference_frame_protocol_second
validation_errors = 0
next_todo = compatibility_dataset_v3_size_relative_schema_probe_plan_after_coverage_gap_audit
```

## Decision

이 단계의 핵심 결론은 H002의 candidate table/ablation contract가 아직 final main table이 아니라는 점이다.
현재 H002 queue는 전체 Open3DSG/3DSSG relation type을 커버하지 않는다. 따라서 paper-level promotion
전에 relation-family별 coverage gap을 먼저 명시해야 한다.

## Coverage Summary

| Family | Predicates | Current status | Decision |
| --- | --- | --- | --- |
| `size_relative` | `bigger than`, `smaller than` | current queue 없음, GT `1822` | next active schema/source-adapter probe |
| `relative_horizontal` | `left`, `right`, `front`, `behind`, `in front of` | current queue 없음, GT `36944` | high-value gap, reference-frame protocol 먼저 필요 |
| `relative_vertical` | `higher than`, `lower than` | current queue 있음 | current clean anchor 유지 |
| `support_contact` | `standing on`, `lying on`, `supported by` | current queue 있음 | caveated compatibility route 유지 |
| `proximity` | `close by` | current queue 있음 | geometry-easy diagnostic/control 유지 |
| `attachment_deferred` | `attached to`, `hanging on`, `connected to`, `mounted on` | current queue 없음 | visual/mesh observability adapter 필요 |
| `containment_in` | `inside`, `standing in`, `lying in`, `hanging in` | current queue 없음, GT 낮음 | future containment schema |
| `part_structural` | `part of`, `belonging to`, `build in`, `cover`, `leaning against` | current queue 없음 | current physical compatibility main claim에서는 제외 |
| `identity_symmetry` | `same as`, `same symmetry as` | current queue 없음 | separate semantic/identity task로 분리 |

## Why Size Relative Next

`size_relative`는 새 relation family이면서 geometry evidence 설계 비용이 낮다. `bigger than`과
`smaller than`은 object scale, volume, height, footprint area 같은 predicate-independent `G_e`를
만들 수 있고, 같은 object-pair geometry에서 predicate direction을 바꾸는 compatibility test도 가능하다.

주의할 점은 `size_relative`도 너무 쉽게 geometry-only로 풀릴 수 있다는 것이다. 따라서 다음 probe는
단순 size threshold가 아니라 same-geometry / predicate-flip / class-pair / source-rank control을 포함해야 한다.

## Why Not Horizontal First

`relative_horizontal`은 GT mass가 가장 크므로 reviewer 관점에서 중요한 gap이다. 그러나 `left/right/front/behind`
는 world frame, viewer frame, camera frame, object-centric frame 중 어떤 기준을 쓰는지에 따라 label 의미가
바뀐다. 따라서 row mining보다 reference-frame protocol이 먼저 필요하다.

## Claim Boundary

아직 허용되지 않는 claim:

- final main table
- all-family generality
- Docker/paper-level promotion
- support/contact solved
- calibrated `p_rel/p_obs`

현재 H002 claim은 여전히 train-only relation-aware predicate-geometry compatibility routing hypothesis다.

## Next

```text
compatibility_dataset_v3_size_relative_schema_probe_plan_after_coverage_gap_audit
```
