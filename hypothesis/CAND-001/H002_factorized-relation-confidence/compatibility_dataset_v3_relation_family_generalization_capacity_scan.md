# H002 Relation-Family Generalization Capacity Scan

## Result

```text
artifact_root = artifacts/compatibility_dataset_v3_relation_family_generalization_capacity_scan/
status = h002_compatibility_dataset_v3_relation_family_generalization_capacity_scan_ready
selected_path = select_proximity_close_by_target_plan_with_all_family_eligibility_table
validation_errors = 0
next_todo = compatibility_dataset_v3_proximity_close_by_target_plan
```

## Decision

다음은 proximity / `close by` target plan으로 진행한다. 단, `close by`는 곧바로
paper-ready가 아니라 target 설계가 필요한 상태다.

핵심 이유:

```text
close by queue rows = 171324
HL rows = 0
LH rows = 171324
label_match_status = no_gt_for_pair 130125 / pair_has_other_predicate 31675 / exact_match 9524
geometry_status = satisfied 171324
mixed class-pair groups exact-vs-other = 1292
balanced rows exact-vs-other = 15444
```

즉 수량과 class-pair mixing은 충분하지만, 현재 H002 queue에서 `close by`는 전부 LH다.
따라서 다음 target plan에서 다음 원칙을 지켜야 한다.

```text
no-GT close-by pair를 자동 negative로 취급하지 않음
pair_has_other_predicate도 자동 negative로 쓰지 않음
same-distance / similar-distance hard negative를 별도 정의
distance-only verifier가 아니라 T_e-G_e compatibility인지 control
coverage / density / object scale을 Q_e 또는 G_e에 명시
```

## Relation-Family Capacity

| Family | GT Total | Queue Total | Exact Match | Mixed Class-Pair Groups | Verdict |
| --- | ---: | ---: | ---: | ---: | --- |
| `proximity` | 12300 | 171324 | 9524 | 1292 | selected first active family |
| `support_contact` | 12600 | 161498 | 7802 | 276 | per-predicate probe after proximity |
| `relative_vertical` | 3552 | 124604 | 1136 | 22 | covered by current queue / anchor |
| `attachment_deferred` | 8767 | 0 | 0 | 0 | source adapter or schema needed |
| `relative_horizontal` | 36944 | 0 | 0 | 0 | source adapter + reference frame protocol needed |
| `size_relative` | 1822 | 0 | 0 | 0 | source adapter or schema needed |
| `containment_in` | 330 | 0 | 0 | 0 | source adapter or schema needed |
| `identity_symmetry` | 2688 | 0 | 0 | 0 | source adapter or schema needed |
| `part_structural` | 701 | 0 | 0 | 0 | source adapter or schema needed |

## Support/Contact Individual Predicates

Grouped support/contact visual/mesh target은 diagnostic-only로 freeze됐지만, 개별 predicate
capacity는 다르게 보인다.

```text
standing on = queue 50245 / exact 5871 / mixed class-pair groups 96
lying on = queue 60652 / exact 1440 / mixed class-pair groups 75
supported by = queue 50601 / exact 491 / mixed class-pair groups 105
```

따라서 다음 판단은 다음과 같다.

```text
grouped support/contact target 재사용 = 하지 않음
standing on / lying on / supported by 개별 predicate probe = 가능
순서 = close by target plan 이후 또는 parallel diagnostic
```

## All Relation Types

현재 H002 queue에 들어온 relation은 다음 6개뿐이다.

```text
close by
higher than
lower than
standing on
lying on
supported by
```

나머지 Open3DSG train-full relation type은 current H002 geometry-checkable queue에 없으므로,
바로 learned model을 돌릴 수 없다. 이들은 새 source adapter, geometry schema, 또는 reference
frame protocol이 필요하다.

## Boundary

```text
split = train_only_capacity_scan
validation_usage = false
test_usage = false
h001_artifacts_modified = false
runs_learned_smoke = false
trains_new_model = false
paper_evidence_allowed = false
```

## Artifacts

```text
summary.json
predicate_capacity.csv
family_capacity.csv
route_decision.csv
example_rows.json
report.md
validation_errors.jsonl
```

## Next

```text
compatibility_dataset_v3_proximity_close_by_target_plan
```
