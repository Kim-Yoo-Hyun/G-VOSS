# Support/Contact Harder Route Materialization Plan After Source Inventory

## Status

```text
artifact_root = artifacts/compatibility_dataset_v3_support_contact_harder_route_materialization_plan_after_source_inventory/
status = h002_support_contact_harder_route_materialization_plan_after_source_inventory_ready
selected_path = support_contact_harder_route_materialization_plan_ready_select_docker_materializer_implementation
validation_errors = 0
next_todo = compatibility_dataset_v3_support_contact_harder_route_docker_materialization_after_plan
```

이 단계는 실제 row materialization이나 metric 실행이 아니라, support/contact hard route의
richer `G_e` materializer가 무엇을 만들어야 하는지 고정한 plan 단계다.

## 고정된 범위

| 항목 | 값 |
| --- | ---: |
| official validation support/contact rows | 3178 |
| same-pair predicate-flip groups | 1589 |
| paired groups passing integrity check | 1589 |
| paired groups failing integrity check | 0 |
| `standing on` rows | 1589 |
| `lying on` rows | 1589 |
| positive rows | 1589 |
| negative rows | 1589 |
| official test usage | 0 |

`support_contact`는 여전히 solved claim이 아니다. 이 plan은 official validation을
eval-only source로 사용하며, official test는 사용하지 않는다.

## Materializer가 만들어야 할 핵심 `G_e`

| Evidence | 구현 상태 | 역할 |
| --- | --- | --- |
| vertical gap | direct current | required main |
| XY support overlap | direct current | required main |
| bottom surface proximity | direct current | required main |
| subject principal axis / pose | partial current + OBB axes | required main |
| support surface normal alignment | semseg normal derived | required if derivable |
| surface alignment | semseg normal or OBB-axis derived | required if derivable |
| contact patch ratio | proxy current, extractor update 필요 | required after update |
| local contact point density | point extraction 필요 | required after update |
| mesh gap / intersection | optional extractor or missing-mask | optional / Q_e-masked |

핵심 원칙은 `G_e`가 predicate-independent geometry evidence여야 한다는 점이다.
`standing on`인지 `lying on`인지는 `C_e = compatibility(T_e, G_e)`에서 판단해야 한다.

## Model View 정책

Primary view는 `model_safe_main_no_class`로 고정한다.

```text
allowed = T_e.predicate_text + T_e.route_family + G_e_hard_route_numeric
blocked = Z_e, Q_e, class labels, ids, GT/source/construction fields, H001 p_geom_valid
```

이 결정을 둔 이유는 현재 `predicate x class-pair` shortcut이 너무 강하기 때문이다.
Class semantic은 H002의 큰 factor contract에서는 `T_e`에 포함될 수 있지만, 이번
support/contact hard route에서는 first main view에 넣으면 class-pair prior를 복사할
위험이 크다. 따라서 class labels는 ablation view에서만 사용한다.

## Shortcut 진단

현재 official support/contact에서:

```text
predicate_class_cell_count = 350
mixed_predicate_class_cells = 8
mixed_predicate_class_rows = 106
mixed_predicate_class_balanced_rows = 40
```

즉, 같은 `predicate x class-pair` 안에서 accept/reject가 모두 존재하는 cell은 너무
적다. 따라서 within-cell mixed slice는 primary metric으로 쓰기 어렵고, shortcut
diagnostic/control로만 사용한다.

## Promotion Gate

다음 Docker materialization 이후에도 바로 paper result로 올리면 안 된다. 최소한 다음
gate가 필요하다.

- materialization integrity: 3,178 rows / 1,589 paired groups / validation errors 0
- richer `G_e` availability: OBB direct feature + normal/pose/contact-density 또는 explicit missing-mask
- schema separation: `model_safe_main_no_class` blocked-field hit 0
- shortcut control: `predicate x class-pair` probe와 within-class-pair shuffled-`G` control 포함
- interaction evidence: `T_e x G_e`가 predicate-only, geometry-only, concat보다 강하고 wrong-`T` / shuffled-`G`에서 무너짐
- claim boundary: official test, source reranking, calibrated `p_obs/p_rel`, solved support/contact claim 금지

## Next

```text
compatibility_dataset_v3_support_contact_harder_route_docker_materialization_after_plan
```

다음 단계는 Docker 기반 materializer 구현이다. 계획된 runtime output root는:

```text
experiments/H002_compatibility_routing/support_contact_harder_materialization/latest/
```
