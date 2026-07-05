# Compatibility Dataset V3 Contract

Artifact root:

```text
artifacts/compatibility_dataset_v3_contract/
```

Status:

```text
status = h002_compatibility_dataset_v3_contract_ready
dataset = h002_compatibility_dataset_v3_predicate_conditioned
selected_route = same_geometry_multi_predicate
validation_errors = 0
next_todo = compatibility_dataset_v3_capacity_scan
```

## Purpose

v2 failed because the target was still solvable as generic geometry perturbation detection. The
v3 contract fixes the target so that predicate semantics must condition the interpretation of
geometry evidence:

```text
same G_e + predicate A = compatible
same G_e + predicate B = incompatible
```

The primary target is still `C_e = compatibility(T_e, G_e)`, not final human reliability `p_rel`.
`Z_e` source score/rank remains excluded from `C_e`.

## Primary Family

Initial family:

```text
relative_vertical: higher than / lower than
```

Primary row group:

```text
geometry_group_id = same directed subject/object pair
G_e = same numeric geometry evidence
T_e = different predicate text/label
labels = one positive, one opposite-predicate negative
```

Label rule:

```text
center_delta_z above frozen margin -> higher than positive, lower than negative
center_delta_z below frozen margin -> lower than positive, higher than negative
ambiguous vertical margin -> excluded from primary rows
```

Initial frozen margin contract:

```text
abs(center_delta_z) >= 0.10m
abs(normalized_center_delta_z) >= 0.20
```

The capacity scan may report sensitivity over a predeclared grid, but the final materialization
threshold must be frozen before learned smoke.

## Secondary And Deferred Families

`support_contact` remains secondary:

```text
standing on / lying on / supported by
```

Reason: v2 support/contact was dominated by distance and overlap shifts. It can become primary only
if the capacity scan or evidence probe finds role/orientation, contact direction, surface normal, or
visual/mesh evidence that can distinguish support predicates without falling back to generic
geometry perturbation.

Deferred:

- `proximity`: `close by` is likely distance-only unless paired with a stronger multi-predicate
  contrast.
- `attachment_like`: `attached to`, `hanging on`, `connected to` need stronger visual/mesh evidence
  before primary `C_e` use.

## Required Gates

The next materialization/smoke must pass:

- `same_geometry_group_integrity`: primary positive and negative rows share the same
  `geometry_feature_hash`.
- `balanced_same_group_labels`: each group has one compatible and one incompatible predicate row.
- `blocked_field_absence`: model views exclude labels, construction route, row role, raw-source
  predicate, hidden audit status, and group identifiers as features.
- `geometry_only_near_chance`: `G_e` alone should be near chance on same-geometry groups.
- `predicate_conditioning_gain`: `T_e + G_e` must beat `G_e`, `T_e`, and `Z_e` baselines.
- `wrong_predicate_degradation`: wrong predicate with the same geometry must degrade.
- `shuffled_geometry_degradation`: shuffled geometry must degrade.
- `source_shortcut_control`: source-only, rank-only, predicate-only, and object-pair probes remain
  near chance.

## Outputs

```text
dataset_contract.json
row_schema.json
family_contract.csv
gate_contract.csv
blocked_fields.csv
model_views.csv
smoke_protocol.json
summary.json
validation_errors.jsonl
report.md
```

## Boundary

This step:

- is train-only;
- does not materialize v3 rows;
- does not run learned smoke;
- does not use validation/test data;
- does not create paper-level evidence;
- does not modify H001 artifacts.

## Next

```text
compatibility_dataset_v3_capacity_scan
```
