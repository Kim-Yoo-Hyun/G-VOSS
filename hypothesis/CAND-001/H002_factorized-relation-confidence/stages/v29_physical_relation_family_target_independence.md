# V29 Physical Relation-Family Target Independence

Date: 2026-06-23 KST

## Purpose

v28에서 만든 v14 physical relation-family target artifacts가 posterior smoke에
사용될 만큼 독립적인지 audit했다. 이 단계는 model training이나 posterior smoke를
실행하지 않는다.

## Artifact

```text
artifacts/train_rga_full/open3dsg_train_full/rga/
  reliability_target_v14_physical_relation_family_target_independence_audit/
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
status = h002_reliability_target_v14_physical_relation_family_target_independence_audit_blocked_positive_sparse_and_shortcut_risk
rows = 240
relation_binary_rows = 200
relation_binary_counts = 0:152, 1:48
relation_class_mass_pass = false
relation_strict_clear_slices = 0
relation_diagnostic_clear_slices = 0
full_quick_probe_risk_flags = 65
slice_audit_rows = 174
slice_risk_rows = 3828
slice_blocking_risk_flags = 1171
posterior_allowed = false
validation_errors = 0
next_todo = reliability_target_v14_physical_relation_family_path_decision_after_audit
```

## Target Decisions

| Target | Role | Rows | Classes | Status |
| --- | --- | ---: | --- | --- |
| `relation_binary` | primary | 200 | `0:152, 1:48` | `blocked_positive_sparse` |
| `geometry_support_binary` | auxiliary | 200 | `0:152, 1:48` | `auxiliary_or_diagnostic_positive_sparse` |
| `usefulness_binary` | auxiliary | 200 | `0:152, 1:48` | `auxiliary_or_diagnostic_positive_sparse` |
| `relation_multiclass` | diagnostic | 240 | `reject:152, abstain:40, accept:48` | `auxiliary_or_diagnostic_positive_sparse` |
| `endpoint_multiclass` | diagnostic | 240 | `clear:210, uncertain:30` | `auxiliary_or_diagnostic_positive_sparse` |
| `coverage_multiclass` | provenance | 240 | `sufficient:240` | `single_class_provenance_only` |

## Interpretation

The raw relation binary target fails the class-mass gate because the positive
class has `48` rows instead of the predeclared `50`.

There is a balanced full slice of `96` rows (`48/48`), but it is not an
independent slice. It still has blocking shortcut risks from scan/object identity,
visible/hidden object-pair identity, quota cell, machine hint, rank band, and
visible witness summaries.

The strongest full quick-probe risks include:

```text
support_or_vertical_witness_summary_v14 -> relation_binary
quota_cell_id_hidden -> relation_binary
geometry_witness_summary_v14 -> relation_binary
scan_id -> relation_binary
subject/object pair -> relation_multiclass
```

Therefore v14 is useful diagnostic evidence, but it cannot support a posterior
method claim yet.

## Boundary

This is a train-only target audit.

It is not:

- paper-level benchmark evidence
- posterior performance evidence
- validation/test evidence
- a change to H001 or paper artifacts

## Next

```text
reliability_target_v14_physical_relation_family_path_decision_after_audit
```

The next step should decide whether to repair v14 sampling/labeling, collect more
positive support-contact rows, change the label surface to reduce witness-text
shortcut, or freeze this branch as diagnostic evidence.
