# H002 Within-Rank Stability

Last updated: 2026-06-13

## Purpose

`42_rank_proxy_debias.md`의 핵심 blocker는 다음이었다.

```text
negative_rank_only > factorized_reliability_posterior
```

따라서 이번 gate는 rank 자체가 target을 설명하는 shortcut인지 더 좁게 검증한다.
같은 rank band 내부에서도 factorized evidence가 남아야 H002의 posterior claim이
방어 가능하다.

## Tool

Added:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/within_rank_stability.py
```

Command:

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/within_rank_stability.py
```

Result:

```text
status=within_rank_mixed bands=7 metrics=49 pairs=107 validation_used=False
```

## Boundary

- Train-only hypothesis-stage check.
- `(codex_ver)` labels are treated as real labels by user-directed assumption.
- No validation/test rows are used.
- Folds are grouped by `scan_id` inside each rank band.
- Positive/negative pairs are greedily matched by `rank_in_context` inside each rank band.
- `V_mv_e` is not used as model input.
- This is not a paper-level metric.

## Output Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/within_rank_stability_codex_real_assumption/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/within_rank_stability_codex_real_assumption/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/within_rank_stability_codex_real_assumption/metrics.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/within_rank_stability_codex_real_assumption/pairwise.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/within_rank_stability_codex_real_assumption/matched_pairs.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/within_rank_stability_codex_real_assumption/predictions_*.jsonl
```

## Evaluated Bands

| Target | Rank band | Rows | Positive | Negative | Groups | Both-class groups |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `mined_controlled_codex_ver` | `rank_201_500` | 32 | 16 | 16 | 16 | 10 |
| `mined_controlled_codex_ver` | `rank_501_1000` | 32 | 16 | 16 | 17 | 15 |
| `mined_controlled_codex_ver` | `rank_gt1000` | 32 | 16 | 16 | 20 | 12 |
| `combined_controlled_codex_ver` | `rank_201_500` | 32 | 16 | 16 | 16 | 10 |
| `combined_controlled_codex_ver` | `rank_501_1000` | 32 | 16 | 16 | 17 | 15 |
| `combined_controlled_codex_ver` | `rank_gt1000` | 32 | 16 | 16 | 20 | 12 |
| `combined_controlled_codex_ver` | `tail` | 27 | 16 | 11 | 21 | 2 |

`tail`은 `combined`에만 존재하며 mean matched rank gap이 435.82로 크다. 따라서
primary rank-control evidence가 아니라 보조 관찰로만 둔다.

## Main Finding

Primary bands에서 grouped metric 기준으로 factorized posterior는
`negative_rank_only`를 안정적으로 이기지 못했다.

| Target | Rank band | Delta AUPRC | Delta Brier |
| --- | --- | ---: | ---: |
| `mined` | `rank_201_500` | -0.0917 | +0.0727 |
| `mined` | `rank_501_1000` | -0.0545 | +0.0116 |
| `mined` | `rank_gt1000` | +0.0000 | +0.0020 |
| `combined` | `rank_201_500` | -0.0917 | +0.0727 |
| `combined` | `rank_501_1000` | -0.0545 | +0.0116 |
| `combined` | `rank_gt1000` | +0.0000 | +0.0020 |

Delta is:

```text
factorized_reliability_posterior - negative_rank_only
```

Interpretation:

- `rank_201_500`에서는 rank proxy가 더 강하다.
- `rank_501_1000`에서는 AUROC는 약간 좋아지지만 AUPRC/Brier가 나빠진다.
- `rank_gt1000`에서는 사실상 동률이고 Brier는 약간 나빠진다.
- `combined tail`에서는 factorized가 강하지만, rank gap이 커서 strict rank-control
  evidence로 쓰기 어렵다.

## Pairwise Finding

Rank-matched pairwise accuracy는 factorized가 일부 band에서 rank proxy보다 낫다.

| Target | Rank band | Pairs | Mean rank gap | Factorized | Negative rank | Factorized no-rank |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `mined` | `rank_201_500` | 16 | 32.06 | 0.8750 | 0.8438 | 0.5625 |
| `mined` | `rank_501_1000` | 16 | 11.56 | 0.8125 | 0.6875 | 0.6250 |
| `mined` | `rank_gt1000` | 16 | 51.38 | 0.9375 | 0.9375 | 0.6875 |
| `combined` | `tail` | 11 | 435.82 | 0.9091 | 0.5455 | 0.7273 |

This is useful but not enough:

- pairwise accuracy suggests relation-level evidence exists inside rank bands.
- 그러나 grouped CV metric은 아직 rank proxy보다 안정적으로 좋지 않다.
- `factorized_no_rank` alone is weak in most bands, so non-rank factors are not yet
  sufficient as deployable evidence.

## Verdict

Current verdict:

```text
within_rank_mixed
```

Meaning:

```text
H002 has a real signal worth pursuing, but current controlled labels are still
not independent enough from semantic-rank / underconfidence construction.
```

Confirmed:

- Same rank band 내부에서도 positive/negative pair를 만들 수 있다.
- Pairwise level에서는 factorized score가 rank proxy보다 나은 경우가 있다.
- Pure geometry raw score, especially `p_geom_valid`, is not enough to explain
  relation reliability.

Not confirmed:

- grouped primary-band metric에서 factorized posterior가 rank proxy를 안정적으로
  이긴다는 주장.
- non-rank geometry/coverage/uncertainty factors alone이 target을 충분히 설명한다는
  주장.
- current codex target이 rank construction에서 독립적이라는 주장.

## Implication

H002를 버릴 필요는 없다. 다만 다음 단계는 모델을 키우는 것이 아니라 target을
더 엄격하게 만드는 것이다.

현재 문제는:

```text
posterior model capacity problem < target independence problem
```

따라서 다음 target은 positive/negative를 다음 조건으로 묶어야 한다.

- same predicate family
- same or tighter rank band
- close `rank_in_context`
- same geometry status where possible
- similar coverage state
- no direct use of proposed stratum as model feature
- tail rows are secondary unless rank gap is tightly controlled

## Next TODO

Next document:

```text
44_rank_matched_target.md
```

Goal:

- construct stricter rank-matched controlled target.
- use only train rows.
- reduce or mark rows with large rank gap.
- separate primary pairs from exploratory tail pairs.
- rerun posterior smoke on the rank-matched target.
