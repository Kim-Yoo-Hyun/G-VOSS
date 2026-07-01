# H002 Support/Contact Class-Pair Repair Path Decision

Default artifact:

```text
artifacts/compatibility_dataset_v3_independent_validity_support_contact_class_pair_repair_path_decision_after_capacity_scan/
```

Status:

```text
status = h002_compatibility_dataset_v3_independent_validity_support_contact_class_pair_repair_path_decision_freeze_independent_validity_diagnostic
selected_path = freeze_support_contact_independent_validity_as_diagnostic_select_scope_synthesis
validation_errors = 0
next_todo = compatibility_dataset_v3_scope_synthesis_after_support_contact_independent_validity_freeze
```

## Decision

Freeze support/contact independent-validity as diagnostic-only.

The previous repair capacity scan showed that the strict repair needed for a
main support/contact target is too sparse:

```text
predicate_x_class_pair scan-capped capacity = 88
lying on strict capacity = 64
standing on strict capacity = 24
```

The relaxed class-pair option is possible but weaker:

```text
class_pair scan-capped capacity = 426
```

This relaxed option controls `subject_class + object_class`, but it does not
control `predicate + subject_class + object_class`. Therefore it does not remove
the actual shortcut that blocked the support/contact target.

## Route Verdicts

| Route | Verdict | Reason |
| --- | --- | --- |
| Strict `predicate + subject_class + object_class` repair | Reject | Only `88` scan-capped rows, with `standing on` at `24` rows |
| Relaxed `subject_class + object_class` diagnostic | Defer as optional diagnostic | Has `426` rows, but does not remove full predicate-class shortcut |
| Object-class-masked diagnostic | Defer as optional diagnostic | Tests non-class signal but removes part of deployable `T_e` |
| Freeze support/contact independent-validity | Select | Avoids overstating a shortcut-prone target |
| New GT or human-audit support/contact source | Future/user decision | Needed only if support/contact must become a main independent-validity family |

## Interpretation

This is not a rejection of support/contact as a relation family. It means that
the current Open3DSG train-side GT/source construction does not provide a clean
support/contact independent-validity target under strict predicate-class control.

Support/contact remains useful in two narrower roles:

- diagnostic evidence showing why GT-anchored independent-validity construction
  is hard for support/contact;
- scoped `C_e` mechanism evidence from the earlier pose-conditioned
  support/contact setup.

The current main clean evidence remains the exact-stratum repaired
independent-validity smoke, which is relative-vertical dominant. The next step
is to synthesize the H002 scope after freezing support/contact independent
validity as diagnostic.

## Boundary

- Train-only path decision.
- No validation/test usage.
- No row materialization.
- No learned smoke or model training.
- No calibrated `p_rel` / `p_obs` claim.
- No paper-level evidence.
- No H001 artifact modification.
