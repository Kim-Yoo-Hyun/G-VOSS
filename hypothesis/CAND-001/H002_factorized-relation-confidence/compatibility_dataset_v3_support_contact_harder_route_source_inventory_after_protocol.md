# Support/Contact Harder Route Source Inventory After Protocol

## Status

```text
artifact_root = artifacts/compatibility_dataset_v3_support_contact_harder_route_source_inventory_after_protocol/
status = h002_compatibility_dataset_v3_support_contact_harder_route_source_inventory_after_protocol_ready
selected_path = support_contact_harder_route_source_inventory_ready_select_materialization_plan
validation_errors = 0
next_todo = compatibility_dataset_v3_support_contact_harder_route_materialization_plan_after_source_inventory
```

이 단계는 새 metric 실행이 아니라, locked support/contact hard-route protocol이 실제
official validation source와 full-train point/multiview 산출물 위에서 materialize 가능한지
확인하는 source inventory다.

## 핵심 판단

`support_contact` hard route는 다음 단계로 진행 가능하다. 현재 official validation
materialization은 `standing on` / `lying on` 3,178개 row를 갖고 있지만, 사용 중인
`G_e`는 아직 OBB proxy 중심이다. 반면 local 3RScan asset에는 semseg, aligned PLY,
mesh, segment, dominant normal 정보가 모두 존재하므로, 더 강한 predicate-independent
`G_e` extractor를 설계할 재료는 충분하다.

단, 이 결과는 paper metric도 아니고 official test result도 아니다. 또한
`predicate_x_class_pair` shortcut risk가 아직 높기 때문에, `support_contact`를 solved
relation family로 올릴 수는 없다.

## Source Inventory

| Source | Rows | Main Rows | Scans | 상태 |
| --- | ---: | ---: | ---: | --- |
| `official_validation_current_materialization` | 3178 | 3178 | 156 | OBB proxy `G_e` materialized |
| `official_validation_source_assets` | 3178 | 3178 | 156 | semseg/PLY/mesh/segment/normal asset available |
| `train_point_multiview_inventory` | 800 | 640 | 357 | point/mesh/multiview ready rate recorded |
| `train_point_multiview_materialization` | 800 | 640 | 357 | numeric point/OBB support-contact feature template available |

Official validation support/contact 구성:

- predicates: `standing on` 1,589 / `lying on` 1,589
- labels: positive 1,589 / negative 1,589
- unique scans: 156
- unique class pairs: 175
- largest class pair: 342 rows

## Required `G_e` Availability

| Evidence | Official availability | 현재 판단 |
| --- | ---: | --- |
| vertical gap | 1.0 | direct include |
| XY support overlap | 1.0 | direct include |
| contact patch ratio | 1.0 | extractor update 후 include |
| support surface normal alignment | 1.0 | semseg dominant normal 기반 include |
| subject principal axis / pose | 1.0 | partial current + OBB axes 기반 include |
| bottom surface proximity | 1.0 | direct include |
| local contact point density | 1.0 | PLY + segment membership 기반 extractor 필요 |
| mesh gap / intersection | 1.0 | optional mesh extractor 또는 explicit missing-mask 필요 |
| surface alignment | 1.0 | semseg normal 또는 OBB axes 기반 include |

따라서 다음 materialization plan에서는 기존 OBB feature를 유지하면서, normal/pose/contact
patch/local point density 중심으로 `G_e`를 확장해야 한다.

## Shortcut Caveat

| Probe | Majority Accuracy | Risk | 해석 |
| --- | ---: | --- | --- |
| predicate-only | 0.853996 | medium | predicate prior가 남아 있음 |
| class-pair | 0.500000 | low | class-pair 단독은 균형적 |
| predicate × class-pair | 0.993707 | high | hard-route main claim을 막는 핵심 caveat |

`predicate_x_class_pair` shortcut은 여전히 높다. 따라서 next materialization은 단순히
feature를 늘리는 작업이 아니라, shortcut audit과 control collapse를 다시 통과하도록
model-safe / hidden field 분리와 class-pair-aware evaluation을 함께 설계해야 한다.

## Next

```text
compatibility_dataset_v3_support_contact_harder_route_materialization_plan_after_source_inventory
```

다음 단계에서는 richer support/contact `G_e` materializer를 구체화한다. Main `C_e`
입력은 계속 `T_e + G_e`만 사용하고, `Z_e`와 `Q_e`는 제외한다. Official test는 사용하지
않는다.
