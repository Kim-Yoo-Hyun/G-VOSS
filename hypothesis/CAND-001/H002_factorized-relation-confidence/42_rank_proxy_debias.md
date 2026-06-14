# H002 Rank Proxy Debias

Last updated: 2026-06-13

## Purpose

`41_grouped_control_smoke.md`에서 발견한 가장 큰 blocker를 검증한다.

Blocker:

```text
negative_rank_only > factorized_reliability_posterior
```

사용자 지시에 따라 `(codex_ver)` labels는 hypothesis-stage real label로 취급한다.
그러나 이 가정 아래에서도 factorized posterior가 단순 rank-derived proxy보다 약하면,
method contribution으로 주장하기 어렵다.

## Tool

Added:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/rank_proxy_debias.py
```

Command:

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/rank_proxy_debias.py
```

Result:

```text
status=rank_proxy_not_debiased metrics=22 validation_used=False mined_controlled_codex_ver:rankplus_d_auprc=-0.0491:rankplus_d_brier=0.0286 combined_controlled_codex_ver:rankplus_d_auprc=-0.0141:rankplus_d_brier=0.0164
```

## Output Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/rank_proxy_debias_codex_real_assumption/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/rank_proxy_debias_codex_real_assumption/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/rank_proxy_debias_codex_real_assumption/metrics.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/rank_proxy_debias_codex_real_assumption/predictions_*.jsonl
```

## Debias Views

Primary proxy:

```text
negative_rank_only = 1 - semantic_score_norm
```

Rank-derived fields removed in no-rank views:

```text
rank_in_context
predicate_rank_for_pair
semantic_score_norm
top100_semantic
top50_semantic
top100_and_unsatisfied
tail_gt100_and_satisfied
```

Rank-derived uncertainty/disagreement fields removed in `factorized_no_rank`:

```text
absolute_disagreement
semantic_geometry_disagreement_score
semantic_score_norm_minus_p_geom_valid
underconfidence_score
```

Key views:

| View | Meaning |
| --- | --- |
| `factorized_no_rank` | factorized view after removing rank and rank-derived disagreement |
| `semantic_plus_geometry_no_rank` | `S+G` after removing rank-derived semantic fields |
| `negative_rank_plus_factorized_no_rank` | rank proxy plus non-rank factorized evidence |
| `negative_rank_plus_disagreement` | rank proxy plus rank-derived disagreement features |
| `disagreement_only` | disagreement features without rank proxy |

## Main Metrics

Scan-grouped train-internal CV:

| Target | View | AUROC | AUPRC | Brier | ECE-5 |
| --- | --- | ---: | ---: | ---: | ---: |
| `mined_controlled_codex_ver` | `factorized_reliability_posterior` | 0.9427 | 0.9409 | 0.1098 | 0.0980 |
| `mined_controlled_codex_ver` | `negative_rank_only` | 0.9505 | 0.9589 | 0.1057 | 0.0732 |
| `mined_controlled_codex_ver` | `factorized_no_rank` | 0.5868 | 0.5617 | 0.2696 | 0.0849 |
| `mined_controlled_codex_ver` | `negative_rank_plus_factorized_no_rank` | 0.9028 | 0.9098 | 0.1343 | 0.0667 |
| `mined_controlled_codex_ver` | `negative_rank_plus_disagreement` | 0.9536 | 0.9580 | 0.1047 | 0.0680 |
| `combined_controlled_codex_ver` | `factorized_reliability_posterior` | 0.7397 | 0.6801 | 0.2086 | 0.0878 |
| `combined_controlled_codex_ver` | `negative_rank_only` | 0.7884 | 0.7094 | 0.1899 | 0.2166 |
| `combined_controlled_codex_ver` | `factorized_no_rank` | 0.4415 | 0.4868 | 0.2814 | 0.0970 |
| `combined_controlled_codex_ver` | `negative_rank_plus_factorized_no_rank` | 0.7574 | 0.6953 | 0.2063 | 0.1569 |
| `combined_controlled_codex_ver` | `negative_rank_plus_disagreement` | 0.7865 | 0.7220 | 0.1925 | 0.1056 |

## Key Comparisons

### 1. Full Factorized vs Rank Proxy

| Target | Delta AUROC | Delta AUPRC | Delta Brier | Pass |
| --- | ---: | ---: | ---: | --- |
| `mined_controlled_codex_ver` | -0.0078 | -0.0179 | +0.0041 | no |
| `combined_controlled_codex_ver` | -0.0487 | -0.0293 | +0.0187 | no |

The full factorized posterior does not beat `negative_rank_only`.

### 2. Non-Rank Factorized Evidence Added To Rank Proxy

Delta is `negative_rank_plus_factorized_no_rank - negative_rank_only`.

| Target | Delta AUROC | Delta AUPRC | Delta Brier | Pass |
| --- | ---: | ---: | ---: | --- |
| `mined_controlled_codex_ver` | -0.0477 | -0.0491 | +0.0286 | no |
| `combined_controlled_codex_ver` | -0.0310 | -0.0141 | +0.0164 | no |

Adding non-rank factorized evidence to the rank proxy hurts performance.

### 3. Disagreement Added To Rank Proxy

Delta is `negative_rank_plus_disagreement - negative_rank_only`.

| Target | Delta AUROC | Delta AUPRC | Delta Brier | Pass |
| --- | ---: | ---: | ---: | --- |
| `mined_controlled_codex_ver` | +0.0030 | -0.0009 | -0.0010 | no |
| `combined_controlled_codex_ver` | -0.0019 | +0.0126 | +0.0026 | no |

Disagreement features are not enough to clearly improve over rank proxy.

## Decision

Current verdict:

```text
rank_proxy_not_debiased
```

Even with `(codex_ver)` treated as real labels, H002 does not yet support a
factorized-posterior method claim.

Established:

- relation reliability labels differ inside fixed `proximity / close by` and
  `geometry_status=satisfied`.
- geometry-only is weak.
- rank/underconfidence proxy is very strong.
- factorized posterior can improve over `semantic_plus_geometry` in some grouped
  settings.

Not established:

- factorized posterior beats a simple rank-derived proxy.
- non-rank geometry/coverage/uncertainty evidence adds signal beyond rank.
- current label target is independent of rank construction.

## Implication

H002 should not currently be framed as:

```text
factorized posterior reliably improves relation reliability prediction.
```

The safer current framing is:

```text
RGA exposes that relation reliability is not geometry validity, but the current
controlled target is still rank-confounded.
```

This is useful. It tells us the next issue is target construction, not model
capacity.

## Next TODO

Next document:

```text
43_within_rank_stability.md
```

Recommended next implementation:

- evaluate each rank band separately.
- build same-rank matched positive/negative pairs if possible.
- check whether any factorized signal remains inside fixed rank bands.
- if not, redesign the controlled target so positives and negatives are not
  separable by semantic rank.
