# H002 Learned Smoke Runner V1

Date: 2026-06-25 KST

## Purpose

이 문서는 `prototype_dataset_v1` 위에서 실행한 첫 train-internal learned smoke를 기록한다.
목표는 paper-level 성능을 주장하는 것이 아니라, H002의 새 방향인 predicate-geometry
compatibility learning이 source-only, geometry-rule, predicate/family shortcut보다
의미 있는 신호를 갖는지 확인하는 것이다.

## Runner

```text
tools/learned_smoke_runner_v1.py
```

Default command:

```bash
python hypothesis/CAND-001/H002_factorized-relation-confidence/tools/learned_smoke_runner_v1.py
```

Input:

```text
artifacts/prototype_dataset_v1/
```

Output:

```text
artifacts/learned_smoke_v1/
```

The runner uses pure-Python logistic regression because the local environment does not assume
`sklearn` or `numpy`. It uses grouped train-internal folds only.

## Tasks

### Task A: Compatibility

Binary target:

```text
compatibility_label = positive vs counterfactual_negative
```

Rows:

```text
134 = 67 positive + 67 counterfactual negative
```

This is the main smoke for:

```text
C_e = compatibility(T_e, G_e)
```

### Task B: Observability

Binary target:

```text
observable vs limited/insufficient
```

Rows:

```text
694
```

This approximates:

```text
p_obs = P(evidence is sufficient to decide)
```

### Task C: Reliability

Binary target:

```text
accept vs reject
```

Rows:

```text
543 = 101 accept + 442 reject
```

This approximates:

```text
p_rel = P(relation is reliable | observable evidence)
```

## Model Views

| Name | Input |
| --- | --- |
| `M0_intercept` | intercept only |
| `M1_source_only_Z` | source score, rank, source id |
| `M2_semantic_source_TZ` | semantic content plus source confidence |
| `M3_geometry_rule_pgeom` | H001-style `p_geom_valid` rule score only |
| `M4_geometry_only_G` | predicate-independent numeric geometry fields |
| `M5_compatibility_TG` | semantic content plus geometry evidence, no `Z_e` |
| `M6_factorized_TZGQ` | semantic, source, geometry, and observability features |
| `S1_predicate_family_shortcut` | predicate and family only |
| `S2_source_rank_shortcut` | source score/rank scalars only |

## Current Result

Result artifact:

```text
artifacts/learned_smoke_v1/summary.json
```

Key metrics:

```text
Task A rows = 134
M1 source-only Z AUROC = 0.4885
M2 semantic+source T+Z AUROC = 0.9668
M3 p_geom_valid AUROC = 0.5507
M4 geometry-only G AUROC = 0.7634
M5 compatibility T+G AUROC = 0.9728
M6 factorized T+Z+G+Q AUROC = 0.9748
S1 predicate/family shortcut AUROC = 0.5978
S2 source/rank shortcut AUROC = 0.5043
```

Other task metrics:

```text
Task B M6 observability AUROC = 1.0000
Task C M6 reliability AUROC = 0.9648
two-head accept/reject/abstain macro-F1 = 0.5062
validation_errors = 0
```

Gate result:

```text
gate_1_dataset_sanity = pass
gate_2_learned_compatibility_signal = pass
gate_3_observability_signal = pass
gate_4_reliability_signal = pass
overall = learned_smoke_promising_but_needs_family_shortcut_review
```

Family-specific Task A compatibility:

```text
relative_vertical M5 AUROC = 0.9379, n = 35
support_contact M5 AUROC = 0.9824, n = 99
```

## Interpretation

The learned smoke supports the H002 design direction:

```text
source confidence alone is not enough,
geometry-only evidence has independent signal,
and T_e + G_e compatibility is stronger than predicate/family shortcut probes.
```

However, this is still hypothesis-stage evidence. `M2_semantic_source_TZ` is also very strong,
which means semantic label/rank structure remains a serious shortcut risk. The result should be
read as evidence that compatibility learning is worth continuing, not as paper-ready proof.

## Boundary

This runner:

- uses train-internal grouped folds only;
- does not use validation or test data;
- does not train a paper model;
- does not produce paper-level evidence;
- is useful for direction selection and failure analysis only.

## Follow-Up

The next TODO selected by this runner was:

```text
attachment_numeric_geometry_materialization_v1
```

That step is now complete. The current branch-level next TODO is:

```text
attachment_numeric_geometry_smoke_v1
```

Rationale:

- `support_contact` and `relative_vertical` already have usable numeric `G_e`.
- `attachment_deferred` now has a separate numeric geometry artifact under
  `artifacts/attachment_numeric_geometry_v1/`.
- The next bottleneck is therefore better `G_e`, not a stronger posterior combiner.
