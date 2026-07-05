# H002 Independent Target-Source Decision After Scope Synthesis

Default artifact:

```text
artifacts/compatibility_dataset_v3_independent_target_source_decision_after_scope_synthesis/
```

Status:

```text
status = h002_compatibility_dataset_v3_independent_target_source_decision_selected
selected_path = select_support_contact_visual_mesh_human_audit_with_size_containment_probe
validation_errors = 0
next_todo = compatibility_dataset_v3_support_contact_visual_mesh_audit_target_plan
```

## Purpose

This stage decides the next independent target source after the current H002 scope synthesis. It
does not materialize new rows or run a learned smoke. It chooses which target-source route should
be planned next.

## Decision

Selected main route:

```text
support_contact_human_visual_mesh_audit_target
```

Rationale:

- The current blocker is target-source independence, not model capacity.
- `relative_vertical` is clean but too narrow to carry a broad H002 reliability claim by itself.
- `support_contact` has enough raw family mass and mesh/pose/contact evidence, but the current
  Open3DSG train-side independent-validity target is shortcut-prone.
- Additional relation types are useful only as bounded probes unless they also solve target
  independence.

## Route Decision

| Route | Verdict | Reason |
| --- | --- | --- |
| `support_contact_human_visual_mesh_audit_target` | `selected_main` | Directly addresses the current H002 blocker: independent reliability labels with visual/mesh evidence. |
| `relation_type_expansion_only` | `reject_as_main_select_optional_probe` | More relation types do not fix target independence by themselves. |
| `relative_vertical_heldout_docker_promotion` | `defer_not_main` | Cleanest current `C_e` evidence, but too narrow as the next main route. |
| `cross_source_agreement_target` | `defer_secondary` | Useful later, but source disagreement is not automatically reliability GT. |
| `stop_h002_as_mechanism_evidence` | `reject_for_now` | Still possible as fallback, but support/contact audit is the best next test. |

## Selected Target Contract

Selected predicates:

```text
lying on
standing on
supported by
```

Primary target axes:

- `C_e`: predicate-geometry compatibility.
- `Q_e`: observability / evidence quality.
- `p_obs`: whether evidence is sufficient to decide.
- `p_rel`: relation reliability given observable evidence.

Required next gates before learned smoke:

- accept/reject class mass must pass per primary predicate or controlled pair family;
- predicate, subject class, object class, and `predicate_x_class_pair` shortcut probes must pass;
- visual/mesh labels must be locked before hidden/source metadata join;
- hidden construction fields must remain outside the model-safe view;
- `Q_e` / abstain must remain separated from `p_rel` accept/reject;
- validation/test rows must not be used for target construction.

## Optional Relation-Type Probes

These are not selected as the main route.

| Probe | Predicates | GT total | Role | Risk |
| --- | --- | ---: | --- | --- |
| `size_relative` | `bigger than`; `smaller than` | 1822 | optional feasibility probe | too close to `higher/lower`, weak novelty as main |
| `containment_inclusion` | `standing in`; `lying in`; `build in`; `part of`; `belonging to`; `cover`; `hanging in` | 847 | high-risk optional probe | sparse labels and object/container-class shortcut |
| `leaning_contact_orientation` | `leaning against` | 184 | future probe | low GT mass, needs normals/orientation |
| `relative_horizontal` | `left`; `right`; `front`; `behind` | 36944 | deferred | reference-frame ambiguity |
| `identity_symmetry` | `same as`; `same symmetry as` | 2688 | not recommended for H002 main | identity/shape matching rather than relation compatibility |

## Boundary

- Train-only decision artifact.
- No validation/test usage.
- No row materialization.
- No learned smoke or model training.
- No paper-level evidence.
- No H001 artifact modification.

## Next

```text
compatibility_dataset_v3_support_contact_visual_mesh_audit_target_plan
```
