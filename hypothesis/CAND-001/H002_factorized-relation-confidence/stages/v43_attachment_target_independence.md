# V43 Attachment Target Independence

Date: 2026-06-23 KST

## Purpose

v42에서 만든 v18 attachment-deferred target artifacts가 posterior smoke로 넘어갈 만큼
독립적인지 audit했다.

이 단계는 target-independence audit이며 posterior 학습이나 성능 평가가 아니다.

## Artifact

```text
artifacts/train_rga_full/open3dsg_train_full/rga/
  reliability_target_v18_attachment_deferred_target_independence_audit/
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
status = h002_reliability_target_v18_attachment_deferred_target_independence_audit_blocked_positive_sparse_and_shortcut_risk
next_todo = reliability_target_v18_attachment_deferred_path_decision_after_audit
rows = 240
```

## Target Decisions

Primary attachment reliability target:

```text
relation_binary_rows = 114
relation_binary_counts = {'0': 81, '1': 33}
min_class_count = 33
class_mass_pass = false
strict_clear_slices = 0
diagnostic_clear_slices = 0
posterior_allowed = false
```

Connected diagnostic target:

```text
connected_diagnostic_rows = 62
connected_diagnostic_counts = {'diagnostic_connected_possible': 37, 'diagnostic_connected_ambiguous': 25}
min_class_count = 25
strict_clear_slices = 0
diagnostic_clear_slices = 0
```

Auxiliary geometry-support target:

```text
geometry_support_rows = 154
geometry_support_counts = {'0': 81, '1': 73}
class_mass_pass = true
strict_clear_slices = 0
```

## Shortcut Findings

```text
full_quick_probe_risk_flags = 119
slice_blocking_risk_flags = 3163
slice_audit_rows = 266
slice_risk_rows = 7714
```

Top primary relation risks include:

- `subject_object_visible_pair`
- `scan_id`
- `provisional_status_hidden`
- `geometry_status_hidden`
- `cell_id_hidden`
- `sampling_queue_hidden`
- `reason_family_hidden`
- `machine_hint_hidden`
- `attachment_witness_summary_v18`
- `geometry_witness_summary_v18`

Balanced full slice can make `33/33`, but it still has blocking shortcut risks. Therefore this
is not an acceptable posterior target.

## Interpretation

v18 attachment route produced a valid audit artifact, but not a usable posterior target.

The blocker is twofold:

- class mass: reliable attachment positives are only `33`, below the predeclared gate
- independence: no strict or diagnostic controlled slice clears shortcut risk

Geometry-support has enough class mass, but it is an auxiliary evidence target and also has no
strict independent slice. It cannot replace relation reliability as the main target.

## Boundary

Hidden fields were used only as audit/control variables after label lock.

They are not:

- deployable model inputs
- posterior features
- validation/test evidence
- paper-level metric evidence

## Next

```text
reliability_target_v18_attachment_deferred_path_decision_after_audit
```

The path decision should decide whether to freeze v18 attachment as diagnostic evidence, repair the
target construction, add stronger label evidence, or defer attachment until multi-view audit evidence
is available.
