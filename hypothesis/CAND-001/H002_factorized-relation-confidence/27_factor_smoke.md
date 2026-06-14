# H002 Factor Smoke

Last updated: 2026-06-12

## Purpose

`26_factor_dataset.md`에서 만든 train-only smoke inputs로 H002의 first
factorized reliability posterior 비교를 실행했다.

이 단계의 목적은 paper-level 성능을 주장하는 것이 아니다. 목적은 다음을 확인하는
것이다.

1. `semantic_only`, `geometry_only`, `semantic_plus_geometry`,
   `factorized_reliability_posterior` baseline을 같은 input contract에서 실행할 수 있는가.
2. strict/weak working target이 실제로 posterior smoke에 충분히 독립적인 target인가.
3. factorized representation이 단순 shortcut을 학습하는 위험이 있는가.

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

Boundary:

```text
split = train_only
validation usage = false
paper result = false
human confirmed labels = false
```

## Tool

Added:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/factor_smoke.py
```

Command:

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/factor_smoke.py
```

Status:

```text
ready_with_shortcut_caveat
```

Implementation note:

- `sklearn` / `numpy` are not installed in the host environment.
- The tool uses a small pure-Python logistic regression.
- Hyperparameters were fixed before reading results:
  - folds: `5`
  - epochs: `1500`
  - learning rate: `0.08`
  - L2: `0.03`
- No validation rows were used for hyperparameter tuning.

## Output Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/factor_smoke/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/factor_smoke/metrics.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/factor_smoke/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/factor_smoke/predictions_*.jsonl
```

The output directory contains per-baseline prediction files for:

- strict / in-sample
- strict / train-internal 5-fold
- weak / in-sample
- weak / train-internal 5-fold

## Main Metrics

The main table below reports train-internal 5-fold smoke results. This is still
train-only and must not be read as held-out validation evidence.

| Target | Baseline | AUROC | AUPRC | Brier | ECE-5 | Accuracy@0.5 |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| strict | `semantic_only` | 1.0000 | 1.0000 | 0.0092 | 0.0468 | 0.9785 |
| strict | `geometry_only` | 1.0000 | 1.0000 | 0.0005 | 0.0206 | 1.0000 |
| strict | `semantic_plus_geometry` | 1.0000 | 1.0000 | 0.0003 | 0.0143 | 1.0000 |
| strict | `factorized_reliability_posterior` | 1.0000 | 1.0000 | 0.0003 | 0.0120 | 1.0000 |
| weak | `semantic_only` | 0.9563 | 0.9681 | 0.0663 | 0.0479 | 0.9167 |
| weak | `geometry_only` | 0.9603 | 0.9701 | 0.0690 | 0.0301 | 0.9167 |
| weak | `semantic_plus_geometry` | 0.9739 | 0.9813 | 0.0590 | 0.0286 | 0.9167 |
| weak | `factorized_reliability_posterior` | 0.9746 | 0.9818 | 0.0585 | 0.0288 | 0.9167 |

Initial reading:

- Strict target is too easy. Every main baseline reaches AUROC/AUPRC `1.0`.
- Weak target is slightly more informative because it includes `dense_relation_noise`
  as satisfied-geometry negative rows.
- `factorized_reliability_posterior` is marginally highest on weak target, but the
  delta over `semantic_plus_geometry` is too small and too target-dependent to
  claim method advantage.

## Probe Metrics

Probe metrics show why the strict result should not be over-interpreted.

| Target | Probe | AUROC | AUPRC | Interpretation |
| --- | --- | ---: | ---: | --- |
| strict | `semantic_score_norm` | 0.0023 | 0.3248 | positive target is mostly low-semantic LH |
| strict | `negative_semantic_score_norm` | 0.9977 | 0.9980 | inverted semantic rank almost solves strict target |
| strict | `p_geom_valid` | 0.6829 | 0.6244 | continuous geometry-only score alone is not enough |
| strict | `geometry_satisfied_rule` | 1.0000 | 1.0000 | deterministic status solves strict target |
| strict | `rga_shortcut_rule` | 1.0000 | 1.0000 | RGA bucket shortcut solves strict target |
| weak | `negative_semantic_score_norm` | 0.8183 | 0.7551 | weak target still keeps semantic-rank shortcut |
| weak | `geometry_satisfied_rule` | 0.9018 | 0.9163 | dense relation noise makes weak target less trivial |

## Shortcut Audit

Strict target shortcut:

| Target | RGA shortcut state | Rows |
| --- | --- | ---: |
| negative | `top100_and_unsatisfied=1`, `tail_gt100_and_satisfied=0`, `geometry_status=unsatisfied` | 45 |
| positive | `top100_and_unsatisfied=0`, `tail_gt100_and_satisfied=1`, `geometry_status=satisfied` | 48 |

This means strict target is basically:

```text
semantic_overconfidence HL -> negative
true_underconfidence LH -> positive
```

Therefore a model can achieve perfect strict performance by learning the RGA
bucket construction itself.

Weak target shortcut:

| Target | RGA shortcut state | Rows |
| --- | --- | ---: |
| negative | `top100_and_unsatisfied=1`, `geometry_status=unsatisfied` | 45 |
| negative | `tail_gt100_and_satisfied=1`, `geometry_status=satisfied` | 11 |
| positive | `tail_gt100_and_satisfied=1`, `geometry_status=satisfied` | 76 |

The 11 negative satisfied-geometry rows are `dense_relation_noise`. They make the
weak target more useful than strict, but it is still machine-assisted and still
derived from the same RGA/audit pipeline.

## Interpretation

This stage is useful, but not because it proves factorized posterior novelty.

What it proves:

- The H002 factorized feature pipeline runs end-to-end.
- All four planned baseline views can be trained and scored under a train-only
  contract.
- Weak target gives a nontrivial but still small and noisy first diagnostic.
- The current strict target is not independent enough for a method claim.

What it does not prove:

- It does not prove `factorized_reliability_posterior` is better than
  `semantic_plus_geometry`.
- It does not prove relation reliability generalization.
- It does not provide validation/test evidence.
- It does not replace human-confirmed audit labels.

The main technical lesson is:

```text
H002 needs a shortcut-controlled target/evaluation design before posterior
performance can be interpreted.
```

## Current Boundary

Established:

- train-only smoke fitting is executable.
- no validation rows were used.
- baseline comparison artifacts exist.
- strict target shortcut is confirmed.
- weak target is more informative but still not paper-lockable.

Not established:

- independent relation reliability target.
- shortcut-controlled factorized posterior advantage.
- human-confirmed label quality.
- held-out validation/test performance.
- paper-level main table result.

## Next TODO

Next document:

```text
28_shortcut_control.md
```

Required next work:

- define which features are target-construction shortcuts.
- rerun smoke with shortcut-controlled feature views.
- separate `RGA bucket classification` from `relation reliability prediction`.
- decide whether the next target must be human-confirmed before any posterior
  claim is meaningful.
- keep all checks train-only until the target/feature definition is frozen.
