# Attachment Independent Positive Anchor Path Decision After Audit V1

Date: 2026-06-26 KST

## Purpose

This step decides what to do after the positive-anchor target-independence audit. The audit showed
that the attachment target now has enough positive/negative class mass, but still has no strict or
diagnostic controlled slice for `p_rel` or `C_e`.

The decision question is:

```text
Should H002 keep repairing this attachment reliability target,
run posterior smoke anyway,
or freeze it as diagnostic evidence and return to method-level compatibility learning?
```

## Runner

```bash
python hypothesis/CAND-001/H002_factorized-relation-confidence/tools/attachment_independent_positive_anchor_path_decision_after_audit_v1.py
```

Output root:

```text
artifacts/attachment_independent_positive_anchor_path_decision_after_audit_v1/
```

Main outputs:

- `summary.json`
- `path_decision.json`
- `route_table.csv`
- `top_risk_flags.csv`
- `report.md`
- `validation_errors.jsonl`

## Result

```text
status = h002_attachment_independent_positive_anchor_path_decision_diagnostic_freeze
selected_path = freeze_positive_anchor_target_as_diagnostic_and_move_to_compatibility_learning_plan
posterior_smoke_allowed = false
validation_errors = 0
next_todo = compatibility_learning_scope_plan_v1
```

Input audit snapshot:

```text
rows = 560
p_rel_primary_binary = 306 rows, 60 positive / 246 negative
c_e_compatibility_binary = 306 rows, 60 positive / 246 negative
p_obs_primary_binary = 480 rows, 306 observable / 174 unobservable-or-abstain
p_rel_class_mass_pass = true
p_rel_strict_clear_slice_count = 0
p_rel_diagnostic_clear_slice_count = 0
full_risk_flags = 112
```

Controlled-slice capacity:

```text
same_visible_pair_rows = 8
same_visible_pair_min_class = 4
same_predicate_visible_pair_rows = 0
construction_endpoint_strict_rows = 0
```

## Decision Matrix

| Route | Verdict | Reason |
| --- | --- | --- |
| Run posterior smoke now | Reject | It would mostly test shortcut recovery, not factorized relation reliability. |
| Select a controlled slice from current 560 rows | Reject as immediate path | Same-visible-pair has only `8` rows, same-predicate-visible-pair has `0`, and construction-endpoint-strict has `0`. |
| Mine more positive anchors with the same policy | Reject | The blocker is target identifiability, not remaining positive count. |
| Relax abstain/accept policy | Reject | This would tune the labels to fit the posterior. |
| Promote attachment target as paper reliability GT | Reject | No independent controlled slice cleared shortcut risk. |
| Use packets for `Q_e` and failure taxonomy | Select secondary | The packets are still valuable for observability and hard-relation analysis. |
| Freeze target as diagnostic and move to compatibility learning plan | Select | This is the most defensible next step for the current H002 method. |

## Interpretation

Positive-anchor mining repaired class mass, but not target independence. This is an important
distinction: the target is no longer too small, but it is still not a reliable supervised target for
`p_rel` or a final relation reliability posterior.

The attachment packet set should therefore be kept as:

- diagnostic hard-family evidence;
- `Q_e` / observability evidence;
- failure taxonomy and qualitative examples;
- possible future source for stronger manually verified positives.

It should not be used as:

- paper-level reliability GT;
- posterior smoke target;
- proof that the final factorized reliability head works.

## Next

The next H002 step should move back to the method level and define which relation families,
positive/negative tiers, evidence fields, and controls are allowed for compatibility learning.

```text
compatibility_learning_scope_plan_v1
```

## Boundary

- Train-only H002 artifact.
- No validation/test usage.
- No posterior training.
- No paper-level reliability GT promotion.
- Hidden/source/proxy fields remain diagnostic controls only.
- H001 artifacts are not modified.
