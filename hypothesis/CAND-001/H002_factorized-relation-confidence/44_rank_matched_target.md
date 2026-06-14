# H002 Rank-Matched Target

Last updated: 2026-06-13

## Purpose

`43_within_rank_stability.md`의 결론은 `within_rank_mixed`였다.

핵심 문제:

```text
same rank band 안에서는 pairwise signal이 일부 남지만,
grouped metric에서는 negative_rank_only가 여전히 강하다.
```

따라서 이번 gate는 rank band보다 더 좁은 target을 만든다. Positive/negative를
`rank_in_context` 기준으로 직접 matching하고, large rank gap pair는 primary smoke에서
제외한다.

## Tool

Added:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/rank_matched_target.py
```

Command:

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/rank_matched_target.py
```

Result:

```text
status=rank_matched_mixed evaluated_targets=2 metrics=20 primary_pairs=86 tail_pairs=11 validation_used=False
```

`primary_pairs=86`은 `mined`와 `combined` source target을 합친 수다. 각 evaluated
primary target은 43쌍, 86 rows다.

## Boundary

- Train-only hypothesis-stage check.
- `(codex_ver)` labels are treated as real labels by user-directed assumption.
- No validation/test rows are used.
- Primary target: non-tail rank band and `rank_gap_abs <= 50`.
- Tail target: `rank_gap_abs <= 500`이면 exploratory rows로만 저장한다.
- Tail rows are not used in smoke metrics.
- Folds are grouped by `scan_id`.
- `V_mv_e` is not used as model input.
- This is not a paper-level metric.

## Output Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/rank_matched_target_codex_real_assumption/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/rank_matched_target_codex_real_assumption/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/rank_matched_target_codex_real_assumption/metrics.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/rank_matched_target_codex_real_assumption/pairwise.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/rank_matched_target_codex_real_assumption/pair_records.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/rank_matched_target_codex_real_assumption/*_rows.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/rank_matched_target_codex_real_assumption/predictions_*.jsonl
```

## Target Construction

| Target | Scope | Rows | Positive | Negative | Pairs | Mean rank gap | Max rank gap | Evaluated |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `mined_rank_matched_gap50_codex_ver` | primary | 86 | 43 | 43 | 43 | 14.56 | 47.00 | yes |
| `combined_rank_matched_gap50_codex_ver` | primary | 86 | 43 | 43 | 43 | 14.56 | 47.00 | yes |
| `combined_tail_exploratory_gap500_codex_ver` | tail exploratory | 22 | 11 | 11 | 11 | 103.91 | 367.00 | no |

Important:

- `mined`와 `combined`의 primary gap-50 target은 같은 row set이다.
- `combined`의 extra tail rows는 primary metric에서 제외했다.
- 현재 controlled target은 전부 `proximity / close by / satisfied /
  covered_checkable`이므로, 이번 gate에서 실제로 더 강하게 통제한 축은
  `rank_in_context`다.

## Grouped Smoke Metrics

Primary target metrics are identical for `mined` and `combined`.

| View | AUROC | AUPRC | Brier | ECE-5 |
| --- | ---: | ---: | ---: | ---: |
| `semantic_only` | 0.9319 | 0.9364 | 0.1162 | 0.0906 |
| `geometry_only` | 0.6577 | 0.6418 | 0.2561 | 0.0616 |
| `semantic_plus_geometry` | 0.8978 | 0.9027 | 0.1313 | 0.0950 |
| `factorized_reliability_posterior` | 0.9313 | 0.9272 | 0.1169 | 0.0967 |
| `negative_rank_only` | 0.9435 | 0.9511 | 0.1139 | 0.0531 |
| `factorized_no_rank` | 0.6604 | 0.6198 | 0.2506 | 0.0727 |
| `negative_rank_plus_factorized_no_rank` | 0.9005 | 0.9020 | 0.1363 | 0.0992 |
| `negative_rank_plus_disagreement` | 0.9416 | 0.9461 | 0.1138 | 0.0716 |

## Key Comparisons

Delta is left minus right.

| Left | Right | Delta AUROC | Delta AUPRC | Delta Brier |
| --- | --- | ---: | ---: | ---: |
| `factorized_reliability_posterior` | `semantic_plus_geometry` | +0.0335 | +0.0245 | -0.0144 |
| `factorized_reliability_posterior` | `negative_rank_only` | -0.0122 | -0.0239 | +0.0029 |
| `negative_rank_plus_factorized_no_rank` | `negative_rank_only` | -0.0430 | -0.0490 | +0.0223 |
| `negative_rank_plus_disagreement` | `negative_rank_only` | -0.0019 | -0.0049 | -0.0002 |
| `factorized_no_rank` | `geometry_continuous_only` | +0.0027 | -0.0220 | -0.0056 |

Interpretation:

- Rank-matching improves target cleanliness, but does not make factorized
  posterior beat `negative_rank_only`.
- Factorized posterior does improve over `semantic_plus_geometry`, but this is
  not enough because semantic rank proxy is the stronger control.
- Adding non-rank factorized evidence to `negative_rank_only` hurts grouped
  performance.
- `negative_rank_plus_disagreement` is almost tied with rank proxy, so current
  disagreement features mostly behave as rank-derived evidence.

## Pairwise Accuracy

| Target | Pairs | Mean gap | Factorized | Negative rank | Factorized no-rank | P-geom raw |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `mined_rank_matched_gap50_codex_ver` | 43 | 14.56 | 0.8605 | 0.8372 | 0.6512 | 0.5349 |
| `combined_rank_matched_gap50_codex_ver` | 43 | 14.56 | 0.8605 | 0.8372 | 0.6512 | 0.5349 |

Pairwise view is slightly more favorable to H002:

```text
factorized pairwise accuracy > negative_rank_only
```

But grouped metric remains the stricter criterion for method support.

## Verdict

Current verdict:

```text
rank_matched_mixed
```

What is established:

- A stricter rank-matched target is feasible.
- Primary target has balanced labels: 43 positive / 43 negative.
- Mean rank gap is small: 14.56.
- `p_geom_valid` alone is still weak, supporting the distinction between
  geometry validity and relation reliability.
- Factorized posterior has a small pairwise advantage over rank proxy.

What is not established:

- Factorized posterior beats `negative_rank_only` under scan-grouped CV.
- Non-rank factorized evidence adds stable deployable signal beyond rank.
- Current `(codex_ver)` target is sufficiently independent from semantic-rank
  construction.

## Implication

H002 should not yet claim:

```text
factorized reliability posterior outperforms strong rank-controlled baselines.
```

The safer claim remains:

```text
RGA exposes relation reliability as distinct from geometry validity, but the
current codex-controlled target is still rank/underconfidence-confounded.
```

This is not a failure of the RGA framework. It is a warning that the current
label source is not independent enough to support a posterior method claim.

## Next TODO

Next document:

```text
45_target_independence_audit.md
```

Goal:

- diagnose exactly why rank proxy remains strong after rank matching.
- separate target construction effects from deployable evidence effects.
- define the minimum new label/audit evidence needed before training a larger
  posterior.
- decide whether H002 should continue as a posterior method claim or narrow to
  an RGA benchmark/failure-analysis claim.
