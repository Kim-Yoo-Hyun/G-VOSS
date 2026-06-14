# H002 Shortcut Control

Last updated: 2026-06-12

## Purpose

`27_factor_smoke.md`에서 strict target이 사실상 `HL vs LH` shortcut으로 풀린다는
문제가 확인됐다. 이 문서는 H002 posterior smoke가 relation reliability를 학습하는지,
아니면 target construction을 재구성하는지 확인하기 위해 shortcut-controlled feature
views를 실행한 결과를 기록한다.

핵심 질문:

```text
Can the current target still be predicted after removing RGA construction shortcuts?
```

결론부터 말하면, 현재 target은 아직 독립적인 relation reliability target이 아니다.
특히 strict target은 deterministic status와 rank shortcut을 제거해도 continuous geometry
evidence만으로 거의 완벽히 분리된다.

## Input Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/factor_dataset/strict_smoke.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/factor_dataset/weak_smoke.jsonl
```

Input counts:

| Target | Rows | Positive | Negative |
| --- | ---: | ---: | ---: |
| strict | 93 | 48 | 45 |
| weak | 132 | 76 | 56 |

## Tool

Added:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/factor_shortcut_control.py
```

Command:

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/factor_shortcut_control.py
```

Status:

```text
ready_target_not_independent
```

Boundary:

```text
split = train_only
validation usage = false
paper result = false
human confirmed labels = false
```

## Output Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/factor_shortcut_control/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/factor_shortcut_control/metrics.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/factor_shortcut_control/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/factor_shortcut_control/predictions_*.jsonl
```

## Controlled Feature Views

| View | Control |
| --- | --- |
| `full_factorized` | original factorized feature view |
| `drop_direct_rga_shortcuts` | remove explicit RGA shortcut/interactions |
| `drop_direct_and_status` | remove explicit shortcuts and deterministic geometry/coverage status |
| `drop_direct_status_rank` | additionally remove semantic rank/top-K fields |
| `drop_direct_status_rank_category` | additionally remove predicate label/family/source categorical fields |
| `continuous_core` | only continuous semantic raw score and continuous geometry evidence |
| `semantic_raw_only` | only source semantic raw confidence |
| `geometry_continuous_only` | only continuous geometry evidence without deterministic geometry status |

Shortcut keys controlled in this stage include:

```text
top100_and_unsatisfied
tail_gt100_and_satisfied
semantic_geometry_disagreement_score
underconfidence_score
absolute_disagreement
semantic_score_norm_minus_p_geom_valid
geometry_status / geometry_status_* one-hot fields
coverage_state / covered_checkable / covered_and_uncertain
rank_in_context / predicate_rank_for_pair / top50_semantic / top100_semantic
semantic_score_norm
predicate_label / predicate_family / source_id
```

## Train-Internal 5-Fold Metrics

This table is train-only and diagnostic. It must not be read as held-out evidence.

| Target | View | AUROC | AUPRC | Brier | ECE-5 | Accuracy@0.5 |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| strict | `full_factorized` | 1.0000 | 1.0000 | 0.0003 | 0.0120 | 1.0000 |
| strict | `drop_direct_rga_shortcuts` | 1.0000 | 1.0000 | 0.0003 | 0.0144 | 1.0000 |
| strict | `drop_direct_and_status` | 1.0000 | 1.0000 | 0.0015 | 0.0249 | 1.0000 |
| strict | `drop_direct_status_rank` | 1.0000 | 1.0000 | 0.0027 | 0.0351 | 1.0000 |
| strict | `drop_direct_status_rank_category` | 1.0000 | 1.0000 | 0.0035 | 0.0450 | 1.0000 |
| strict | `continuous_core` | 1.0000 | 1.0000 | 0.0035 | 0.0455 | 1.0000 |
| strict | `semantic_raw_only` | 0.9785 | 0.9844 | 0.0911 | 0.0771 | 0.8817 |
| strict | `geometry_continuous_only` | 1.0000 | 1.0000 | 0.0066 | 0.0624 | 1.0000 |
| weak | `full_factorized` | 0.9746 | 0.9818 | 0.0585 | 0.0288 | 0.9167 |
| weak | `drop_direct_rga_shortcuts` | 0.9746 | 0.9818 | 0.0586 | 0.0285 | 0.9167 |
| weak | `drop_direct_and_status` | 0.9695 | 0.9781 | 0.0599 | 0.0275 | 0.9167 |
| weak | `drop_direct_status_rank` | 0.9650 | 0.9748 | 0.0605 | 0.0266 | 0.9167 |
| weak | `drop_direct_status_rank_category` | 0.9643 | 0.9734 | 0.0633 | 0.0265 | 0.9167 |
| weak | `continuous_core` | 0.9495 | 0.9620 | 0.0689 | 0.0567 | 0.9167 |
| weak | `semantic_raw_only` | 0.8057 | 0.7250 | 0.1540 | 0.1391 | 0.7652 |
| weak | `geometry_continuous_only` | 0.9610 | 0.9715 | 0.0646 | 0.0355 | 0.9167 |

## Interpretation

### Strict Target

Strict target is not independent.

Even after removing:

- explicit RGA shortcut flags,
- deterministic `geometry_status`,
- semantic rank/top-K,
- predicate label/family/source category,

the `continuous_core` view still reaches AUROC/AUPRC `1.0/1.0`. The
`geometry_continuous_only` view also reaches `1.0/1.0`.

This means strict target is still recoverable from continuous geometry residual
signals. That is expected because strict negative is `semantic_overconfidence`
with geometry-unsatisfied rows and strict positive is `true_underconfidence`
with geometry-satisfied rows.

Therefore strict target currently tests:

```text
Can the model reconstruct RGA satisfied-vs-unsatisfied structure?
```

It does not yet test:

```text
Can the model predict relation reliability beyond the RGA construction rule?
```

### Weak Target

Weak target is more useful but still not enough for posterior novelty.

When explicit shortcuts, deterministic status, rank, and categories are removed,
weak target remains high:

```text
continuous_core AUROC/AUPRC = 0.9495 / 0.9620
geometry_continuous_only AUROC/AUPRC = 0.9610 / 0.9715
```

This is less trivial than strict because weak negative includes
`dense_relation_noise`, which can have geometry satisfied. However, the target is
still mostly explained by the same semantic/geometry evidence used to construct
the audit queue and working labels.

### Posterior Claim

The current H002 posterior smoke should not be used to claim:

```text
factorized_reliability_posterior > semantic_plus_geometry
```

The correct claim boundary is:

```text
The feature pipeline is executable, but the current target is not independent
enough to validate posterior novelty.
```

## Decision

H002 should keep RGA as the main benchmark/diagnostic framework, but the
factorized posterior branch needs a redesigned target before it can become a
method contribution.

The next target must avoid using RGA bucket identity itself as the binary label.
It should compare reliability within controlled strata, for example:

- same `geometry_status=satisfied`, distinguish `true_underconfidence` /
  `annotation_sparsity` from `dense_relation_noise`.
- same predicate family, compare informative relation vs dense/trivial relation.
- same rank band, compare geometry-supported reliable edge vs geometry-supported
  but unhelpful/noisy edge.
- human-confirmed labels before any paper-level posterior claim.

## Current Boundary

Established:

- shortcut-controlled smoke script exists.
- shortcut-controlled train-only metrics exist.
- strict target is confirmed as non-independent.
- weak target is useful for debugging but not strong enough for method claim.
- no validation rows were used.

Not established:

- independent relation reliability supervision.
- factorized posterior advantage over `semantic_plus_geometry`.
- human-confirmed target labels.
- held-out validation/test evidence.
- paper-level main table result.

## Next TODO

Next document:

```text
29_target_redesign.md
```

Required next work:

- redesign the target so it is not equivalent to `HL vs LH` or
  `satisfied vs unsatisfied`.
- define controlled strata for within-bucket reliability labels.
- decide which working labels are positive, negative, excluded, or relabel-only.
- specify whether human confirmation is required before further posterior
  fitting.
- keep the redesign train-only until the target and feature contract is frozen.
