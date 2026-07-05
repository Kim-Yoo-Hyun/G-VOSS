# Compatibility Learning Scope Plan V1

Date: 2026-06-26 KST

## Purpose

This step fixes the method-level scope for H002 after the attachment positive-anchor target was
frozen as diagnostic-only. The goal is not to train a stronger posterior, but to decide which
relation families can support `C_e = compatibility(T_e, G_e)` under the current evidence and
shortcut-control requirements.

The key decision is:

```text
H002 v1 primary scope = support_contact + relative_vertical
H002 v1 diagnostic hard family = attachment_like
future generality = proximity
deferred = relative_horizontal + containment
```

## Runner

```bash
python hypothesis/CAND-001/H002_factorized-relation-confidence/tools/compatibility_learning_scope_plan_v1.py
```

Output root:

```text
artifacts/compatibility_learning_scope_plan_v1/
```

Main outputs:

- `summary.json`
- `scope_plan.json`
- `family_scope.csv`
- `evidence_axis_contract.json`
- `control_contract.json`
- `report.md`
- `validation_errors.jsonl`

## Result

```text
status = h002_compatibility_learning_scope_plan_ready
selected_scope = primary_support_contact_relative_vertical_attachment_diagnostic
posterior_smoke_allowed = false
validation_errors = 0
next_todo = compatibility_dataset_v2_contract
```

Current prototype family counts:

```text
support_contact rows = 99
relative_vertical rows = 35
attachment_deferred rows = 560

support_contact compatibility = 50 positive / 49 counterfactual_negative
relative_vertical compatibility = 17 positive / 18 counterfactual_negative
```

## Family Scope

| Family | Status | Role |
| --- | --- | --- |
| `support_contact` | `primary_v1` | Main compatibility-learning family with contact/support numeric geometry. |
| `relative_vertical` | `primary_v1_needs_expansion` | Main directional-geometry family, but needs v2 row expansion and flip/swap controls. |
| `attachment_like` | `diagnostic_hard_family` | Use for `Q_e`, observability, failure taxonomy, and future verified positives only. |
| `proximity` | `future_generality` | Add later after primary scope is stable; no-GT negatives are unsafe. |
| `relative_horizontal` | `deferred` | Requires reference-frame contract. |
| `containment` | `deferred` | Requires containment-specific geometry and completeness checks. |

## Why This Scope

`support_contact` is the strongest current primary family because it already has numeric
predicate-independent geometry evidence from raw witness fields, enough balanced compatibility rows,
and relation-specific physical meaning.

`relative_vertical` is still important because it tests whether `T_e` changes interpretation of
the same geometry. However, the current row count is smaller, so the next dataset contract must
expand it and include:

- `higher than` / `lower than` predicate flip;
- subject/object swap;
- same-rank and same-coverage hard negatives;
- source-rank and predicate shortcut probes.

`attachment_like` is not removed from H002. It is frozen as diagnostic because the target-first
repair route produced class mass but not independent target identifiability. Its packets remain
useful for:

- `Q_e` and observability;
- visible/mesh evidence failure taxonomy;
- hard-family examples;
- future manually verified positives.

It must not be used for current `p_rel` posterior smoke or paper-level reliability GT.

## Evidence Axis Contract

`T_e` may contain predicate, relation family, subject/object class, and class text embeddings.

`Z_e` may contain source score, source rank, source id, and source calibration metadata. It can be
used by source baselines and final `p_rel`, but not by `C_e`.

`G_e` may contain only predicate-independent object-pair geometry: metric features, raw witness v2
numeric fields, point/mesh geometry when materialized, contact/support/vertical/proximity geometry
features. It must not contain predicate, source score/rank, audit label, GT match, or construction
key.

`C_e` is:

```text
compatibility(T_e, G_e)
```

and must not use `Z_e`.

`Q_e` may contain coverage, missing geometry, point/mesh/view availability, asset quality, and
evidence conflict. It should control abstain/selective decision, not relation truth directly.

H001 `p_geom_valid` remains allowed only as:

- geometry-only baseline;
- teacher or auxiliary supervision;
- ablation input in a separately named condition.

It is not the final H002 reliability score.

## Required Controls

Minimum controls for the next H002 dataset/smoke:

- source-only `Z_e`;
- semantic+source `T_e + Z_e`;
- geometry-only `G_e`;
- compatibility `T_e + G_e` without `Z_e`;
- full factorized decision;
- predicate/family shortcut;
- source rank band shortcut;
- endpoint label-pair shortcut;
- scan/instance hidden probe;
- hidden construction proxy probe;
- wrong-pair geometry;
- shuffled geometry;
- predicate flip or subject/object swap for directional relations.

## Next

The next step should define the concrete v2 dataset contract under this scope.

```text
compatibility_dataset_v2_contract
```

## Boundary

- Train-only H002 planning artifact.
- No validation/test usage.
- No new posterior trained.
- No paper-level evidence promotion.
- H001 artifacts are not modified.
