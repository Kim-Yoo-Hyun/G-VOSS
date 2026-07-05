# R7 Attachment Observability Class-Pair Repair Schema Shortcut Audit

## Result

```text
artifact_root = artifacts/compatibility_dataset_v3_attachment_observability_class_pair_repair_schema_shortcut_audit/
status = h002_compatibility_dataset_v3_attachment_observability_class_pair_repair_schema_shortcut_audit_blocked_shortcut_risk
selected_path = block_learned_smoke_select_path_decision
validation_errors = 0
next_todo = compatibility_dataset_v3_attachment_observability_class_pair_repair_path_decision_after_schema_shortcut_audit
```

## Artifact Outputs

- `summary.json`
- `report.md`
- `target_viability.csv`
- `shortcut_audit.csv`
- `controlled_strata_capacity.csv`
- `schema_field_audit.csv`
- `route_decision.csv`
- `risk_register.csv`
- `diagnostic_visible_view_not_smoke_ready.jsonl`
- `validation_errors.jsonl`

## Target Viability

- relation multiclass: `480` rows, `accept 258 / reject 90 / abstain 132`, diagnostic-only
- `p_obs`: `480` rows, positive `455`, negative `25`, negative-sparse
- combined observable `p_rel`: `348` rows, accept `258`, reject `90`, audit candidate by mass
- `attached to` observable `p_rel`: `172` rows, accept `172`, reject `0`, single-class diagnostic-only
- `hanging on` observable `p_rel`: `176` rows, accept `86`, reject `90`, audit candidate by mass

## Shortcut Findings

Allowed high-risk blockers: `14`.

Important blockers:

- combined observable `p_rel`: `predicate_subject_object_class_pair` reaches majority-rule accuracy `1.0` over baseline `0.741379`.
- `hanging on` observable `p_rel`: `subject_label`, `subject_object_class_pair`, and `predicate_subject_object_class_pair` each reach majority-rule accuracy `1.0` over baseline `0.511364`.
- `p_obs`: negative class is sparse and visible image-count/quality buckets are expected to dominate.
- `attached to`: no observable reject rows under the current visible-packet label policy.

Controlled-strata capacity confirms the same problem:

- `p_rel_combined` exact `predicate_subject_object_class_pair`: mixed groups `0`, balanced capacity `0`.
- `p_rel_hanging_on` exact `subject_object_class_pair`: mixed groups `0`, balanced capacity `0`.
- `p_rel_hanging_on` exact `predicate_subject_object_class_pair`: mixed groups `0`, balanced capacity `0`.

## Interpretation

The class-pair repair improved label mass, but it did not create a clean learned
compatibility target. The current labels are still explained by visible object
class priors. Running learned smoke would therefore test whether a model can
memorize object-class/endpoint priors, not whether `T_e` and `G_e/Q_e` form a
source-independent attachment-observability reliability signal.

This does not invalidate the R7 route. It means the current class-pair repair
artifact should be kept as diagnostic evidence, and the next step must decide
whether to freeze R7 as diagnostic, mine truly mixed same-class-pair visual
accept/reject rows, or reframe R7 primarily as `p_obs` / abstention.

## Boundary

- train-only schema/shortcut audit
- no validation/test usage
- no H001 artifact modification
- hidden fields used only after label lock for audit
- no model training
- no learned smoke
- no paper-level evidence claim

## Next

Run `compatibility_dataset_v3_attachment_observability_class_pair_repair_path_decision_after_schema_shortcut_audit`.
