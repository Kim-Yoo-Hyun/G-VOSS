# V21 Proximity Scene/Geometry Label Ingestion

Date: 2026-06-23 KST

## Purpose

v20에서 locked 상태가 된 `close by` / proximity scene-geometry proxy labels를 hidden audit
manifest와 join하고, posterior smoke 전에 필요한 target material과 quick shortcut probes를
생성했다.

이 단계부터 hidden fields를 읽지만, 목적은 audit/control이다. Hidden metadata는 deployable
model input이 아니다.

## Artifact

```text
artifacts/train_rga_full/open3dsg_train_full/rga/
  reliability_target_v13_proximity_lh_scene_geometry_label_ingestion/
    summary.json
    report.md
    ingested_rows.jsonl
    multiclass_target.jsonl
    binary_target.jsonl
    geometry_support_target.jsonl
    usefulness_target.jsonl
    abstain_rows.jsonl
    quick_probe_risks.json
    block_contrast_summary.csv
    visible_pair_contrast_summary.csv
    validation_errors.jsonl
```

Validation errors: `0`

Validation/test usage: `false`

Posterior smoke: `blocked`

## Status

```text
status = h002_reliability_target_v13_proximity_lh_scene_geometry_label_ingested_positive_sparse_with_probe_risk
next_todo = reliability_target_v13_proximity_lh_scene_geometry_target_independence_audit
```

## Main Result

```text
rows = 240
multiclass_rows = 240
binary_rows = 176
abstain_rows = 64
geometry_support_rows = 176
usefulness_rows = 176

relation_reliability_state_v13 =
  accept_reliable_close_by: 39
  reject_dense_relation_noise: 82
  reject_trivial_or_context_only: 55
  abstain_uncertain: 64

relation_reliability_binary_target =
  positive: 39
  negative: 137

geometry_support_target =
  positive: 121
  negative: 55

usefulness_target =
  positive: 39
  negative: 137
```

## Target Viability

```text
minimum_per_class_for_posterior = 50
reliability_positive_rows = 39
reliability_negative_rows = 137
class_mass_pass = false
same_block_mixed_reliability_binary_groups = 22
same_visible_pair_mixed_reliability_binary_groups = 22
quick_probe_risk_flags = 32
```

v13은 v12 visible-only branch보다 나아진 점이 있다. v12에서는 object-pair mixed contrast가
0개라 object-pair identity로 target이 거의 결정됐다. v21에서는 same block / same visible
object-pair 내부 mixed accept/reject group이 `22`개 생겼다.

하지만 이것만으로 posterior-ready는 아니다.

- reliability positive가 `39`개로 predeclared minimum-per-class `50`보다 작다.
- quick probe가 `p_geom_bin_hidden`, `scan_id`, `geometry_witness_summary_v13`,
  `nearest_neighbor_context_v13` 등에서 shortcut risk를 감지했다.
- label이 scene/geometry visible evidence를 보고 채워졌기 때문에, geometry text surface가
  label을 직접 설명하는 것은 expected risk이며 full target-independence audit에서 통제해야 한다.

## Claim Boundary

이 단계는 target ingestion과 diagnostic audit이다. H002 posterior가 relation reliability를
개선한다는 evidence가 아니다.

현재 해석은 다음이다.

```text
target material improved over v12, but posterior smoke is still blocked by
positive sparsity and remaining shortcut risk.
```

## Next

```text
reliability_target_v13_proximity_lh_scene_geometry_target_independence_audit
```

다음 단계에서는 binary reliability, geometry-support, usefulness target 각각에 대해 controlled
slice가 있는지 확인해야 한다. 특히 same-block, same-visible-pair, same-rank-band,
same-p-geom-bin, same-geometry-witness controls가 필요하다.
