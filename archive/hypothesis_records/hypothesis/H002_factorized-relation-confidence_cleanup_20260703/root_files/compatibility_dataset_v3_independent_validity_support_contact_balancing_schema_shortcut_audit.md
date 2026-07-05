# H002 Support/Contact Balancing Schema Shortcut Audit

Default artifact:

```text
artifacts/compatibility_dataset_v3_independent_validity_support_contact_balancing_schema_shortcut_audit/
```

Status:

```text
status = h002_compatibility_dataset_v3_independent_validity_support_contact_balancing_schema_shortcut_audit_blocked_shortcut_risk
validation_errors = 1
next_todo = compatibility_dataset_v3_independent_validity_support_contact_balancing_path_decision_after_schema_shortcut_audit
```

## Purpose

This stage audits the `1200`-row support/contact-primary independent-validity
candidate set before any learned smoke. The materialized rows are balanced at
the predicate level, but exact predicate-class balance was intentionally
relaxed to obtain enough support/contact rows. Therefore the required question
is whether allowed semantic/source fields, raw geometry fields, or hidden
construction fields can solve the target too easily.

## Input

```text
candidate_root = artifacts/compatibility_dataset_v3_independent_validity_support_contact_balancing_candidate_materialization/
candidate_rows = 1200
model_safe_rows = 1200
hidden_manifest_rows = 1200
positive / negative = 600 / 600
lying on = 300 / 300
standing on = 300 / 300
```

## Result

The schema leakage checks passed, but the shortcut audit blocks learned smoke:

```text
sanitized_blocked_feature_path_hits = 0
model_feature_blocked_key_hits = 0
source_confidence_high_or_medium_risk = 0
raw_geometry_high_or_medium_risk = 0
critical_high_or_medium_risk = 4
blocked_hidden_high_risk = 6
```

The critical allowed semantic/source probes that remain too predictive are:

```text
subject_class_label       accuracy = 0.804167  risk = medium
object_class_label        accuracy = 0.785000  risk = medium
subject_object_class_pair accuracy = 0.920000  risk = medium
predicate_x_class_pair    accuracy = 0.975833  risk = high
```

Predicate itself is balanced:

```text
predicate_label accuracy = 0.500000 risk = low
rank_band       accuracy = 0.591667 risk = low
```

Raw geometry single-field probes did not trigger a medium/high risk warning.
Source-score/rank probes also did not trigger a medium/high risk warning. The
blocker is therefore not `G_e_raw` or `Z_e` alone. The blocker is that the
relaxed support/contact target still lets object-class and predicate-class
composition explain the label.

## Interpretation

This result should not be promoted to learned compatibility smoke. A model
trained on the current support/contact set could appear to learn
`compatibility(T_e, G_e)`, while actually exploiting class priors such as which
subject/object categories are usually supportable. That would weaken the H002
claim because the intended evidence is relation-level semantic-geometry
compatibility, not object-class plausibility.

At the same time, this is not a schema-leakage failure:

- hidden construction fields are not present in the sanitized model view;
- `p_geom_valid`, `geometry_status`, label provenance, and target-construction
  summaries remain hidden-only;
- predicate balance and rank-band balance are acceptable at this audit level.

## Decision

Learned smoke remains blocked. The next step is a path decision:

```text
compatibility_dataset_v3_independent_validity_support_contact_balancing_path_decision_after_schema_shortcut_audit
```

That decision should choose one of:

- repair the support/contact target with stronger class-pair balancing or
  within-class contrast;
- remove or mask object-class labels for this diagnostic and test whether
  compatibility still survives without class shortcuts;
- freeze this support/contact-primary set as diagnostic-only and keep the
  earlier pose-conditioned support/contact result as scoped `C_e` mechanism
  evidence.

## Boundary

- Train-only hypothesis audit.
- No validation/test usage.
- No learned smoke or model training.
- No calibrated `p_rel` / `p_obs` claim.
- No paper-level evidence.
- No H001 artifact modification.
