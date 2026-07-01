# H002 Independent Validity Candidate Materialization

## Status

```text
status = h002_compatibility_dataset_v3_independent_validity_candidate_materialization_ready_for_schema_shortcut_audit
validation_errors = 0
next_todo = compatibility_dataset_v3_independent_validity_schema_shortcut_audit
```

## Artifact

```text
artifact_root = artifacts/compatibility_dataset_v3_independent_validity_candidate_materialization/
candidate_rows = candidate_rows.jsonl
smoke_ready_view = smoke_ready_view.jsonl
hidden_manifest = hidden_manifest.jsonl
summary = summary.json
```

## Materialized Counts

```text
materialized_total_rows = 4027
materialized_primary_binary_rows = 3200
materialized_nonbinary_rows = 827
primary_positive_rows = 1600
primary_negative_rows = 1600
```

Family counts:

| Family | Rows |
| --- | ---: |
| `relative_vertical` | 2012 |
| `support_contact_pose_conditioned` | 2015 |

Role counts:

| Role | Rows |
| --- | ---: |
| `positive` | 1600 |
| `negative` | 1600 |
| `abstain` | 400 |
| `abstain_or_audit` | 400 |
| `audit_required` | 27 |

## Quota Result

All frozen quota cells were materialized:

| Family | Positive | Negative | No-GT Satisfied Abstain/Audit | Geometry Uncertain Abstain | GT Conflict Audit |
| --- | ---: | ---: | ---: | ---: | ---: |
| `relative_vertical` | 800 | 800 | 200 | 200 | 12 |
| `support_contact_pose_conditioned` | 800 | 800 | 200 | 200 | 15 |

No-GT rows were not used as negative labels.

## Cap Relaxation Note

Strict scan and visible-pair caps selected only `3491/4027` rows. The missing rows were caused by
visible-pair concentration in:

- `relative_vertical::positive_exact_gt_satisfied`
- `support_contact_pose_conditioned::strong_negative_gt_pair_other_predicate_unsatisfied`

The materializer then used a deterministic fallback pass that relaxed only the visible-pair cap and
selected the remaining `536` rows. Scan caps stayed enforced. This keeps the frozen primary target
balanced, but it increases shortcut risk through subject/object label pair concentration.

Therefore this artifact is not smoke-ready as a learned result until the next schema/shortcut audit
checks whether visible-pair, predicate, rank, family, or source-score features can trivially recover
the target.

## Boundary

- Train split only.
- No validation/test rows were used.
- No learned model or smoke was run.
- H001 artifacts were not modified.
- This is hypothesis-stage materialization, not paper evidence.

## Next

```text
compatibility_dataset_v3_independent_validity_schema_shortcut_audit
```
