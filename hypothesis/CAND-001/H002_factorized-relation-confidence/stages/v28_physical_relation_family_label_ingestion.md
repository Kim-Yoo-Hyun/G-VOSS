# V28 Physical Relation-Family Label Ingestion

Date: 2026-06-23 KST

## Purpose

v27에서 lock한 visible-only proxy labels를 v26 hidden audit manifest와
`blind_review_id`로 join해 target artifacts를 만들었다. 이 단계는 label을 새로 만들지
않고, hidden fields를 posterior input이 아니라 audit/control metadata로만 보존한다.

## Artifact

```text
artifacts/train_rga_full/open3dsg_train_full/rga/
  reliability_target_v14_physical_relation_family_label_ingestion/
    summary.json
    report.md
    ingested_rows.jsonl
    multiclass_target.jsonl
    binary_target.jsonl
    geometry_support_target.jsonl
    usefulness_target.jsonl
    endpoint_identity_target.jsonl
    coverage_target.jsonl
    abstain_rows.jsonl
    quick_probe_risks.json
    quota_cell_contrast_summary.csv
    visible_pair_contrast_summary.csv
    predicate_contrast_summary.csv
    family_contrast_summary.csv
    validation_errors.jsonl
```

Validation errors: `0`

Validation/test usage: `false`

Posterior smoke: `blocked`

## Status

```text
status = h002_reliability_target_v14_physical_relation_family_label_ingested_positive_sparse_with_probe_risk
rows = 240
multiclass_rows = 240
binary_rows = 200
geometry_support_rows = 200
usefulness_rows = 200
endpoint_rows = 240
coverage_rows = 240
abstain_rows = 40
positive_rows = 48
negative_rows = 152
class_mass_pass = false
quick_probe_risk_flags = 64
validation_errors = 0
next_todo = reliability_target_v14_physical_relation_family_target_independence_audit
```

## Target Counts

```text
relation_reliability_state_v14 = accept_reliable:48, reject_unreliable:152, abstain_uncertain:40
binary_target = 1:48, 0:152
geometry_support_target = 1:48, 0:152
usefulness_target = 1:48, 0:152
endpoint_identity_state_v14 = clear:210, uncertain:30
coverage_state_v14 = sufficient:240
```

## Contrast Checks

```text
same_quota_cell_mixed_reliability_binary_groups = 3
same_visible_pair_mixed_reliability_binary_groups = 11
same_predicate_mixed_reliability_binary_groups = 3
```

This is better than a fully identity-determined target, but it is not enough to
claim target independence. The strongest quick-probe risks are visible witness
text and geometry/cell metadata, which are close to the proxy label policy.

## Key Risk

The target is still positive-sparse relative to the earlier minimum class-mass
gate (`48 < 50`). Also, quick-probe risk flags (`64`) show that shortcut and
label-policy leakage risks remain plausible.

Therefore this stage does not unlock posterior smoke. It only unlocks a full
target-independence audit.

## Boundary

This is hypothesis-stage target material.

It is not:

- paper-level human-confirmed benchmark evidence
- posterior performance evidence
- validation/test evidence
- a change to H001 or paper artifacts

## Next

```text
reliability_target_v14_physical_relation_family_target_independence_audit
```
