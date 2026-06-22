# V20 Proximity Scene/Geometry Label Fill

Date: 2026-06-22 KST

## Purpose

v19에서 생성한 `close by` / proximity LH branch의 scene/geometry-aware label sheet를
reviewer-visible evidence만 사용해 채웠다.

이번 label fill의 목적은 posterior 성능을 보는 것이 아니라, object-pair text만 보던 v12/v14
proxy label path를 넘어 local scene/geometry evidence가 포함된 target material을 만드는 것이다.

## Artifact

```text
artifacts/train_rga_full/open3dsg_train_full/rga/
  reliability_target_v13_proximity_lh_scene_geometry_label_fill/
    summary.json
    report.md
    filled_label_sheet_v13.tsv
    label_decisions_v13.jsonl
    validation_errors.jsonl
```

Validation errors: `0`

Validation/test usage: `false`

Hidden audit manifest read during fill: `false`

Posterior smoke: `blocked`

## Status

```text
status = h002_reliability_target_v13_proximity_lh_scene_geometry_label_filled_codex_proxy_visible_only
next_todo = reliability_target_v13_proximity_lh_scene_geometry_label_ingestion
```

## Main Result

```text
rows = 240
accept_reliable_close_by = 39
reject_dense_relation_noise = 82
reject_trivial_or_context_only = 55
abstain_uncertain = 64
positive_rows = 39
negative_rows = 137
binary_usable_rows = 176
validation_errors = 0
```

## Label Policy

`accept_reliable_close_by`는 visible evidence가 다음 조건을 동시에 어느 정도 만족할 때만
부여했다.

- close/overlapping geometry가 명확함.
- local-neighbor tier가 front 또는 middle에 있음.
- duplicate 또는 many-alternative ambiguity가 제한적임.
- scene context상 해당 `close by` relation이 trivial dense-neighborhood edge가 아니라
  informative local relation으로 보임.

다음 경우는 `reject_dense_relation_noise`, `reject_trivial_or_context_only`, 또는
`abstain_uncertain`으로 처리했다.

- 같은 object type 또는 주변 object가 너무 많아 relation이 dense noise에 가까움.
- geometry evidence가 broad/tail 또는 weak overlap에 가까움.
- visual/layout evidence가 부족해 `close by` reliability를 판단하기 어려움.
- relation definition 자체가 애매함.

## Positive-Mass Risk

이번 label fill은 v12/v14보다 binary usable row가 늘었다.

```text
v14 binary usable rows = 107
v20 binary usable rows = 176
```

하지만 reliable positive는 `39`개뿐이다. 이는 이전 target gate에서 사용하던
minimum-per-class `50` 기준에 못 미친다.

따라서 이 결과를 억지로 posterior-ready target으로 올리면 안 된다. 다음 ingestion/audit에서
확인해야 할 질문은 다음이다.

```text
1. hidden audit manifest를 join한 뒤에도 target이 shortcut으로 쉽게 풀리는가?
2. object-pair, scan, rank, machine-hint, geometry-bin만으로 accept/reject가 예측되는가?
3. positive 39개가 too sparse라 posterior smoke 자체가 불안정한가?
4. 같은 visible object-pair block 내부에서 accept/reject contrast가 실제로 존재하는가?
```

## Claim Boundary

이 단계는 hypothesis-stage proxy label fill이다. paper evidence가 아니며 posterior evidence도
아니다.

중요한 점은 positive를 늘리기 위해 label policy를 완화하지 않았다는 것이다. 현재 목표는
성능을 좋게 보이게 하는 것이 아니라, H002의 relation reliability target이 독립적으로 성립할 수
있는지 확인하는 것이다.

## Next

```text
reliability_target_v13_proximity_lh_scene_geometry_label_ingestion
```

다음 단계에서는 filled label sheet를 hidden audit manifest와 join하고, multiclass/binary target,
geometry-support target, usefulness target을 만든다. 이후 positive mass와 shortcut risk를 확인한
뒤에만 posterior smoke 여부를 판단한다.
