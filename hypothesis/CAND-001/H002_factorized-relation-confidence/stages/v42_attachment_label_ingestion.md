# V42 Attachment Label Ingestion

Date: 2026-06-23 KST

## Purpose

v41에서 lock한 visible-only labels를 hidden audit manifest와 join해 target artifacts를 만들고
quick shortcut probes를 실행했다.

이 단계는 label ingestion과 diagnostic audit 준비이며 posterior smoke가 아니다.

## Artifact

```text
artifacts/train_rga_full/open3dsg_train_full/rga/
  reliability_target_v18_attachment_deferred_label_ingestion/
    summary.json
    report.md
    ingested_rows.jsonl
    multiclass_target.jsonl
    binary_target.jsonl
    diagnostic_connected_target.jsonl
    geometry_support_target.jsonl
    usefulness_target.jsonl
    endpoint_identity_target.jsonl
    coverage_target.jsonl
    abstain_rows.jsonl
    quick_probe_risks.json
    cell_contrast_summary.csv
    visible_pair_contrast_summary.csv
    predicate_contrast_summary.csv
    family_contrast_summary.csv
    role_contrast_summary.csv
    validation_errors.jsonl
```

Validation errors: `0`

Validation/test usage: `false`

Posterior smoke: `blocked`

## Status

```text
status = h002_reliability_target_v18_attachment_deferred_label_ingested_positive_sparse_with_probe_risk
next_todo = reliability_target_v18_attachment_deferred_target_independence_audit
rows = 240
```

## Target Counts

```text
multiclass_rows = 240
binary_rows = 114
diagnostic_connected_rows = 62
geometry_support_rows = 154
usefulness_rows = 114
endpoint_rows = 240
coverage_rows = 240
abstain_rows = 126
```

Primary binary target:

```text
positive_rows = 33
negative_rows = 81
class_mass_pass = false
minimum_per_class_for_posterior = 50
```

Diagnostic `connected to` target:

```text
diagnostic_connected_possible = 37
diagnostic_connected_ambiguous = 25
```

## Quick Probe

```text
quick_probe_risk_flags = 102
same_cell_mixed_reliability_binary_groups = 4
same_visible_pair_mixed_reliability_binary_groups = 3
same_predicate_mixed_reliability_binary_groups = 2
```

The most important risk is not just class imbalance. The quick probes show that current labels are
still strongly explainable by construction or visible grouping fields such as `cell_id_hidden`,
`candidate_role_hidden`, `predicate_label`, `subject_object_visible_pair`, and visible geometry
summaries.

## Interpretation

v18 attachment ingestion gives useful diagnostic evidence, but it is not posterior-ready.

Two blockers remain:

- positive class mass is too small: `33` positives versus required `50`
- shortcut risk is high: `102` quick-probe flags

Therefore the next step is a target-independence audit, not factorized posterior smoke.

## Boundary

Hidden audit metadata was read only after label lock for ingestion and audit.

It is not:

- deployable model input
- posterior performance evidence
- validation/test evidence
- paper-level benchmark evidence

## Next

```text
reliability_target_v18_attachment_deferred_target_independence_audit
```
