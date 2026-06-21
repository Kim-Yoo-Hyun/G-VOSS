# H003 Smoke Protocol

Last updated: 2026-06-20 KST

## Status

- Stage: hypothesis smoke protocol.
- Uses: `04_dataset_contract.md`.
- First method target: M3 factorized reliability posterior.
- Second method target: M2 semantic-geometry consistency embedding.

## Goal

The smoke test asks:

> Can a deployable semantic-geometry reliability model detect counterfactual
> geometry inconsistency better than semantic-only or naive semantic-times-
> geometry scoring, without relying on hidden targets or trivial shortcuts?

This is not a paper-result protocol yet.

## Stage A: Dataset Sanity

Input:

- read-only row export following `04_dataset_contract.md`.
- one source at a time.
- one frozen split file.
- one frozen corruption manifest.

Checks:

- required schema fields are present.
- no target/proxy/reviewer label appears in deployable feature columns.
- all generated negatives have `counterfactual_group_id`.
- all counterfactuals remain in the same split as their original row.
- `unknown` labels are excluded from binary train/eval metrics.
- missing GT is never converted into a negative by default.

Pass condition:

```text
schema_errors = 0
leakage_errors = 0
split_group_errors = 0
```

## Stage B: Baselines

Run the following before any learned H003 method:

| Baseline | Input | Required Role |
| --- | --- | --- |
| `source_score_only` | source score/rank | Semantic-source lower bound. |
| `semantic_only` | predicate/object/source fields | Object-class and language-prior shortcut probe. |
| `geometry_only` | compact geometry + coverage | Geometry sufficiency probe. |
| `semantic_times_geometry` | source score x geometry score | Naive score-composition baseline. |
| `explicit_rule_score` | rule-derived geometry score/status | Strong rule-based diagnostic baseline. |

Expected diagnostic behavior:

- semantic-only and source-score-only should be relatively insensitive to
  geometry corruption.
- geometry-aware baselines should react to corruption.
- if semantic-only already performs near perfectly, the target likely has a
  shortcut and should not be used for method claims.

## Stage C: M3 Factorized Reliability Posterior

First H003 method:

```text
P(R_e = 1 | S_e, G_e, C_e, U_e, interactions)
```

Allowed models:

- logistic regression.
- calibrated gradient boosting.
- small MLP only if simpler models underfit.

Preferred first model:

```text
regularized logistic regression + calibration check
```

Reason:

- exposes coefficient/sign behavior.
- easier to debug leakage and shortcuts.
- strong enough to test whether coverage and uncertainty add value.

Train only on train split. Use dev split for smoke-gate decisions. Hold a test
split until the schema, corruption, model family, and thresholds are frozen.

## Stage D: M2 Consistency Embedding

M2 is promoted only after M3 passes Stage C.

Candidate first embedding:

```text
z_sem = f_sem(predicate, subject_label, object_label, source_score)
z_geo = f_geo(compact_geometry, predicate_family, coverage)
score = cosine_or_mlp(z_sem, z_geo)
loss = binary_consistency + margin(counterfactual_pair)
```

M2 must compare against M3, not only against semantic-only.

Promotion condition:

- improves hard-negative false-valid rate, calibration, or source-transfer over
  M3.
- does not collapse recall-retention if used for reranking.
- passes shortcut controls.

## Stage E: M5 Counterfactual Consistency Benchmark

Required corruption groups:

- wrong-pair same-scene.
- shuffled geometry same-family.
- subject/object swap.
- predicate-family flip.
- vertical order inversion for vertical relations.
- support/contact removal for support/contact relations.
- distance perturbation for proximity relations.

Metrics:

- mean score drop from original to corrupted row.
- hard-negative false-valid rate.
- AUROC/AUPRC for original-vs-corrupted discrimination.
- corruption-specific failure table.
- score-drop by predicate family.

Diagnostic expectation:

```text
score(original_valid) > score(counterfactual_corrupted)
```

This must hold within family and rank-matched slices, not only globally.

## Primary Metrics

Validity metrics:

- AUROC.
- AUPRC.
- Brier score.
- ECE.
- hard-negative false-valid rate.

Counterfactual metrics:

- mean corruption score drop.
- median corruption score drop.
- percent of corrupted rows whose score remains above the valid threshold.

Reranking metrics if a prediction-source output is used:

- `R@K`.
- `Violation@K`.
- `Delta R`.
- `Delta V`.
- recall retention.

Use K grid:

```text
K = {5, 10, 20, 50, 100}
```

`K=1` is sanity-check only.

## Smoke Pass Conditions

These thresholds are smoke gates, not paper claims.

Dataset gate:

- `schema_errors = 0`.
- `leakage_errors = 0`.
- `split_group_errors = 0`.

M3 gate:

- factorized posterior improves hard-negative false-valid rate over
  `source_score_only` by at least 10 percent relative on dev.
- factorized posterior does not underperform both `geometry_only` and
  `explicit_rule_score` on AUPRC.
- ECE is not worse than `semantic_times_geometry` by more than 0.03 absolute.
- no shortcut control shows semantic-only matching the factorized posterior
  within 1 pp on every validity and hard-negative metric.

M2 promotion gate:

- M2 improves over M3 on at least two of:
  hard-negative false-valid rate, counterfactual score drop, AUPRC, ECE, or
  source-held-out transfer.
- M2 does not reduce recall-retention by more than 3 pp if used for reranking.
- embedding separation remains in same-family and same-rank-band slices.

Falsification:

- semantic-only matches learned methods across hard-negative controls.
- explicit rule score beats M3/M2 on all reliability and calibration metrics.
- improvements disappear after scene-level split.
- generated negatives are separable only because of easy corruption artifacts.

## Terminology Decision

H003 should use its own terminology:

- `dual-channel edge representation`.
- `factorized reliability posterior`.
- `semantic-geometry consistency embedding`.
- `counterfactual consistency benchmark`.

H002's `RGA` terminology can be cited as a prior branch concept, but H003 should
not rely on `RGA` as the method name.

## Next Implementation Gate

Before writing model code, create a source inventory and exact path whitelist:

- input row sources.
- allowed deployable fields.
- target fields.
- ignored hidden/proxy fields.
- output directory for H003 smoke artifacts.

