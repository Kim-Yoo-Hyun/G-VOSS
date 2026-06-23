# V41 Attachment Label Fill

Date: 2026-06-23 KST

## Purpose

v40에서 만든 `attachment_deferred` label-ready packet을 visible-only proxy label로 채웠다.
이 단계는 hidden audit manifest를 읽지 않고 `label_ready_sheet_v18.tsv`와 review card surface만
사용한다.

이 단계는 label fill이며, label ingestion이나 posterior smoke가 아니다.

## Artifact

```text
artifacts/train_rga_full/open3dsg_train_full/rga/
  reliability_target_v18_attachment_deferred_label_fill/
    summary.json
    report.md
    filled_label_sheet_v18.tsv
    label_decisions_v18.jsonl
    validation_errors.jsonl
```

Validation errors: `0`

Hidden audit manifest read: `false`

Validation/test usage: `false`

Posterior smoke: `blocked`

## Status

```text
status = h002_reliability_target_v18_attachment_deferred_label_filled_codex_proxy_visible_only
next_todo = reliability_target_v18_attachment_deferred_label_ingestion
rows = 240
```

## Result

```text
relation_reliability_state_v18 =
  accept_reliable_attachment: 33
  reject_unreliable_attachment: 81
  abstain_uncertain: 64
  diagnostic_connected_possible: 37
  diagnostic_connected_ambiguous: 25

binary_primary_usable_rows = 114
primary_positive_rows = 33
primary_negative_rows = 81
diagnostic_rows = 62
```

Geometry support:

```text
supports = 73
contradicts = 81
ambiguous = 86
```

Predicate breakdown:

```text
attached to:
  accept = 11
  reject = 38
  abstain = 33

hanging on:
  accept = 22
  reject = 43
  abstain = 31

connected to:
  diagnostic possible = 37
  diagnostic ambiguous = 25
```

## Interpretation

This fill is valid as visible-only target material, but it is not posterior-ready.
The previous post-label gate required enough binary mass and positive mass before model smoke.
Current primary target has:

```text
binary_primary_usable_rows = 114
primary_positive_rows = 33
primary_negative_rows = 81
```

So posterior smoke remains blocked. The next step is label ingestion: join the filled sheet with
the hidden manifest, create target artifacts, and run quick probes before any target-independence audit.

## Boundary

This is train-only proxy label evidence.

It is not:

- target-independence evidence
- posterior performance evidence
- validation/test evidence
- paper-level benchmark evidence
- multi-view model-input evidence

## Next

```text
reliability_target_v18_attachment_deferred_label_ingestion
```
