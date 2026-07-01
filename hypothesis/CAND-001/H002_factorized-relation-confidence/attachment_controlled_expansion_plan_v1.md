# H002 Attachment Controlled Expansion Plan V1

Date: 2026-06-25 KST

## Purpose

`attachment_shortcut_controlled_smoke_v1`에서 strict within-cell balanced control을 통과했다.
하지만 해당 slice는 `34` rows뿐이므로 method claim으로 승격할 수 없다.

이번 단계의 목적은 attachment 계열을 버리지 않고, 더 큰 train-only controlled candidate
set으로 확장하기 위한 materialization contract를 고정하는 것이다.

## Runner

Command:

```bash
python hypothesis/CAND-001/H002_factorized-relation-confidence/tools/attachment_controlled_expansion_plan_v1.py
```

Output:

```text
artifacts/attachment_controlled_expansion_plan_v1/
```

Status:

```text
h002_attachment_controlled_expansion_plan_v1_ready
validation_errors = 0
```

## Input Evidence

Controlled smoke:

```text
rows = 34
positive / negative = 17 / 17
T+G AUROC = 0.9550
hidden best AUROC = 0.5000
```

v20 full-train endpoint-balanced capacity:

```text
400-row preview feasible = true
quota deficits = {}
attached to = 80 positive + 80 counterfactual negative
hanging on = 80 positive + 80 counterfactual negative
connected to = 40 near/overlap diagnostic + 40 far/ambiguous diagnostic
```

Rejected strict route:

```text
v21 same-predicate/rank/geometry/family strict route = blocked
reason = strict_spec_each_primary_predicate_mixed_min_10 failed
```

## Selected Route

```text
v20_endpoint_balanced_preview_400_repackage_with_numeric_geometry_join
```

이 선택의 의미는 다음과 같다.

- v20의 endpoint-balanced full-train capacity를 사용한다.
- target size를 `400` rows로 늘린다.
- `attached to`와 `hanging on`을 primary binary compatibility task로 둔다.
- `connected to`는 아직 binary relation reliability target이 아니라 diagnostic/observability
  axis로 둔다.
- v20 preview row를 새 H002 compatibility-learning schema로 재패키징한다.
- 다음 materialization에서 raw pair geometry를 다시 조인해 numeric `G_e`를 구성한다.

## Target Contract

```text
target_rows = 400
primary_binary_rows = 320
diagnostic_connected_rows = 80
split = train_only
```

Primary compatibility task:

```text
attached to:
  positive = 80
  counterfactual_negative = 80

hanging on:
  positive = 80
  counterfactual_negative = 80
```

Diagnostic connected task:

```text
connected to:
  near_or_overlap_diagnostic = 40
  far_or_functional_ambiguous_diagnostic = 40
```

`connected to`를 primary binary로 넣지 않는 이유는 functional connection이 OBB/metric geometry만으로
성립 여부가 확정되기 어렵기 때문이다. 이 relation은 이후 multi-view/mesh audit evidence가 붙을 때
primary로 승격할 수 있다.

## Input Boundary

Model input:

```text
T_e = predicate/object semantic content
Z_e = source confidence/rank
G_e = predicate-independent numeric geometry evidence
Q_e = raw geometry availability and uncertainty/observability cues
```

Compatibility rule:

```text
C_e = compatibility(T_e, G_e)
Z_e must not enter C_e
```

Forbidden as model input:

```text
cell_id_hidden
proxy_role
provisional_status_hidden
capacity_evidence_tier
geometry_status
machine_hint
label/review fields
```

Hidden fields may be used only for sampling, validation, and shortcut probes.

## Next Materialization Contract

Next runner:

```text
tools/attachment_controlled_candidate_materialization_v1.py
```

Input preview:

```text
artifacts/train_rga_full/open3dsg_train_full/rga/
  reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_capacity_scan/
  preview_internal_400.jsonl
```

Required output:

```text
artifacts/attachment_controlled_candidates_v1/
  candidate_rows.jsonl
  compatibility_rows.jsonl
  diagnostic_connected_rows.jsonl
  summary.json
  validation_errors.jsonl
  report.md
```

The materializer must join preview rows back to raw pair geometry by `prediction_id` or
`directed_pair_id` and emit numeric `G_e` fields compatible with the current
`attachment_numeric_geometry_v1` schema.

## Next Smoke Gates

The follow-up smoke should pass these minimum gates before attachment is merged into the combined
H002 prototype.

```text
primary_binary_rows >= 240
per primary predicate positive >= 60
per primary predicate negative >= 60
validation_errors = 0
T+G beats source-only
T+G beats predicate/family shortcut
T+G beats hidden-best probe by at least 0.05 AUROC
endpoint-label-pair shortcut AUROC <= 0.70
```

## Decision

Attachment remains a promising H002 extension, but the next operation is materialization, not paper
promotion.

Next TODO:

```text
attachment_controlled_candidate_materialization_v1
```

