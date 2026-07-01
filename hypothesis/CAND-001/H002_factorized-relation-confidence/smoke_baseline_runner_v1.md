# H002 Smoke Baseline Runner V1

Date: 2026-06-25 KST

## Purpose

이 문서는 `smoke_baseline_plan_v1.md`의 첫 실행 runner를 기록한다. 목표는 learned model을
바로 학습하는 것이 아니라, materialized prototype dataset이 source/geometry/shortcut
baseline에서 어떤 신호를 보이는지 진단하는 것이다.

## Runner

```text
tools/smoke_baseline_runner_v1.py
```

Default command:

```bash
python hypothesis/CAND-001/H002_factorized-relation-confidence/tools/smoke_baseline_runner_v1.py
```

Input:

```text
artifacts/prototype_dataset_v1/
```

Output:

```text
artifacts/smoke_baseline_v1/
```

## What This Runner Does

The runner computes deterministic diagnostic baselines:

- `B0_constant_0_5`
- `B1_source_score`
- `B1_rank_inverse`
- `B3_p_geom_valid`
- `B4_semantic_x_p_geom_valid`
- `B5_generic_geometry_proxy`
- `B6_relation_conditioned_geometry_proxy`
- `B7_concat_proxy`
- `B8_no_Q_factorized_proxy`
- `B9_full_two_head_proxy`

It also computes shortcut probes:

- family prevalence probe;
- predicate prevalence probe;
- source rank-band prevalence probe;
- source-id prevalence probe;
- geometry-feature-count prevalence probe.

## Tasks

### Task A: Compatibility

Rows:

```text
compatibility_label = positive vs counterfactual_negative
```

Current scope:

```text
support_contact + relative_vertical
```

The attachment rows remain `unknown` for compatibility because numeric attachment `G_e` is not yet
materialized.

### Task B: Observability

Rows:

```text
observable vs limited/insufficient
```

This task uses a deterministic `Q_e` proxy only.

### Task C: Reliability

Rows:

```text
accept vs reject
accept / reject / abstain
```

This is diagnostic because current `p_rel` and `p_obs` are not learned.

## Current Result

The default runner has been executed once.

Result artifact:

```text
artifacts/smoke_baseline_v1/summary.json
```

The exact metrics are owned by:

- `artifacts/smoke_baseline_v1/metrics_by_task.json`
- `artifacts/smoke_baseline_v1/metrics_by_family.json`
- `artifacts/smoke_baseline_v1/counterfactual_score_drop.json`
- `artifacts/smoke_baseline_v1/shortcut_probe_metrics.json`
- `artifacts/smoke_baseline_v1/report.md`

Current key metrics:

```text
Task A rows = 134
source-only AUROC = 0.5008
p_geom_valid AUROC = 0.5257
semantic_score * p_geom_valid AUROC = 0.5317
generic geometry proxy AUROC = 0.6298
relation-conditioned geometry proxy AUROC = 0.6681
concat proxy AUROC = 0.6349
full two-head proxy AUROC = 0.6234
mean paired drop for relation-conditioned geometry proxy = 0.1411
```

Gate result:

```text
gate_1_dataset_sanity = pass
gate_2_compatibility_signal = pass
gate_3_observability_signal = pass
gate_4_factorized_benefit = pass
overall = ready_for_learned_smoke
```

Family caveat:

```text
support_contact relation-conditioned geometry AUROC = 0.7371
relative_vertical relation-conditioned geometry AUROC = 0.5163
```

This means the first signal is not uniformly strong across families. The learned smoke must report
family-specific results and predicate/family shortcut probes.

## Boundary

This runner:

- uses train-only rows;
- does not train a model;
- does not use validation/test data;
- does not produce paper-level evidence;
- is a diagnostic smoke runner only.

## Next TODO

The deterministic smoke selected and enabled the learned smoke step:

```text
learned_smoke_runner_v1
```

That step is now complete. The current branch-level next TODO is:

```text
attachment_numeric_geometry_materialization_v1
```
