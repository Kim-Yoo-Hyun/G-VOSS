# V17 Proximity LH Path After Audit

Date: 2026-06-22 KST

## Purpose

v16 target-independence audit 이후 `proximity / close by` LH-only branch를 어떻게 처리할지
결정했다.

## Artifact

```text
artifacts/train_rga_full/open3dsg_train_full/rga/
  reliability_target_v12_proximity_lh_only_path_decision_after_audit/
    summary.json
    report.md
    option_matrix.json
    selected_plan.json
    validation_errors.jsonl
```

Validation errors: `0`

Validation/test usage: `false`

Posterior smoke: `blocked`

## Decision

```text
status = h002_reliability_target_v12_proximity_lh_path_decision_select_scene_geometry_repair
selected_path = v13_proximity_lh_scene_geometry_repair_plan
next_todo = reliability_target_v13_proximity_lh_scene_geometry_repair_plan
```

결정:

```text
visible-only proximity LH branch = diagnostic-only negative evidence
next = scene/geometry-aware target repair plan
```

## Why Not Posterior

```text
strict_slices = 0
diagnostic_slices = 0
subject_object_visible_pair_binary_mixed_groups = 0
subject_object_label_pair_hidden_binary_mixed_groups = 0
posterior_smoke_allowed = false
```

현재 실패한 경로는 H002 자체가 아니다.

```text
visible object-pair text -> proxy label -> posterior target
```

이 경로가 실패한 이유는 visible object-pair text가 label을 사실상 결정하기 때문이다.

## Selected Repair Principle

다음 target은 같은 object-pair 안에서도 reliable / unreliable `close by`가 갈릴 수 있어야 한다.

필요한 label evidence:

```text
local object layout card
distance / nearest-neighbor context
local density or duplicate-object context
scene crop or review card if available
geometry witness explanation as audit evidence
```

금지할 shortcut evidence:

```text
source semantic rank
machine_hint
label_match_status
target construction bucket
posterior score
```

## Repair Requirements

```text
candidate_source = train-only proximity LH pool
minimum_same_pair_mixed_groups_goal = 20
minimum_binary_rows_goal = 120
minimum_per_class_goal = 50
primary_sampling_unit = subject_object_visible_pair
```

Required controls:

```text
same object-pair mixed contrast
scan cap
rank-band audit
label-match / machine-hint audit after label lock
do not mix with v8/v9 support/vertical targets
```

## Next

```text
reliability_target_v13_proximity_lh_scene_geometry_repair_plan
```

Posterior smoke remains blocked until the repaired target passes target-independence audit.
