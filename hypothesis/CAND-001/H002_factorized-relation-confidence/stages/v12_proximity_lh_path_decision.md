# V12 Proximity LH Path Decision

Date: 2026-06-22 KST

## Purpose

v11 proximity feasibility 결과를 바탕으로 `close by` / proximity를 H002의 다음 target
repair branch로 받아들일지 결정했다.

핵심 질문은 다음과 같다.

```text
Should H002 reduce RGA to LH-only?
Or should RGA remain bidirectional while the next empirical branch is LH-only?
```

## Artifact

```text
artifacts/train_rga_full/open3dsg_train_full/rga/
  reliability_target_v10_proximity_lh_only_path_decision/
    summary.json
    report.md
    option_matrix.json
    selected_plan.json
    validation_errors.jsonl
```

Validation errors: `0`

Validation/test usage: `false`

Posterior smoke: `blocked`

Label fill: `blocked`

Label readiness: `allowed`

## Decision

```text
status = h002_reliability_target_v10_proximity_lh_path_decision_select_lh_only_label_readiness
selected_path = v12_proximity_lh_only_label_readiness
next_todo = reliability_target_v12_proximity_lh_only_label_readiness
```

결정:

```text
RGA framework는 bidirectional HL/LH mismatch로 유지한다.
현재 empirical branch만 proximity LH-only로 좁힌다.
```

즉, H002의 핵심 claim은 그대로 둔다.

```text
semantic score != geometry validity != relation reliability
```

다만 현재 `proximity / close by` artifact에서는 `RGA-HL = 0`, `RGA-LH = 171324`이므로,
이 relation family에서 억지로 양방향 benchmark를 만들지 않는다.

## Evidence

```text
total_proximity_rows = 185346
queue_proximity_rows = 171324
RGA-HL proximity rows = 0
RGA-LH proximity rows = 171324
strict_lh_pool_rows = 50966
preview_rows = 240
unique_scans = 106
unique_label_pairs = 173
```

## Selected Target Question

다음 branch의 target question:

```text
Among low-semantic/high-geometry close-by edges,
distinguish reliable true underconfidence from dense proximity noise,
annotation sparsity, and alternative-relation cases.
```

이 질문은 geometry-only와 semantic-only를 모두 어렵게 만든다.

- semantic-only는 source rank가 낮으므로 relation을 reject하기 쉽다.
- geometry-only는 all rows가 geometry satisfied라서 relation을 accept하기 쉽다.
- factorized reliability는 둘 중 하나로 환원되지 않는 relation reliability를 설명해야 한다.

## Rejected Paths

- `redefine_rga_as_lh_only`: reject. RGA framework는 양방향 mismatch 정의로 유지해야 한다.
- `run_factorized_posterior_now`: reject. 독립 reliability label과 target-independence audit이 아직 없다.
- `construct_proximity_hl_source_now`: defer. 현재 train evidence에 proximity HL이 없으므로 artificial target risk가 크다.
- `use_label_match_status_as_target`: reject. `machine_hint`가 `label_match_status`를 1.0 accuracy로 예측하므로 target으로 쓰면 안 된다.
- `add_multiview_as_model_input_now`: reject. base S/G/C/U posterior target이 먼저 깨끗해야 한다.

## Next

```text
reliability_target_v12_proximity_lh_only_label_readiness
```

다음 단계는 v10 preview candidates를 label-ready sheet로 준비하는 것이다. 단, reviewer-visible
field에서 `machine_hint`, `label_match_status`, `rank_band`, `scan_id`,
`subject_object_label_pair`는 숨기거나 audit-only로 유지해야 한다.

Posterior smoke는 label ingestion 이후 target-independence audit을 통과하기 전까지 계속 금지한다.
