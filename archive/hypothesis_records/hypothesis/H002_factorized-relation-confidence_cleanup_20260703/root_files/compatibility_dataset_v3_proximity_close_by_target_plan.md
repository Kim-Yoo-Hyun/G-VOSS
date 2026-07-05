# H002 Proximity Close-By Target Plan

## Result

```text
artifact_root = artifacts/compatibility_dataset_v3_proximity_close_by_target_plan/
status = h002_compatibility_dataset_v3_proximity_close_by_target_plan_ready_for_source_inventory
selected_path = plan_close_by_source_inventory_for_near_far_hard_negative_target
validation_errors = 0
next_todo = compatibility_dataset_v3_proximity_close_by_source_inventory
```

## Decision

`close by`를 먼저 진행한다. 다만 바로 learned smoke나 posterior 학습으로 가지 않고,
scale-aware near/far/abstain target을 만들 수 있는지 확인하는 source inventory를 먼저
진행한다.

이유는 단순하다. `close by`는 row 수가 충분하지만 `no_gt_for_pair`를 negative로 쓰면
annotation sparsity를 relation failure로 오해할 위험이 크다. 따라서 target은 다음 규칙을
따른다.

```text
no_gt_for_pair != reject
pair_has_other_predicate != reject
HL/LH membership != label
p_geom_valid != main target
source score/rank Z_e is excluded from C_e
```

## Current Capacity

Full train match rows 기준:

```text
close-by rows = 185346
label status = no_gt_for_pair:142571; pair_has_other_predicate:33247; exact_match:9528
geometry status = satisfied:171326; uncertain:7328; unsatisfied:6692
rank bands = rank_gt1000:133872; rank_501_1000:42864; rank_201_500:8596; rank_101_200:12; top50:2
```

이전 HL/LH queue에서는 `LH = 171324`, `HL = 0`이었다. 즉 high-semantic/low-geometry
failure를 바로 만들 수 있는 구조가 아니라, full train match rows의
`satisfied/uncertain/unsatisfied` 분포를 이용해 별도 near/far target을 설계해야 한다.

## Target Contract

```text
T_e = predicate/object semantic content
Z_e = source score/rank/provenance
G_e = predicate-independent proximity geometry
C_e = compatibility(T_e, G_e), excluding Z_e
Q_e = evidence quality / ambiguity / observability
p_obs = can this edge be judged?
p_rel = is this edge reliable when observable?
```

`G_e` 후보:

- `distance_3d`, `distance_xy`
- `normalized_distance_3d`, `normalized_distance_xy`
- `projected_iou_xy`
- projected subject/object overlap ratio
- object scale and size ratio, if derivable in the next source inventory

`Q_e` 후보:

- geometry feature availability
- degenerate or missing object geometry
- very large object / room-like object ambiguity
- dense-scene proximity ambiguity
- visual/mesh evidence availability, if later added as audit evidence

## Required Controls

- `semantic_only_T`
- `source_only_Z`
- `geometry_only_G`
- `distance_only`
- `T_plus_G_compatibility`
- `p_geom_valid_rule`
- shuffled geometry
- wrong-pair geometry
- same-distance matched subset

특히 `close by`에서는 `distance_only`가 강할 수 있다. 따라서 H002 claim은
“거리 threshold로 close-by를 맞춘다”가 아니라, 같은 거리 조건에서도 object scale,
overlap, semantic content, observability quality가 reliability 판단에 필요한지를 보여야 한다.

## Support/Contact Deferral

Grouped support/contact target은 diagnostic-only로 freeze했다. 하지만 다음 개별 predicate
probe는 유지한다.

```text
standing on
lying on
supported by
```

순서는 `close by` source inventory 이후다. 개별 predicate probe는 grouped
support/contact target의 shortcut 문제를 피하기 위해 predicate별 target과 evidence policy를
따로 잡는다.

## Boundary

```text
split = train_only_target_plan
validation_usage = false
test_usage = false
h001_artifacts_modified = false
materializes_rows = false
fills_labels = false
runs_learned_smoke = false
trains_new_model = false
paper_evidence_allowed = false
```

## Artifacts

```text
summary.json
target_contract.json
evidence_schema.csv
label_policy.csv
quota_plan.csv
hard_negative_policy.csv
shortcut_gates.csv
baseline_controls.csv
source_inventory_contract.json
close_by_distance_quantiles.csv
route_decision.csv
report.md
validation_errors.jsonl
```

## Next

```text
compatibility_dataset_v3_proximity_close_by_source_inventory
```
