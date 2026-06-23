# V22 Proximity Scene/Geometry Target Independence Audit

Date: 2026-06-23 KST

## Purpose

v21에서 생성한 `close by` / proximity scene-geometry target material이 posterior smoke에
사용될 만큼 독립적인지 검사했다.

검사 대상은 다음 네 가지다.

- primary `relation_binary`
- auxiliary `geometry_support_binary`
- auxiliary `usefulness_binary`
- diagnostic `relation_multiclass`

## Artifact

```text
artifacts/train_rga_full/open3dsg_train_full/rga/
  reliability_target_v13_proximity_lh_scene_geometry_target_independence_audit/
    summary.json
    report.md
    target_decisions.json
    full_shortcut_risks.json
    slice_audit.csv
    slice_risks.json
    validation_errors.jsonl
```

Validation errors: `0`

Validation/test usage: `false`

Posterior smoke: `blocked`

## Status

```text
status = h002_reliability_target_v13_proximity_lh_scene_geometry_target_independence_audit_blocked_positive_sparse_and_shortcut_risk
next_todo = reliability_target_v13_proximity_lh_scene_geometry_path_decision_after_audit
```

## Target Decisions

| Target | Role | Rows | Class Counts | Class Mass | Strict Clear | Diagnostic Clear | Status |
| --- | --- | ---: | --- | --- | ---: | ---: | --- |
| `relation_binary` | primary | 176 | `0:137, 1:39` | fail | 0 | 0 | `blocked_positive_sparse` |
| `geometry_support_binary` | auxiliary | 176 | `1:121, 0:55` | pass | 0 | 0 | `auxiliary_or_diagnostic_no_strict_independent_slice` |
| `usefulness_binary` | auxiliary | 176 | `0:137, 1:39` | fail | 0 | 0 | `auxiliary_or_diagnostic_positive_sparse` |
| `relation_multiclass` | diagnostic | 240 | `82/64/39/55` | fail | 0 | 0 | `auxiliary_or_diagnostic_positive_sparse` |

## Main Finding

v21에서 same block / same visible-pair mixed accept/reject group이 `22`개 생긴 것은 v12보다
개선된 지점이다. 하지만 v22 audit에서는 posterior-ready target이 되지 못했다.

```text
primary reliability min_class_count = 39
posterior_min_per_class = 50
relation strict_clear_slice_count = 0
relation diagnostic_clear_slice_count = 0
full_quick_probe_risk_flags = 41
slice_blocking_risk_flags = 517
```

특히 relation reliability target은 balanced full slice로도 `39/39`까지만 만들 수 있으므로
strict class-mass gate를 넘지 못한다. diagnostic mass가 되는 slice도 남는 shortcut risk 때문에
clear slice가 되지 못했다.

## What Failed

Primary reliability target:

- positive class가 `39`개라 posterior class-mass gate에 미달한다.
- `same_block`, `same_visible_pair`, `same_rank_band`, `same_p_geom_bin`, `same_geometry_witness`
  계열 control을 적용해도 blocking risk가 남는다.
- 주요 residual risk는 `scan_id`, `p_geom_bin_hidden`, `geometry_witness_summary_v13`,
  `nearest_neighbor_context_v13`, `label_match_status_hidden`, `machine_hint_hidden`이다.

Geometry-support target:

- class mass는 `121/55`로 통과한다.
- 그러나 auxiliary target이고, strict mass가 있는 slice들도 blocking risk가 남아 independent
  target으로 승격할 수 없다.

## Interpretation

이 결과는 H002 factorization 자체가 틀렸다는 뜻이 아니다. 현재 실패한 것은 v13 proximity
scene-geometry target construction이다.

더 정확한 해석:

```text
scene/geometry-aware label surface improved contrast over v12,
but the resulting target is still too positive-sparse and too entangled with
geometry/scene shortcut variables for posterior smoke.
```

## Next

```text
reliability_target_v13_proximity_lh_scene_geometry_path_decision_after_audit
```

다음 단계에서는 다음 중 하나를 선택해야 한다.

1. v13 proximity branch를 diagnostic-only로 고정한다.
2. 추가 positive mining으로 class mass를 보강한다.
3. `close by`를 main posterior branch가 아니라 generality/limitation evidence로 낮춘다.
4. support/vertical 또는 attachment-style relation으로 primary target repair route를 되돌린다.
