# H002 Scope Synthesis After Support/Contact Independent-Validity Freeze

Default artifact:

```text
artifacts/compatibility_dataset_v3_scope_synthesis_after_support_contact_independent_validity_freeze/
```

Status:

```text
status = h002_compatibility_dataset_v3_scope_synthesis_after_support_contact_freeze_ready
selected_path = freeze_current_scope_select_independent_target_source_decision
validation_errors = 0
next_todo = compatibility_dataset_v3_independent_target_source_decision_after_scope_synthesis
```

## Purpose

This stage synthesizes the current H002 scope after support/contact
independent-validity was frozen as diagnostic-only. The goal is to separate:

- main train-only `C_e` evidence;
- scoped support/contact mechanism evidence;
- diagnostic support/contact independent-validity failure evidence;
- calibration and posterior blockers;
- the next target-source decision.

## Current Claim Boundary

Allowed now:

```text
H002 currently supports a train-only predicate-conditioned compatibility
mechanism: semantic/source evidence and predicate-independent geometry are
insufficient by themselves, while C_e = compatibility(T_e, G_e) separates valid
and invalid relation candidates on the exact-stratum repaired target.
```

Blocked:

- paper-level result;
- held-out validation/test performance;
- all-family 3DSSG reliability;
- support/contact independent-validity main result;
- calibrated `p_rel` / `p_obs` reliability posterior;
- attachment/proximity/horizontal generality.

## Family Scope

| Family | Current role | Allowed | Blocked |
| --- | --- | --- | --- |
| `relative_vertical` | main train-only `C_e` evidence | `C_e` discrimination/ranking on train-only exact-stratum repaired target | held-out reliability, paper-level result, `p_rel/p_obs` |
| `support_contact_pose_conditioned` | scoped constructed `C_e` mechanism evidence | support/contact-specific predicate-conditioned geometry mechanism | independent relation-validity reliability |
| `support_contact_independent_validity` | diagnostic-only frozen | negative target-construction evidence | main support/contact learned smoke |
| `attachment_like` | deferred | none in current main scope | target independence and observability unresolved |
| `proximity` | deferred | none in current main scope | distance-verifier collapse risk |

## Key Numbers

Main train-only independent-validity `C_e` evidence:

```text
model = M6_TG_compatibility_interaction
primary AUROC = 0.9956328125
geometry-only AUROC = 0.5270640625
source-only AUROC = 0.56811015625
wrong-predicate AUROC = 0.02664375
family scope = relative_vertical_dominant
```

Support/contact independent-validity freeze:

```text
strict predicate_x_class_pair capacity = 88
lying on strict capacity = 64
standing on strict capacity = 24
```

Calibration boundary:

```text
proper train-only probability ECE = 0.04658165053413088
Brier = 0.020503824238432555
calibrated p_rel/p_obs claim allowed = false
```

The corrected probability metrics show that the old ECE blocker was partly a
metric-definition issue. They do not establish a deployable reliability
posterior because the current target is still train-only `C_e`, not held-out
relation reliability with an observability/selective-decision target.

## Decision

Selected:

```text
freeze_current_scope_select_independent_target_source_decision
```

Reason:

- the cleanest H002 evidence is currently a `relative_vertical`-dominant
  train-only `C_e` result;
- support/contact pose-conditioned evidence remains useful as mechanism proof;
- support/contact independent-validity cannot be repaired from the same
  Open3DSG train-side source because strict predicate-class capacity is too
  small;
- the next bottleneck is target source and external validity, not model
  architecture.

## Next

```text
compatibility_dataset_v3_independent_target_source_decision_after_scope_synthesis
```

Candidate routes:

- relative-vertical held-out/Docker promotion as a scoped `C_e` method;
- human/visual/mesh audited support/contact reliability labels;
- cross-source agreement target using another relation source;
- stop H002 as mechanism evidence and return to the H001/GeoCalib paper path.

## Boundary

- Train-only synthesis.
- No validation/test usage.
- No row materialization.
- No learned smoke or model training.
- No calibrated `p_rel` / `p_obs` claim.
- No paper-level evidence.
- No H001 artifact modification.
