# Attachment Independent Positive Anchor Target Independence Audit V1

Date: 2026-06-26 KST

## Purpose

This step audits whether the positive-anchor attachment target can support a posterior smoke test
after class mass has been repaired. The previous ingestion produced enough accept/reject rows, but
row count alone is not sufficient: the target must not be trivially recoverable from predicate,
rank, endpoint identity, packet construction, hidden proxy fields, or label-derived auxiliaries.

## Runner

```bash
python hypothesis/CAND-001/H002_factorized-relation-confidence/tools/attachment_independent_positive_anchor_target_independence_audit_v1.py
```

Output root:

```text
artifacts/attachment_independent_positive_anchor_target_independence_audit_v1/
```

Main outputs:

- `summary.json`
- `report.md`
- `target_decisions.json`
- `full_predictor_risks.json`
- `full_predictor_risk_flags.csv`
- `slice_audit.csv`
- `validation_errors.jsonl`
- `controlled_slices/`

## Result

```text
status = h002_attachment_independent_positive_anchor_target_independence_audit_blocked_shortcut_risk
rows = 560
targets = 6
full_risk_flags = 112
full_risk_rows = 192
strict_clear_slices_total = 0
diagnostic_clear_slices_total = 0
validation_errors = 0
next_todo = attachment_independent_positive_anchor_path_decision_after_audit_v1
```

Target-level summary:

```text
p_rel_primary_binary = 306 rows, 60 positive / 246 negative
c_e_compatibility_binary = 306 rows, 60 positive / 246 negative
p_obs_primary_binary = 480 rows, 306 observable / 174 unobservable-or-abstain
geometry_support_binary = 306 rows, 60 supported / 246 unsupported

p_rel_class_mass_pass = true
p_rel_strict_clear_slice_count = 0
p_rel_diagnostic_clear_slice_count = 0
c_e_strict_clear_slice_count = 0
c_e_diagnostic_clear_slice_count = 0
```

Risk categories:

```text
construction_proxy_or_source_hidden = 36
instance_or_scan_id = 32
label_derived_auxiliary = 21
visible_semantic_or_packet = 20
official_gt_axis = 3
```

## Interpretation

The positive-anchor repair solved the immediate class-mass blocker: the primary `p_rel` and `C_e`
targets now have the required `60/60` minimum mass. However, the target is still not identifiable
under controlled-slice criteria.

The best balanced slice is the overall balanced `120`-row slice with `60/60` positive/negative
rows, but it still leaves uncontrolled shortcut risk from construction proxies, provenance IDs,
visible endpoint semantics, official GT axes, and label-derived auxiliary fields. Strong examples
include `decision_reason`, `review_geometry_support`, `directed_pair_id_hidden`,
`same_scene_family_rank_key_hidden`, `subject_object_visible_pair`, and
`visible_pair_key_hidden`.

Therefore this result should be read as:

```text
class mass = repaired
target independence = not repaired
posterior smoke = still blocked
```

## Boundary

- This audit uses train-side H002 artifacts only.
- No validation or test split is used.
- Hidden/source/proxy fields are diagnostic controls only.
- No posterior model is trained in this step.
- No paper-level evidence is promoted from this result.
- H001 experiment and paper artifacts are not modified.

## Decision

Do not run posterior smoke from this target yet. The next step is a path decision that chooses
between controlled-slice repair, label-policy repair, geometry-evidence materialization, or a method
route change for attachment.

Next:

```text
attachment_independent_positive_anchor_path_decision_after_audit_v1
```
