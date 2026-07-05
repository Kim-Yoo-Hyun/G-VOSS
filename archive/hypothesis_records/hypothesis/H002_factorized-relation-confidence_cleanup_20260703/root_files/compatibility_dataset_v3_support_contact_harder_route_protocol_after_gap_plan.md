# Compatibility Dataset V3 Support/Contact Harder Route Protocol After Gap Plan

## Status

```text
artifact_root = artifacts/compatibility_dataset_v3_support_contact_harder_route_protocol_after_gap_plan/
status = h002_compatibility_dataset_v3_support_contact_harder_route_protocol_after_gap_plan_ready
selected_path = support_contact_harder_route_protocol_locked_select_source_inventory
validation_errors = 0
next_todo = compatibility_dataset_v3_support_contact_harder_route_source_inventory_after_protocol
```

## Judgment

현재 H002의 약점은 factorization 자체가 아니라, paper-table primary evidence가
`relative_vertical`과 `size_relative`처럼 signed-comparison relation에 몰려 있다는
점이다. 따라서 다음 단계는 source reranking이나 `p_obs`/`p_rel`로 바로 넘어가는 것이
아니라, harder relation route 하나를 더 단단하게 만드는 것이다.

선택한 route는 `support_contact`다. 이 route는 `standing on`과 `lying on`을 main으로
두고, `supported by`는 superordinate support decomposition / relabel / abstain
diagnostic으로 둔다.

## Locked Protocol

- main predicates: `standing on`, `lying on`
- diagnostic predicate: `supported by`
- main `C_e` inputs: `T_e`, `G_e`
- `T_e`: predicate text/label and semantic content
- `G_e`: predicate-independent pose/contact/overlap/gap/point/mesh evidence
- `Z_e`: main `C_e` input에서 제외
- `Q_e`: main `C_e` input에서 제외
- official test usage: false
- paper metric promoted: false

## Geometry Evidence

이번 hard route에서 `G_e`는 predicate-independent evidence로 고정한다.

- `g_vertical_gap`
- `g_xy_support_overlap`
- `g_contact_patch_ratio`
- `g_support_surface_normal_alignment`
- `g_subject_principal_axis`
- `g_bottom_surface_proximity`
- `g_local_contact_point_density`
- `g_mesh_gap_intersection`
- `g_surface_alignment`

핵심은 이 feature들이 `standing on`인지 `lying on`인지 직접 알면 안 된다는 점이다.
predicate 해석은 `C_e = compatibility(T_e, G_e)`에서만 일어나야 한다.

## Required Controls

- semantic-only
- geometry-only
- plain concat
- wrong-`T` same-route control
- shuffled-`G` global control
- shuffled-`G` within class-pair / family control
- subject/object swap
- predicate-only, class-only, class-pair, predicate x class-pair, scan/instance/source-rank shortcut probe

## Promotion Boundary

이 protocol이 통과해도 바로 말할 수 없는 claim은 다음이다.

- support/contact solved
- calibrated `p_rel` / `p_obs`
- source reranking recall/violation improvement
- official test result
- all-relation generalization

허용되는 claim은 더 좁다.

```text
support/contact hard route에서 predicate-independent geometry evidence를
predicate semantics와 compatibility로 결합해야 하는지 검증한다.
```

## Artifacts

```text
artifacts/compatibility_dataset_v3_support_contact_harder_route_protocol_after_gap_plan/
```

Key outputs:

- `relation_scope.csv`
- `geometry_evidence_protocol.csv`
- `factor_boundary.csv`
- `model_safe_schema.csv`
- `control_protocol.csv`
- `split_policy.csv`
- `promotion_gates.csv`
- `blocked_claims.csv`
- `next_contract.json`
- `report.md`

## Next

```text
compatibility_dataset_v3_support_contact_harder_route_source_inventory_after_protocol
```
