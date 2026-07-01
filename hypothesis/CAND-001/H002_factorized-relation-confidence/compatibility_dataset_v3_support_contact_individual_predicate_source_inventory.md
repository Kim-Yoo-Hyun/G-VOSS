# Compatibility Dataset V3 Support/Contact Individual Predicate Source Inventory

## Status

```text
artifact_root = artifacts/compatibility_dataset_v3_support_contact_individual_predicate_source_inventory/
status = h002_compatibility_dataset_v3_support_contact_individual_predicate_source_inventory_ready_for_candidate_materialization_plan
selected_path = plan_candidate_materialization_for_standing_lying_individual_predicate_cells_supported_by_diagnostic
validation_errors = 0
next_todo = compatibility_dataset_v3_support_contact_individual_predicate_candidate_materialization_plan
```

## Answer

현재 단계에서는 `support/contact`에 해당하는 relation type을 따로따로 본다.

```text
standing on = primary individual probe
lying on = secondary individual / pose-conditioned probe
supported by = diagnostic superordinate probe
```

즉, `support/contact`를 하나의 grouped label로 다시 학습하지 않는다. grouped target은
이미 predicate/class-pair/source shortcut이 강하다는 것이 확인됐기 때문에 main learned target으로
재사용하지 않는다.

## Source Inventory Result

| Predicate | Role | Rows | Class-Pair Balanced Rows | Mixed Groups | Verdict |
| --- | --- | ---: | ---: | ---: | --- |
| `standing on` | primary | 50245 | 382 | 13 | ready for candidate plan |
| `lying on` | secondary | 60652 | 414 | 13 | ready for candidate plan |
| `supported by` | diagnostic | 50601 | 164 | 45 | diagnostic ready |

Interpretation:

- `standing on`은 exact accept와 lying-like hard reject가 충분해서 primary probe로 진행 가능하다.
- `lying on`은 exact accept와 standing-like hard reject가 충분해서 secondary / paired `C_e` probe로 진행 가능하다.
- `supported by`는 capacity는 있지만 `standing on`/`lying on`과 동시에 참일 수 있는 superordinate relation이므로 main binary target으로 쓰지 않는다.

## Same-Geometry Anchor Capacity

```text
predicted same-pair standing+lying pairs = 35504
predicted same-pair all-three support/contact pairs = 35504
previous pose-conditioned classified anchors = 4031
previous selected balanced pose-conditioned anchors = 200
```

This supports continuing toward a candidate materialization plan for `standing on` and
`lying on`, while keeping `supported by` as a diagnostic boundary relation.

## Shortcut Risks

| Risk | Current Signal | Required Handling |
| --- | --- | --- |
| hard-surface shortcut | `standing on` 70.75%, `lying on` 69.19%, `supported by` 70.95% hard-surface rows | candidate plan must cap/stratify floor/table/wall-like pairs |
| class-pair shortcut | primary mixed class-pair groups are 13/13 | preserve mixed accept/reject class-pair cells |
| rank/source shortcut | rank bands are highly structured by predicate | rank/source fields hidden; audit after materialization |
| no-GT misuse | many no-GT rows exist | no-GT is audit/abstain candidate, not automatic reject |
| supported-by overlap | `supported by` has large overlap/abstain pool | keep diagnostic unless clean support/non-support evidence exists |

## Boundary

- Train-only source inventory only.
- No validation/test usage.
- No row materialization.
- No label fill.
- No learned smoke or model training.
- No paper-level evidence.

## Next

```text
compatibility_dataset_v3_support_contact_individual_predicate_candidate_materialization_plan
```
