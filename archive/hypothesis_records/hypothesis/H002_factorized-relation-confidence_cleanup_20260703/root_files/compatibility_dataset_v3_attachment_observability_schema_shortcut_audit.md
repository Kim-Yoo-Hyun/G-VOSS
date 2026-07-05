# R7 Attachment Observability Schema Shortcut Audit

Date: 2026-06-30

## Status

```text
artifact_root = artifacts/compatibility_dataset_v3_attachment_observability_schema_shortcut_audit/
status = h002_compatibility_dataset_v3_attachment_observability_schema_shortcut_audit_blocked_shortcut_risk
selected_path = blocked_allowed_model_safe_shortcut_risk
validation_errors = 0
learned_smoke_allowed = false
next_todo = compatibility_dataset_v3_attachment_observability_path_decision_after_schema_shortcut_audit
```

## Purpose

This step audits the R7 attachment-observability materialization before any
learned smoke. It checks whether model-safe fields leak targets or whether the
current target can be nearly reconstructed by simple allowed shortcuts.

## Inputs

- `artifacts/compatibility_dataset_v3_attachment_observability_materialization/model_safe_view.jsonl`
- `artifacts/compatibility_dataset_v3_attachment_observability_materialization/source_rows.jsonl`
- `artifacts/compatibility_dataset_v3_attachment_observability_materialization/target_manifest.jsonl`
- `artifacts/compatibility_dataset_v3_attachment_observability_materialization/hidden_manifest.jsonl`

## Outputs

- `summary.json`
- `schema_leakage.csv`
- `shortcut_probe_summary.csv`
- `critical_probe_failures.csv`
- `diagnostic_profile.csv`
- `p_obs_smoke_ready_view.jsonl`
- `p_rel_observable_smoke_ready_view.jsonl`
- `validation_errors.jsonl`
- `report.md`

The smoke-ready views are written for reproducibility, but they are not approved
for learned smoke because the audit is blocked.

## Counts

| Item | Count |
| --- | ---: |
| rows | 560 |
| `p_obs` rows | 560 |
| observable `p_rel` rows | 306 |
| `p_obs` labels | `1:306`, `0:254` |
| observable `p_rel` labels | `1:60`, `0:246` |
| schema leakage hits | 0 |
| allowed high-risk blockers | 4 |
| allowed medium-risk probes | 45 |
| hidden high-risk probes | 5 |

## Critical Blockers

| Probe | Target | Accuracy |
| --- | --- | ---: |
| `T_subject_object_pair` | `p_obs` | 0.958929 |
| `T_predicate_x_class_pair` | `p_obs` | 1.000000 |
| `T_subject_object_pair` | observable `p_rel` | 0.986928 |
| `T_predicate_x_class_pair` | observable `p_rel` | 1.000000 |

## Interpretation

The materialized files pass schema leakage checks: hidden ids, source score/rank,
packet paths, review labels, and target fields are not present in
`model_safe_view.jsonl`.

However, the target itself is still shortcut-prone. The current accept/reject and
observable/not-observable labels are almost perfectly determined by semantic
class-pair strata. This means a learned model could succeed by memorizing
predicate and endpoint class combinations rather than learning attachment
observability or predicate-geometry compatibility.

This does not invalidate the R7 route. It means the current 560-row reused
packet set is useful as diagnostic evidence, but not yet as a learned attachment
observability target.

## Decision

Do not run learned smoke from this artifact.

The next step should be a path decision. Reasonable options are:

1. Mine class-pair-balanced R7 rows where the same predicate and same or similar
   subject/object class pairs contain both accept and reject cases.
2. Redefine R7 as an observability-only diagnostic route and defer attachment
   `p_rel` until stronger point/mesh/topology evidence exists.
3. Keep `attached to` / `hanging on` as qualitative or audit evidence while
   moving the next learned target to another route.

## Boundary

- Train-only schema audit.
- No validation/test split was used.
- No labels were changed.
- No learned model was run.
- H001 artifacts were not modified.
