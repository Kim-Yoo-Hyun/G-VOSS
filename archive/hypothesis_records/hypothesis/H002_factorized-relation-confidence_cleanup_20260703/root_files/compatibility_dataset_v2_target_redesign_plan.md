# Compatibility Dataset V2 Target Redesign Plan

Artifact root:

```text
artifacts/compatibility_dataset_v2_target_redesign_plan/
```

Status:

```text
status = h002_compatibility_dataset_v2_target_redesign_plan_ready
selected_route = v3_same_geometry_multi_predicate_contract
validation_errors = 0
next_todo = compatibility_dataset_v3_contract
```

## Decision

Do not repair v2 by:

- adding more generated negatives;
- using a stronger combiner first;
- promoting the current 400-row smoke as compatibility evidence;
- moving directly to human reliability labels before fixing `C_e`.

The failure analysis showed a target-identifiability problem. The current v2 target is solved as
generic geometry perturbation detection, not predicate-conditioned compatibility.

Selected route:

```text
h002_compatibility_dataset_v3_predicate_conditioned
same_geometry_multi_predicate contrast
```

## Core Principle

The same or near-identical `G_e` must appear with multiple `T_e` alternatives.

This makes geometry-only insufficient:

```text
same G_e + predicate A = positive
same G_e + predicate B = negative
```

Then a model has to use the predicate semantics to decide which geometry evidence matters.

## Primary Initial Family

Start with:

```text
relative_vertical: higher than / lower than
```

Reason:

- the predicate pair is directional and mutually exclusive;
- the same object-pair geometry can be paired with both predicates;
- only one predicate should agree with the signed vertical order;
- `G_e` alone cannot assign two labels to the same geometry group.

Contract:

```text
group = same directed pair geometry
positive = predicate agrees with signed vertical order
negative = opposite predicate on the same directed pair geometry
margin = fixed before materialization
```

This is an identifiability proof target, not yet a broad relation-reliability target.

## Secondary Family

Keep support/contact as secondary:

```text
support_contact: standing on / lying on / supported by
```

Reason:

- v2 support/contact is dominated by distance and overlap shifts;
- current numeric `G_e` does not distinguish role-specific predicates well enough;
- `standing on` vs `lying on` likely needs pose/orientation, contact direction, surface normals,
  or visual/mesh evidence;
- `supported by` is more generic than the other support predicates and can blur labels.

Support/contact can be promoted only after an evidence probe shows that role/orientation or
visual/mesh evidence exists.

## Rejected Routes

| Route | Decision | Reason |
| --- | --- | --- |
| more v2 rows | rejected | repeats generic geometry perturbation target |
| stronger combiner now | rejected | failure is target identifiability, not capacity |
| human reliability now | deferred | useful later, but `C_e` target must be fixed first |
| proximity as primary | rejected for now | likely collapses into geometry-only distance verifier |

## Required Gates For V3

The next v3 contract must enforce:

```text
same_geometry_group_integrity
geometry_only_near_chance
predicate_conditioning_gain
wrong_predicate_degradation
source_semantic_shortcut_control
family_specific_reporting
```

The next smoke is promising only if:

```text
T_e + G_e > G_e-only
wrong-T same-G < T_e + G_e
source-only / predicate-only / object-pair-only remain near chance
```

If these fail, the result stays diagnostic-only.

## Boundary

This plan:

- is train-only;
- does not materialize a new dataset;
- does not run learned smoke;
- does not use validation/test data;
- does not create paper-level evidence;
- does not modify H001 artifacts.

## Next

```text
compatibility_dataset_v3_contract
```
