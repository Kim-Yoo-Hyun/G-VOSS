# Compatibility Dataset V3 Principled Design Gap Plan After Table Review

## Status

```text
artifact_root = artifacts/compatibility_dataset_v3_principled_design_gap_plan_after_table_review/
status = h002_compatibility_dataset_v3_principled_design_gap_plan_after_table_review_ready
selected_path = select_harder_support_contact_route_protocol_before_source_deployable_promotion
validation_errors = 0
next_todo = compatibility_dataset_v3_support_contact_harder_route_protocol_after_gap_plan
```

## Judgment

H002의 현재 문제는 factorization이 부자연스럽다는 것이 아니다. `T_e`, `Z_e`, `G_e`,
`C_e`, `Q_e`를 분리하고 `C_e = compatibility(T_e, G_e)`를 핵심 mechanism으로 두는
방향은 원리적으로 유지한다.

현재 약점은 evidence mix다. 가장 강한 table row가 `relative_vertical`과
`size_relative` 같은 signed-comparison relation에 집중되어 있어, reviewer가 direct
geometry sign rule이라고 공격할 수 있다.

따라서 다음 단계는 source reranking이나 stronger combiner가 아니라, signed comparison이
아닌 harder compatibility route를 설계하는 것이다.

## Selected Gap

```text
selected_gap = harder_support_contact_route
selected_next_action = compatibility_dataset_v3_support_contact_harder_route_protocol_after_gap_plan
```

선택 이유:

- `support_contact`는 simple sign rule로 환원하기 어렵다.
- `standing on`과 `lying on`은 pose, contact, support surface, overlap/gap 같은
  geometry evidence가 필요하다.
- 기존 support/contact probe는 interaction signal을 보였지만, official validation에서는
  아직 diagnostic 상태다.
- 따라서 richer `G_e`를 정의하고 strict control을 거는 protocol repair가 필요하다.

## Deferred Paths

| Path | Decision | Reason |
| --- | --- | --- |
| current table promotion | reject | primary evidence가 너무 clean/signed-comparison-heavy |
| source-deployable experiment | defer | harder `C_e` route가 안정화된 뒤 진행 |
| observability / `p_obs` branch | defer | 현재 label이 shortcut-prone 또는 negative-sparse |
| attachment route | defer | attached/hanging label이 class-pair shortcut으로 collapse |

## Protocol Boundary

다음 support/contact hard-route protocol은 다음 원칙을 지켜야 한다.

- main predicates: `standing on`, `lying on`
- diagnostic predicate: `supported by`
- `T_e`: predicate semantic content only
- `G_e`: predicate-independent pose/contact/overlap/gap/point/mesh evidence
- `Z_e`: `C_e` input에서 제외
- `Q_e`: `C_e` input에서 제외, p_obs target 안정화 전까지 diagnostic only
- controls: semantic-only, geometry-only, concat, wrong-`T`, shuffled-`G`, subject/object swap, class-pair shortcut audit
- official test 사용 금지
- source reranking, calibrated `p_rel`/`p_obs`, SOTA, all-relation claim 금지

## Decision

현재 table은 bounded mechanism evidence로 유지한다. H002를 final paper result로 승격하지
않는다. 다음 TODO는 support/contact harder-route protocol을 설계하는 것이다.

## Next

```text
compatibility_dataset_v3_support_contact_harder_route_protocol_after_gap_plan
```
