# V44 Attachment Path Decision

Date: 2026-06-23 KST

## Purpose

v43 attachment target-independence audit 이후 H002의 다음 경로를 결정했다.

이 단계는 path decision이며 label fill, posterior smoke, validation/test evaluation이 아니다.

## Artifact

```text
artifacts/train_rga_full/open3dsg_train_full/rga/
  reliability_target_v18_attachment_deferred_path_decision_after_audit/
    summary.json
    report.md
    option_matrix.jsonl
    selected_plan.json
    validation_errors.jsonl
```

Validation errors: `0`

Validation/test usage: `false`

Posterior smoke: `blocked`

## Status

```text
status = h002_reliability_target_v18_attachment_deferred_path_decision_select_v19_independent_evidence_repair_plan
selected_path = freeze_v18_attachment_diagnostic_select_v19_independent_evidence_repair_plan
next_todo = reliability_target_v19_attachment_deferred_independent_evidence_repair_plan
```

## Decision

v18 attachment target은 diagnostic-only negative target-construction evidence로 고정한다.

다음 route는 `v19_attachment_deferred_independent_evidence_repair_plan`이다.

## Why

v18의 blocker는 combiner나 posterior capacity가 아니다. Target 자체가 아직
relation reliability를 독립적으로 설명하지 못한다.

```text
relation_binary_rows = 114
relation_binary_counts = {'0': 81, '1': 33}
relation_strict_clear_slice_count = 0
relation_diagnostic_clear_slice_count = 0
full_quick_probe_risk_flags = 119
slice_blocking_risk_flags = 3163
```

Geometry-support target은 `81/73`으로 class mass는 통과하지만, 이것은 evidence-axis target이지
relation reliability target이 아니다. 따라서 main target으로 대체하지 않는다.

`connected to`는 `37/25` diagnostic target으로 남긴다. Functional connection은 OBB-level
geometry만으로 확정하기 어렵기 때문이다.

## Rejected Options

- posterior smoke now: reject
- geometry-support as primary target: reject
- `connected to` primary binary target: reject
- more same-style attachment mining: reject
- looser positive label policy: reject
- multi-view as model input now: reject for now

## Selected Next Route

v19에서는 independent evidence repair plan을 만든다.

Requirements:

- train-only rows만 사용한다.
- posterior smoke는 계속 금지한다.
- label/audit evidence와 deployable model input feature를 분리한다.
- multi-view 또는 mesh evidence는 현재 audit/confirmation evidence로만 사용한다.
- construction key, rank band, geometry status, machine hint는 label/model input으로 쓰지 않는다.
- reliable physical attachment를 단순 geometry support/proximity와 분리하는 positive criteria를 정의한다.
- false attachment, floor/support confound, wrong endpoint, insufficient evidence를 reject criteria로 정의한다.
- `connected to`는 visual/mesh evidence가 있기 전까지 diagnostic-only로 유지한다.

## Boundary

This is not:

- posterior evidence
- validation/test evidence
- paper-level metric evidence
- H001 modification

## Next

```text
reliability_target_v19_attachment_deferred_independent_evidence_repair_plan
```
