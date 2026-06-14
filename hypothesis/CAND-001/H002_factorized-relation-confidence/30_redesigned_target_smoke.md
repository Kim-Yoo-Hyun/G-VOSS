# H002 Redesigned Target Smoke

Last updated: 2026-06-13

## Purpose

`29_target_redesign.md`에서 만든 target v2가 이전 strict/weak target처럼 target
construction shortcut으로 trivially 풀리는지 확인했다.

이 단계의 목적은 posterior 성능을 주장하는 것이 아니다. 목적은 target v2가 human
confirmation을 진행할 가치가 있는지 판단하는 train-only plumbing diagnostic이다.

Core check:

```text
Does the redesigned target remain predictable after direct target identity
features are removed?
```

## Input Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/target_redesign/strict_proximity_informativeness.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/target_redesign/weak_satisfied_actionability.jsonl
```

Input counts:

| Target | Rows | Positive | Negative |
| --- | ---: | ---: | ---: |
| `strict_proximity_informativeness` | 27 | 16 | 11 |
| `weak_satisfied_actionability` | 87 | 76 | 11 |

Boundary:

```text
split = train_only
validation usage = false
paper result = false
human confirmed labels = false
posterior claim allowed = false
```

## Tool

Added:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/redesigned_target_smoke.py
```

Command:

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/redesigned_target_smoke.py
```

Status:

```text
ready_plumbing_only
```

Implementation note:

- Pure-Python logistic regression from `factor_smoke.py`.
- No `sklearn` / `numpy` dependency.
- No validation tuning.
- 5-fold train-internal crossfit only.

## Output Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/redesigned_target_smoke/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/redesigned_target_smoke/metrics.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/redesigned_target_smoke/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/redesigned_target_smoke/predictions_*.jsonl
```

## Feature Views

| View | Role |
| --- | --- |
| `full_factorized` | original factorized view, leakage-risk diagnostic only |
| `drop_direct_identity` | removes geometry status, predicate family/label/source, RGA flags, interactions |
| `drop_direct_identity_rank` | additionally removes semantic rank / normalized rank score |
| `safe_continuous` | only semantic raw score and continuous geometry evidence |
| `geometry_continuous_only` | only continuous geometry evidence |
| `semantic_raw_only` | only source semantic raw confidence |

Direct target identity features removed include:

```text
geometry_status / geometry_status_* one-hot
predicate_family / predicate_label / source_id
top100_and_unsatisfied / tail_gt100_and_satisfied
top50_semantic / top100_semantic
semantic_geometry_disagreement_score / underconfidence_score
semantic_score_norm_minus_p_geom_valid
family-specific p_geom interaction terms
```

## Train-Internal 5-Fold Metrics

These are train-only diagnostics, not held-out results.

| Target | View | AUROC | AUPRC | Brier | Accuracy@0.5 |
| --- | --- | ---: | ---: | ---: | ---: |
| strict | `full_factorized` | 0.8864 | 0.9339 | 0.1434 | 0.8519 |
| strict | `drop_direct_identity` | 0.8864 | 0.9217 | 0.1420 | 0.8519 |
| strict | `drop_direct_identity_rank` | 0.8409 | 0.8975 | 0.1725 | 0.7407 |
| strict | `safe_continuous` | 0.8409 | 0.8975 | 0.1725 | 0.7407 |
| strict | `geometry_continuous_only` | 0.8523 | 0.8986 | 0.1828 | 0.7778 |
| strict | `semantic_raw_only` | 0.5483 | 0.7204 | 0.2364 | 0.5926 |
| weak | `full_factorized` | 0.9187 | 0.9887 | 0.0741 | 0.8736 |
| weak | `drop_direct_identity` | 0.9163 | 0.9884 | 0.0751 | 0.8621 |
| weak | `drop_direct_identity_rank` | 0.9115 | 0.9877 | 0.0770 | 0.8736 |
| weak | `safe_continuous` | 0.9115 | 0.9877 | 0.0770 | 0.8736 |
| weak | `geometry_continuous_only` | 0.8983 | 0.9856 | 0.0842 | 0.8736 |
| weak | `semantic_raw_only` | 0.8906 | 0.9855 | 0.0961 | 0.8736 |

## Probe Metrics

Probe metrics help interpret whether a single score trivially solves the target.

| Target | Probe | AUROC | AUPRC | Interpretation |
| --- | --- | ---: | ---: | --- |
| strict | `semantic_score_raw` | 0.6108 | 0.8444 | weak signal only |
| strict | `semantic_score_norm` | 0.6051 | 0.7808 | rank no longer solves target |
| strict | `p_geom_valid` | 0.0966 | 0.4202 | raw geometry probability is anti-aligned |
| strict | `consistency_score` | 0.5000 | 0.7691 | no ranking signal |
| weak | `semantic_score_raw` | 0.9181 | 0.9927 | weak target remains source/family-biased |
| weak | `semantic_score_norm` | 0.9169 | 0.9887 | weak target still has rank/selection bias |
| weak | `p_geom_valid` | 0.2440 | 0.8208 | p_geom alone does not explain target |
| weak | `consistency_score` | 0.8816 | 0.9878 | geometry proxy still correlates with weak labels |

## Interpretation

### Strict Proximity Informativeness

This target is less shortcut-prone than the previous strict target.

Evidence:

- direct target identity removal does not collapse the model.
- rank is no longer a strong single-score solution.
- `p_geom_valid` alone is anti-aligned with the target.
- the target is no longer `satisfied vs unsatisfied`; all rows are
  geometry-satisfied proximity rows.

But it is still too small:

```text
N = 27
positive = 16
negative = 11
```

So this result means:

```text
The redesigned strict target is plausible enough to justify human confirmation.
```

It does not mean:

```text
The factorized posterior improves relation reliability.
```

### Weak Satisfied Actionability

The weak target is still not a clean method target.

Reasons:

- positive rows span `proximity`, `relative_vertical`, and `support_contact`.
- negative rows exist only in `proximity`.
- `semantic_raw_only` and `semantic_score_norm` probes are already high.
- therefore family/source selection bias remains.

Use:

```text
sensitivity-only
```

Do not use:

```text
main posterior target
```

## Decision

Current decision:

```text
Proceed to human confirmation protocol before any further posterior claim.
```

Rationale:

- strict target v2 removes the strongest target-construction shortcut.
- it gives a nontrivial but small signal.
- machine-assisted labels are not enough for paper-level method evidence.
- the next useful work is not more fitting; it is label confirmation.

## Current Boundary

Established:

- redesigned target smoke is executable.
- direct target identity feature controls are implemented.
- strict target is not trivially solved by semantic rank or p_geom alone.
- weak target remains family-confounded.
- no validation rows were used.

Not established:

- human-confirmed reliability labels.
- posterior advantage over baselines.
- cross-scene or cross-source generalization.
- validation/test performance.
- paper-level posterior result.

## Next TODO

Next document:

```text
31_human_confirmation_protocol.md
```

Required next work:

- define human confirmation fields for target v2.
- prioritize `strict_proximity_informativeness` 27 rows first.
- decide whether all 87 weak rows need confirmation or only after strict target
  passes.
- define acceptance criteria for treating labels as posterior-training evidence.
- keep posterior fitting blocked for claims until this confirmation protocol is
  complete.
