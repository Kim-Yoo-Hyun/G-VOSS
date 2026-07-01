# H002 Scope Synthesis After Attachment Observability Diagnostic Freeze

## Result

```text
artifact_root = artifacts/compatibility_dataset_v3_scope_synthesis_after_attachment_observability_diagnostic_freeze/
status = h002_compatibility_dataset_v3_scope_synthesis_after_attachment_observability_diagnostic_freeze_ready
selected_path = scope_sufficient_after_r7_freeze_select_paper_framework_readiness_review
validation_errors = 0
next_todo = compatibility_dataset_v3_paper_framework_readiness_review_after_route_specific_probes
```

## Decision

The current H002 route coverage is sufficient for a hypothesis-stage
relation-aware evidence routing framework. Do not add another relation family
now.

R7 `attached to` / `hanging on` / `connected to` remains in the route taxonomy as
an observability-heavy diagnostic/future boundary, but the current class-pair
repair artifact is not main learned evidence.

## Final Route Boundary

| Scope | Families | Status |
| --- | --- | --- |
| main mechanism evidence | `relative_vertical`, `size_relative`, `relative_horizontal`, `support_contact` | retain |
| geometry-easy control | `close by` | retain as control/generality route |
| superordinate decomposition | `supported by` | retain as diagnostic |
| observability-heavy boundary | `attached to`, `hanging on`, `connected to` | current artifact diagnostic-only |
| future/separate routes | containment, `cover`, `leaning against`, identity/symmetry, semantic/structural | defer |

## Interpretation

R7 freeze does not weaken the main H002 mechanism claim. It sharpens the claim
boundary:

```text
H002 is not an all-relation solved reliability method.
H002 is a relation-aware evidence-routing framework.
```

The current allowed claim remains train-only and mechanism-level:

```text
Different relation families require different evidence routes.
Clean signed/size/frame-aware families support T_e x G_e compatibility;
support/contact is a challenging compatibility route with caveat;
proximity is geometry-decidable; and attachment-like relations require
observability-aware evidence that the current proxy target does not provide.
```

## Blocked Claims

- all-family generality
- paper-level performance
- held-out/test reliability
- calibrated `p_rel` / `p_obs`
- R7 learned reliability on the current artifact
- support/contact fully solved

## Boundary

- train-only scope synthesis
- no validation/test usage
- no H001 artifact modification
- no new labels
- no row materialization
- no learned smoke
- no paper-level evidence claim

## Next

Run `compatibility_dataset_v3_paper_framework_readiness_review_after_route_specific_probes`.
